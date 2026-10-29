"""Storage/auth boundaries and rollback tests; no real cloud credentials needed."""
import io
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from photo_storage import SupabasePhotoStorage, PhotoStorageError
from services import FirebaseService
from store import FirebaseStore

RID = 'a' * 32


def storage():
    return SupabasePhotoStorage('https://example.supabase.co', 'sb_publishable_test')


def backend(role='warga', owner='owner', exists=True):
    result = FirebaseStore.__new__(FirebaseStore)
    result.app = object()
    result.api_key = 'not-a-real-key'
    result.photo_storage = storage()
    result.user = Mock(return_value={'uid': 'actor', 'role': role, 'disabled': False})
    result.report = Mock(return_value={'idPengguna': owner} if exists else None)
    result.auth = Mock()
    result.auth.get_user.return_value = SimpleNamespace(disabled=False)
    result.auth.create_custom_token.return_value = b'custom-token'
    def verify(*args, **kwargs):
        return {'uid': 'actor', **result.auth.create_custom_token.call_args.kwargs['developer_claims']}
    result.auth.verify_id_token.side_effect = verify
    return result


def test_other_resident_cannot_mint_photo_token():
    db = backend()
    with pytest.raises(PhotoStorageError):
        db.photo_access('actor', RID)
    db.auth.create_custom_token.assert_not_called()


@pytest.mark.parametrize('profile_disabled,auth_disabled', [(True, False), (False, True)])
def test_disabled_user_cannot_mint_photo_token(profile_disabled, auth_disabled):
    db = backend(owner='actor')
    db.user.return_value['disabled'] = profile_disabled
    db.auth.get_user.return_value.disabled = auth_disabled
    with pytest.raises(PhotoStorageError):
        db.photo_access('actor', RID)
    db.auth.create_custom_token.assert_not_called()


def test_staff_token_uses_staff_uid_but_owner_path():
    db = backend(role='petugas')
    response = Mock(ok=True)
    response.json.return_value = {'idToken': 'firebase-id-token', 'refreshToken': 'discard-me'}
    with patch('requests.post', return_value=response) as post:
        photos = db.photo_access('actor', RID)
    assert photos.path('foto_foto1.jpg') == f'owner/{RID}/foto_foto1.jpg'
    claim_call = db.auth.create_custom_token.call_args
    assert claim_call.args == ('actor',)
    assert claim_call.kwargs['developer_claims'] == {
        'role': 'authenticated', 'jalancare_report': RID,
        'jalancare_action': 'read', 'jalancare_staff': True}
    assert 'signInWithCustomToken' in post.call_args.args[0]
    db.auth.set_custom_user_claims.assert_not_called()


def test_upload_requires_resident_and_new_report():
    for db in (backend(role='petugas', exists=False), backend(owner='actor')):
        with pytest.raises(PhotoStorageError):
            db.photo_access('actor', RID, write=True)
        db.auth.create_custom_token.assert_not_called()


def test_upload_id_token_claims_are_verified():
    db = backend(exists=False)
    response = Mock(ok=True)
    response.json.return_value = {'idToken': 'id-token'}
    db.auth.verify_id_token.side_effect = None
    db.auth.verify_id_token.return_value = {'uid': 'someone-else'}
    with patch('requests.post', return_value=response), pytest.raises(PhotoStorageError):
        db.photo_access('actor', RID, write=True)


def test_scoped_clients_do_not_share_tokens_and_use_private_download():
    a = storage().scoped('token-a', 'owner', RID)
    b = storage().scoped('token-b', 'owner-b', 'b' * 32)
    response = Mock(ok=True, status_code=200, content=b'jpeg')
    with patch('photo_storage.requests.get', return_value=response) as get:
        assert a.download('foto_foto1.jpg') == b'jpeg'
        assert get.call_args.kwargs['headers']['Authorization'] == 'Bearer token-a'
        assert '/object/authenticated/laporan-foto/owner/' in get.call_args.args[0]
        b.download('foto_foto2.jpg')
        assert get.call_args.kwargs['headers']['Authorization'] == 'Bearer token-b'
    assert a._headers()['Authorization'] == 'Bearer token-a'


def test_no_secret_keys_or_traversal():
    with pytest.raises(PhotoStorageError):
        SupabasePhotoStorage('https://example.supabase.co', 'sb_secret_forbidden')
    with pytest.raises(PhotoStorageError):
        storage().scoped('token', '../owner', RID)
    with pytest.raises(PhotoStorageError):
        storage().scoped('token', 'owner', RID).path('../../foto.jpg')


