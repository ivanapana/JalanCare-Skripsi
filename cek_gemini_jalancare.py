"""Diagnostik narasi memakai data contoh; tidak mengubah laporan atau konfigurasi."""
import importlib.metadata
import json
import os
import re
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / '.env')
KEY = os.getenv('GEMINI_API_KEY', '')
MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')


def safe(value):
    text = str(value)
    if KEY:
        text = text.replace(KEY, '[KUNCI_DISAMARKAN]')
    text = re.sub(r'AIza[\w-]+', '[KUNCI_DISAMARKAN]', text)
    return text[:2500]


def say(label, value):
    print(label, safe(value), flush=True)


def main():
    print('PEMERIKSAAN GEMINI JALANCARE — DATA CONTOH', flush=True)
    if not KEY:
        print('GEMINI_API_KEY kosong. Hentikan dan periksa .env.');return
    import narrative
    from google import genai
    say('File narasi yang dibaca:', narrative.__file__)
    say('Model:', MODEL)
    say('Versi google-genai:', importlib.metadata.version('google-genai'))
    original_client = genai.Client
    clients = []
    calls = []

    def inspect_call(method, fn, **kwargs):
        calls.append(method)
        say('Metode:', method)
        try:
            response = fn(**kwargs)
        except Exception as error:
            say('JENIS ERROR API:', type(error).__name__)
            say('RINCIAN ERROR API:', error)
            raise
        say('Status respons:', getattr(response, 'status', 'tidak ada field status'))
        try:
            raw = response.output_text if method == 'interactions.create' else response.text
            say('Jumlah karakter respons:', len(raw) if isinstance(raw, str) else 0)
            obj = json.loads(raw)
            structure = (isinstance(obj, dict) and set(obj) == {'deskripsi', 'tindakLanjut'}
                         and all(isinstance(v, str) and v.strip() and len(v) <= 1000 for v in obj.values()))
            say('Struktur narasi valid:', bool(structure))
            if structure:
                narrative.validate_prose(obj)
                say('Validasi isi narasi:', 'LOLOS')
            # Only synthetic input is used; never a resident's real report/photo.
            say('Respons untuk data contoh:', raw)
        except Exception as error:
            say('JENIS ERROR VALIDASI:', type(error).__name__)
            say('RINCIAN ERROR VALIDASI:', error)
            if isinstance(locals().get('raw'), str):
                say('Respons untuk data contoh:', raw)
        return response

    def checked_client(**kwargs):
        try:
            client = original_client(**kwargs)
            clients.append(client)
            return SimpleNamespace(
                interactions=SimpleNamespace(create=lambda **kw: inspect_call(
                    'interactions.create', client.interactions.create, **kw)),
                models=SimpleNamespace(generate_content=lambda **kw: inspect_call(
                    'models.generate_content', client.models.generate_content, **kw)))
        except Exception as error:
            say('JENIS ERROR SDK:', type(error).__name__)
            say('RINCIAN ERROR SDK:', error)
            raise

    genai.Client = checked_client
    report = dict(idLaporan='diagnostik-contoh', namaJalan='Jalan Contoh',
                  kabupaten='Minahasa', latitude=1.3, longitude=124.9,
                  timestamp='2026-10-25T00:00:00+00:00', keterangan='',
                  foto=[dict(angle=f'foto{i}', boxes=[dict(confidence=.8,
                        xyxy=[100, 100, 200, 200])]) for i in (1, 2, 3)])
    try:
        _, source, warning = narrative.generate(report, KEY, MODEL)
        say('HASIL AKHIR SUMBER NARASI:', source)
        say('Peringatan:', warning or 'Tidak ada')
        if not calls:
            say('Petunjuk:', 'Permintaan API belum dipanggil. Periksa error SDK di atas.')
        if source == 'gemini':
            print('Tes narasi lengkap berhasil. Jika website masih gagal, restart server dan periksa data laporan nyata.', flush=True)
    finally:
        genai.Client = original_client
        for client in clients:
            try:client.close()
            except Exception:pass


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        say('PEMERIKSAAN BERHENTI:', type(error).__name__)
        say('RINCIAN:', error)
