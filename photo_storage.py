"""Private Supabase Storage using Firebase ID tokens; no service-role keys.

Only processed JPEGs are sent here. Tokens are request-local, never stored in
Firestore, browser cookies, report metadata, or a shared mutable SDK session.
"""
import re
from pathlib import Path
from urllib.parse import quote, urlsplit

import requests


class PhotoStorageError(ValueError):
    pass


class SupabasePhotoStorage:
    provider = 'supabase'

    def __init__(self, url, publishable_key, bucket='laporan-foto'):
        self.url = (url or '').strip().rstrip('/')
        self.key = (publishable_key or '').strip()
        self.bucket = (bucket or '').strip()
        parsed = urlsplit(self.url)
        if (parsed.scheme != 'https' or not parsed.hostname
                or not parsed.hostname.endswith('.supabase.co')
                or parsed.username or parsed.password or parsed.port
                or parsed.path or parsed.query or parsed.fragment):
            raise PhotoStorageError('SUPABASE_URL harus berupa URL HTTPS proyek Supabase.')
        if not self.key.startswith('sb_publishable_'):
            raise PhotoStorageError('Isi SUPABASE_PUBLISHABLE_KEY dengan publishable key, bukan secret key.')
        if not re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,99}', self.bucket):
            raise PhotoStorageError('Nama bucket Supabase tidak valid.')

    def scoped(self, token, uid, report_id):
        if (not isinstance(uid, str) or not 1 <= len(uid) <= 128
                or '/' in uid or '\\' in uid or uid in ('.', '..')
                or any(ord(c) < 32 for c in uid)
                or not re.fullmatch(r'[a-f0-9]{32}', report_id)):
            raise PhotoStorageError('Identitas penyimpanan foto tidak valid.')
        return _ScopedPhotos(self, token, uid, report_id)


class _ScopedPhotos:
    def __init__(self, storage, token, owner_uid, report_id):
        self.storage = storage
        self._token = token
        self.owner_uid = owner_uid
        self.report_id = report_id

    def path(self, filename):
        if not re.fullmatch(r'(foto|deteksi)_(foto[123]|kiri|kanan|atas)\.jpg', filename):
            raise PhotoStorageError('Nama file foto tidak valid.')
        return f'{self.owner_uid}/{self.report_id}/{filename}'

    def _headers(self):
        return {'apikey': self.storage.key, 'Authorization': f'Bearer {self._token}'}

    def _url(self, path='', authenticated=False):
        base = self.storage.url + '/storage/v1/object/'
        if authenticated:
            base += 'authenticated/'
        return base + quote(self.storage.bucket, safe='') + ('/' + quote(path, safe='/') if path else '')

    @staticmethod
    def _check(response):
        if 200 <= response.status_code < 300:
            return
        # Do not echo provider response bodies, API keys, or tokens to the UI.
        if response.status_code in (401, 403):
            raise PhotoStorageError('Akses foto Supabase ditolak. Periksa integrasi Firebase dan policy Storage.')
        if response.status_code == 413:
            raise PhotoStorageError('Foto hasil pemrosesan melebihi batas bucket 10 MB.')
        raise PhotoStorageError('Penyimpanan foto Supabase belum berhasil. Periksa bucket, policy, dan koneksi.')

    def upload_file(self, filename, local_path):
        path = self.path(filename)
        local_path = Path(local_path)
        if local_path.stat().st_size > 10 * 1024 * 1024:
            raise PhotoStorageError('Foto hasil pemrosesan melebihi batas bucket 10 MB.')
        try:
            with local_path.open('rb') as photo:
                response = requests.post(self._url(path), data=photo,
                    headers={**self._headers(), 'Content-Type': 'image/jpeg', 'x-upsert': 'false'},
                    timeout=(10, 60), allow_redirects=False)
            self._check(response)
        except requests.RequestException:
            raise PhotoStorageError('Koneksi upload foto Supabase terputus. Coba lagi.') from None
        return path

    def download(self, filename):
        try:
            response = requests.get(self._url(self.path(filename), authenticated=True),
                headers=self._headers(), timeout=(10, 60), allow_redirects=False)
            self._check(response)
            return response.content
        except requests.RequestException:
            raise PhotoStorageError('Koneksi pembacaan foto Supabase terputus. Coba lagi.') from None

    def remove_failed_uploads(self, filenames):
        # Called only by the failed-upload rollback, never by a public endpoint.
        paths = [self.path(name) for name in filenames]
        if not paths:
            return
        try:
            response = requests.delete(self._url(), json={'prefixes': paths},
                headers=self._headers(), timeout=(10, 30), allow_redirects=False)
            self._check(response)
        except requests.RequestException:
            raise PhotoStorageError('Pembersihan foto gagal unggah perlu diperiksa kembali.') from None