def report_fixture(tmp_path):
    folder = tmp_path / 'draft'
    folder.mkdir()
    for angle in ('foto1', 'foto2', 'foto3'):
        for kind in ('foto', 'deteksi'):
            (folder / f'{kind}_{angle}.jpg').write_bytes(b'processed-jpeg')
    db = Mock(bucket=None, photo_storage=storage())
    photos = storage().scoped('token', 'owner', RID)
    photos.upload_file = Mock(side_effect=lambda filename, file: photos.path(filename))
    photos.remove_failed_uploads = Mock()
    db.photo_access.return_value = photos
    db.report.return_value = None
    service = FirebaseService(db, tmp_path, strict_cloud=True)
    report = dict(idLaporan=RID, idPengguna='owner', timestamp='2026-10-24T00:00:00+00:00',
                  narrativeSource='gemini', foto=[], status='Menunggu Verifikasi')
    return service, db, photos, report, folder


def test_cloud_save_keeps_firestore_metadata_and_six_processed_images(tmp_path):
    service, db, photos, report, folder = report_fixture(tmp_path)
    result = service.simpanDataLaporan(report, folder)
    assert result['storage'] == 'supabase'
    assert result['idPengguna'] == 'owner'
    assert result['citraUrls'] == [f'supabase://laporan-foto/owner/{RID}/foto_foto{i}.jpg' for i in (1, 2, 3)]
    assert result['citraKiri'] == result['citraUrls'][0]
    assert photos.upload_file.call_count == 6
    db.save_report.assert_called_once_with(result)
    photos.remove_failed_uploads.assert_not_called()
    assert not (tmp_path / 'reports' / RID).exists()


def test_partial_upload_is_cleaned_without_saving_report(tmp_path):
    service, db, photos, report, folder = report_fixture(tmp_path)
    photos.upload_file.side_effect = ['first-file', PhotoStorageError('upload failed')]
    with pytest.raises(PhotoStorageError):
        service.simpanDataLaporan(report, folder)
    db.save_report.assert_not_called()
    photos.remove_failed_uploads.assert_called_once_with(['foto_foto1.jpg', 'deteksi_foto1.jpg'])


@pytest.mark.parametrize('commit_state', ['absent', 'exists', 'unknown'])
def test_firestore_commit_ambiguity_does_not_delete_committed_photos(tmp_path, commit_state):
    service, db, photos, report, folder = report_fixture(tmp_path)
    db.save_report.side_effect = TimeoutError('commit response lost')
    if commit_state == 'exists':
        db.report.return_value = report
    elif commit_state == 'unknown':
        db.report.side_effect = TimeoutError('cannot confirm')
    with pytest.raises(TimeoutError):
        service.simpanDataLaporan(report, folder)
    assert photos.remove_failed_uploads.call_count == (1 if commit_state == 'absent' else 0)


def test_supabase_media_checks_permissions_before_downloading(tmp_path):
    # Exercise the actual Flask media route with the existing demo login helper.
    from app import create_app
    from store import LocalStore
    from PIL import Image
    db = LocalStore(tmp_path / 'local.sqlite')
    app = create_app(dict(TESTING=True, PRIVATE=tmp_path, STORE=db, MODE='demo',
        DETECTOR=Mock(), PRIVACY_DETECTOR=Mock()))
    owner = next(u for u in db.users() if u['role'] == 'warga')
    other = db.create_user('other@example.test', 'password123', 'Other')
    db.save_report(dict(idLaporan=RID, idPengguna=owner['uid'], storage='supabase',
        timestamp='2026-10-24T00:00:00+00:00', latitude=1.4, longitude=124.9,
        status='Menunggu Verifikasi', foto=[dict(angle='foto1', boxes=[])]))
    jpeg = io.BytesIO()
    Image.new('RGB', (640, 640)).save(jpeg, format='JPEG')
    access = Mock()
    access.download.return_value = jpeg.getvalue()
    db.photo_access = Mock(return_value=access)
    client = app.test_client()
    def login_as(uid):
        with client.session_transaction() as session:
            session.update(uid=uid, auth_version='2.5.1')
    login_as(other['uid'])
    assert client.get(f'/media/{RID}/foto/foto1').status_code == 403
    db.photo_access.assert_not_called()
    for user in (owner, next(u for u in db.users() if u['role'] == 'petugas')):
        login_as(user['uid'])
        assert client.get(f'/media/{RID}/foto/foto1').status_code == 200
        assert client.get(f'/media/{RID}/deteksi/foto1').status_code == 200
        db.photo_access.assert_called_with(user['uid'], RID)


def test_upload_headers_no_upsert_and_no_raw_provider_errors(tmp_path):
    photos = storage().scoped('token', 'owner', RID)
    file = tmp_path / 'processed.jpg'
    file.write_bytes(b'jpeg')
    with patch('photo_storage.requests.post', return_value=Mock(ok=True, status_code=200)) as post:
        photos.upload_file('foto_foto1.jpg', file)
    assert post.call_args.kwargs['headers']['x-upsert'] == 'false'
    assert post.call_args.kwargs['headers']['Content-Type'] == 'image/jpeg'
    with patch('photo_storage.requests.get', return_value=Mock(ok=False, status_code=403, text='secret')):
        with pytest.raises(PhotoStorageError) as error:
            photos.download('foto_foto1.jpg')
    assert 'secret' not in str(error.value)
