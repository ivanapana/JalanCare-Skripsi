import io,re,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from PIL import Image
from PIL.TiffImagePlugin import IFDRational
from app import create_app
from store import LocalStore,DuplicateError,distance
from vision import read_photo

class FakePrivacy:
    def detect(self,image):return []

class FakeDetector:
    def __init__(self,found=True):self.found=found
    def predict(self,image):return [{'confidence':.73,'xyxy':[50,50,200,200]}] if self.found else []
@pytest.fixture
def setup(tmp_path):
    store=LocalStore(tmp_path/'db.sqlite');app=create_app(dict(TESTING=True,PRIVATE=tmp_path,STORE=store,DETECTOR=FakeDetector(),PRIVACY_DETECTOR=FakePrivacy(),MODE='demo',LOCATION_LOOKUP=lambda a,b:dict(alamatLokasi='Tondano, Kabupaten Minahasa, Sulawesi Utara',daerah='Tondano',kabupaten='Minahasa',locationLookup='test')))
    return app,store

def token(client,path='/'):
    page=client.get(path);assert page.status_code==200
    return re.search(rb'name="csrf" value="([^"]+)"',page.data)[1].decode()
def login(client,role):
    path='/login/petugas' if role=='petugas' else '/login'
    return client.post(path,data={'csrf':token(client,path),'email':role+'@demo.local','password':'PetugasDemo2026!' if role=='petugas' else 'WargaDemo2026!'},follow_redirects=True)
def photo(size=(640,640),lat=1.45,with_gps=True):
    data=io.BytesIO();exif=Image.Exif()
    def dms(value):
        deg=int(value);minutes=int((value-deg)*60);seconds=((value-deg)*60-minutes)*60
        return (IFDRational(deg),IFDRational(minutes),IFDRational(seconds))
    if with_gps:exif[34853]={1:'N',2:dms(lat),3:'E',4:dms(124.9)}
    Image.new('RGB',size,'gray').save(data,format='JPEG',exif=exif);data.seek(0);return data

def analyze(client,lat='1.45'):
    return client.post('/report/analyze',data=dict(csrf=token(client,'/report/new'),namaJalan='Jalan Uji',kabupaten='Minahasa Utara',provinsi='yes',manual_location='yes',latitude=lat,longitude='124.9',blur_regions='{}',photos=[(photo(lat=float(lat)),'1.jpg'),(photo(lat=float(lat)),'2.jpg'),(photo(lat=float(lat)),'3.jpg')]),content_type='multipart/form-data')
def submit(client,rid):return client.post('/report/submit/'+rid,data=dict(csrf=token(client,'/report/preview/'+rid),narasi='Draf uji tanpa pengukuran.',reviewed='yes'))

def test_complete_workflow_and_permissions(setup):
    app,store=setup;w=app.test_client();p=app.test_client();other=app.test_client()
    assert login(w,'warga').status_code==200
    assert w.get('/users').status_code==403
    r=analyze(w);assert r.status_code==302;rid=r.location.rsplit('/',1)[-1]
    page=w.get(r.location);assert page.status_code==200 and b'Template' in page.data
    assert w.get('/media/'+rid+'/deteksi/foto1?preview=1').status_code==200
    assert submit(w,rid).status_code==302
    report=store.report(rid);assert report['jumlahDeteksi']==3 and report['jumlahLubang'] is None
    assert w.post('/report/'+rid+'/status',data={'csrf':token(w,'/dashboard'),'status':'Selesai'}).status_code==403
    # Distinct registered resident cannot read the report or its photos.
    other.post('/register',data=dict(csrf=token(other,'/register'),nama='Other',email='other@example.test',password='password123',confirm_password='password123'))
    other.post('/login',data=dict(csrf=token(other,'/login'),email='other@example.test',password='password123',confirm_password='password123'))
    assert other.get('/report/'+rid).status_code==403
    assert other.get('/media/'+rid+'/foto/foto1').status_code==403
    assert login(p,'petugas').status_code==200
    assert p.get('/statistics').status_code==200 and p.get('/users').status_code==200
    response=p.post('/report/'+rid+'/status',data=dict(csrf=token(p,'/report/'+rid),status='Selesai',catatan='Perbaikan selesai',jumlahLubang='1',panjangCm='20',lebarCm='15',kedalamanCm='5',nilaiSDI='10'))
    assert response.status_code==302
    assert w.get('/api/report/'+rid+'/status').json['status']=='Selesai'
    assert p.get('/export/pdf').data[:4]==b'%PDF'
    assert p.get('/export/xlsx').data[:2]==b'PK'
    # A completed report does not block a new report at the same location.
    assert '/report/preview/' in analyze(w).location

def test_duplicate_and_no_detection(setup):
    app,store=setup;c=app.test_client();login(c,'warga');r=analyze(c);rid=r.location.rsplit('/',1)[-1];submit(c,rid)
    r=analyze(c);assert r.location.endswith('/report/new') and len(store.reports())==1
    base=store.reports()[0];new=dict(base,idLaporan='other')
    with pytest.raises(DuplicateError):store.save_report(new)
    assert len(store.reports())==1
    app2=create_app(dict(TESTING=True,PRIVATE=Path(app.config['PRIVATE'])/'empty',STORE=store,DETECTOR=FakeDetector(False),PRIVACY_DETECTOR=FakePrivacy(),MODE='demo',LOCATION_LOOKUP=lambda a,b:dict(alamatLokasi='Tondano, Kabupaten Minahasa, Sulawesi Utara',daerah='Tondano',kabupaten='Minahasa',locationLookup='test')))
    c2=app2.test_client();login(c2,'warga');r=analyze(c2,lat='1.46');assert r.location.endswith('/report/new') and len(store.reports())==1

def test_csrf_and_validation(setup):
    app,store=setup;c=app.test_client()
    assert c.post('/demo-login/petugas').status_code==400
    login(c,'warga')
    r=c.post('/report/analyze',data=dict(csrf=token(c,'/report/new'),namaJalan='X',kabupaten='Minahasa Utara',provinsi='yes',photos=[(photo((320,320)),'bad.jpg'),(photo(),'ok.jpg'),(photo(),'ok2.jpg')]),content_type='multipart/form-data')
    assert r.location.endswith('/report/new') and not store.reports()
    assert abs(distance(1,124,1,124))<.001

def test_accounts_and_public_role(setup):
    app,store=setup;c=app.test_client()
    c.post('/register',data=dict(csrf=token(c,'/register'),nama='Test',email='test@example.test',password='password123',confirm_password='password123',role='petugas'))
    assert next(u for u in store.users() if u['email']=='test@example.test')['role']=='warga'
    login(c,'petugas')
    c.post('/users',data=dict(csrf=token(c,'/users'),action='create',nama='Staff2',email='staff2@example.test',password='password123',confirm_password='password123',role='petugas'))
    u=next(u for u in store.users() if u['email']=='staff2@example.test');assert u['role']=='petugas'
    c.post('/users',data=dict(csrf=token(c,'/users'),action='update',uid=u['uid'],nama='Staff2',email=u['email'],role='warga',disabled='yes'))
    assert store.user(u['uid'])['disabled']
    c.post('/users',data=dict(csrf=token(c,'/users'),action='delete',uid=u['uid']))
    assert store.user(u['uid']) is None

def test_languages(setup):
    app,_=setup;c=app.test_client()
    c.post('/language',data=dict(csrf=token(c),lang='en'))
    assert b'BETTER ROADS' in c.get('/').data

def test_gemini_invalid_output_and_fallback(monkeypatch):
    from narrative import generate
    from google import genai
    from types import SimpleNamespace
    report=dict(namaJalan='Uji',kabupaten='Minahasa',latitude=1.4,longitude=124.9,timestamp='2026-10-04',keterangan='',foto=[dict(angle='kiri',boxes=[])])
    monkeypatch.setattr(genai,'Client',lambda **kwargs:SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kwargs:SimpleNamespace(text='{"deskripsi":123,"tindakLanjut":"x"}'))))
    text,source,warning=generate(report,'test-not-a-real-key','test-model')
    assert source=='template' and warning and 'SDI' in text
    monkeypatch.setattr(genai,'Client',lambda **kwargs:SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kwargs:SimpleNamespace(text='{"deskripsi":"Indikasi lubang.","tindakLanjut":"Periksa lapangan."}'))))
    text,source,warning=generate(report,'test-not-a-real-key','test-model')
    assert source=='gemini' and warning is None

def test_blur_does_not_change_detection_input():
    from vision import blur_private
    import numpy as np
    img=Image.fromarray(np.random.default_rng(1).integers(0,256,size=(640,640,3),dtype=np.uint8))
    before=img.tobytes();blurred,count=blur_private(img,[[.1,.1,.3,.3]])
    assert img.tobytes()==before and blurred.tobytes()!=before and count>=1
    with pytest.raises(ValueError):blur_private(img,[[.8,.1,.5,.3]])

def test_exif_only_ignores_device_and_missing_exif(setup):
    app,store=setup;c=app.test_client();login(c,'warga')
    # Supplied device/manual location is ignored; EXIF remains the source.
    r=analyze(c);rid=r.location.rsplit('/',1)[-1]
    report=json.loads((Path(app.config['PRIVATE'])/('draft-'+rid)/'report.json').read_text())
    assert report['locationSource']=='EXIF' and abs(report['latitude']-1.45)<1e-6
    assert report['daerah']=='Tondano' and report['kabupaten']=='Minahasa'
    data=dict(csrf=token(c,'/report/new'),latitude='1.45',longitude='124.9',manual_location='yes',photos=[(photo(with_gps=False),'a.jpg'),(photo(with_gps=False),'b.jpg'),(photo(with_gps=False),'c.jpg')])
    response=c.post('/report/analyze',data=data,content_type='multipart/form-data',follow_redirects=True)
    assert 'GPS EXIF tidak ditemukan'.encode() in response.data
    assert len(store.reports())==1

def test_rejection_reason_translation_and_reopen_location(setup):
    app,store=setup;w=app.test_client();p=app.test_client();login(w,'warga');r=analyze(w);rid=r.location.rsplit('/',1)[-1];submit(w,rid);login(p,'petugas')
    assert p.post('/report/'+rid+'/status',data=dict(csrf=token(p,'/report/'+rid),status='Ditolak',catatan='')).status_code==400
    assert p.post('/report/'+rid+'/status',data=dict(csrf=token(p,'/report/'+rid),status='Ditolak',catatan='Bukan kewenangan jalan provinsi.')).status_code==302
    assert store.report(rid)['alasanPenolakan']=='Bukan kewenangan jalan provinsi.'
    w.post('/language',data=dict(csrf=token(w,'/dashboard'),lang='en'))
    page=w.get('/dashboard');assert b'Rejected' in page.data and b'>Ditolak<' not in page.data
    api=w.get('/api/report/'+rid+'/status').json
    assert api['label']=='Rejected' and api['note']=='Bukan kewenangan jalan provinsi.'
    assert '/report/preview/' in analyze(w).location
    page=p.get('/dashboard?kabupaten=Tondano');assert b'Jalan Uji' in page.data

def test_exactly_three_files_and_new_ui(setup):
    app,store=setup;c=app.test_client();login(c,'warga')
    page=c.get('/report/new').data
    assert b'name="photos"' in page and b'multiple' in page
    assert b'get-location' not in page and b'name="latitude"' not in page and b'name="provinsi"' not in page
    response=c.post('/report/analyze',data=dict(csrf=token(c,'/report/new'),photos=[(photo(),'one.jpg')]),content_type='multipart/form-data',follow_redirects=True)
    assert 'Pilih tepat tiga foto'.encode() in response.data

def test_address_lookup_cached_and_failure(tmp_path,monkeypatch):
    from location import reverse_location
    import location
    calls=[]
    class Response:
        def raise_for_status(self):pass
        def json(self):return {'address':{'town':'Tondano','county':'Kabupaten Minahasa','state':'Sulawesi Utara'}}
    monkeypatch.setattr(location.requests,'get',lambda *a,**kw:(calls.append(kw) or Response()))
    monkeypatch.setattr(location.time,'sleep',lambda x:None)
    result=reverse_location(1.4,124.9,tmp_path/'cache.db')
    assert result['daerah']=='Tondano' and result['kabupaten']=='Minahasa'
    assert reverse_location(1.4,124.9,tmp_path/'cache.db')==result and len(calls)==1
    def fail(*a,**kw):raise location.requests.RequestException()
    monkeypatch.setattr(location.requests,'get',fail)
    assert reverse_location(1.5,124.9,tmp_path/'cache.db')['locationLookup']=='unavailable'

def test_no_unrequested_blur():
    from vision import blur_private
    import numpy as np
    img=Image.fromarray(np.random.default_rng(7).integers(0,256,size=(640,640,3),dtype=np.uint8))
    result,count=blur_private(img,[])
    assert count==0 and result.tobytes()==img.tobytes()

def test_location_visible_before_analysis(setup):
    app,store=setup;c=app.test_client();login(c,'warga')
    r=c.post('/api/photos/location',data=dict(csrf=token(c,'/report/new'),photos=[(photo(),'a.jpg'),(photo(),'b.jpg'),(photo(),'c.jpg')]),content_type='multipart/form-data')
    assert r.status_code==200 and r.json['source']=='EXIF' and r.json['daerah']=='Tondano'
    assert not store.reports()
    assert 'Revisi 2.8'.encode() in c.get('/report/new').data

def test_revision23_translation_viewer_and_map_policy(setup):
    app,store=setup;c=app.test_client();login(c,'warga')
    with c.session_transaction() as session:session['lang']='en'
    r=analyze(c);rid=r.location.rsplit('/',1)[-1]
    page=c.get(r.location);text=page.get_data(as_text=True)
    assert page.headers['Referrer-Policy']=='strict-origin-when-cross-origin'
    assert 'id="photo-viewer"' in text and 'data-enlarge' in text
    assert 'Report of potential potholes' in text and 'Photo 1: 1 box' in text
    assert 'Initial draft based on model detections' in text
    assert 'original report' in text
    submit(c,rid)
    stored=store.report(rid)
    assert stored['narasiLaporan']=='Draf uji tanpa pengukuran.'
    store.update_report(rid,{'kabupaten':'Belum teridentifikasi'})
    assert 'Unidentified' in c.get('/dashboard').get_data(as_text=True)
    duplicate_page=c.get(analyze(c).location).get_data(as_text=True)
    assert 'An active report exists within 30 metres' in duplicate_page
    assert 'Ada laporan aktif dalam radius' not in duplicate_page
    staff=app.test_client();login(staff,'petugas')
    with staff.session_transaction() as session:session['lang']='en'
    stats=staff.get('/statistics').get_data(as_text=True)
    assert 'Unidentified' in stats and 'Location list / alternative' in stats
    assert 'data-tiles="https://tile.openstreetmap.org/' in stats


def test_geocoder_state_district_and_readable_labels():
    from location import parse_address
    from vision import annotate
    result=parse_address({'address':{'village':'Urongo','state_district':'Kabupaten Minahasa','state':'Sulawesi Utara'}})
    assert result['kabupaten']=='Minahasa' and 'Minahasa' in result['alamatLokasi']
    image=Image.new('RGB',(3000,4000),'gray')
    boxes=[{'confidence':.55,'xyxy':[2700,3800,2950,3990]}]
    output=annotate(image,boxes)
    assert output.size==image.size and image.getpixel((2700,3800))==(128,128,128)
    assert output.getpixel((2700,3800))!=(128,128,128)

def test_diagram_login_roles_and_logout(setup):
    app,store=setup;store.create_user('w@example.test','password123','Warga','warga');store.create_user('p@example.test','password123','Staff','petugas')
    w=app.test_client();p=app.test_client()
    response=w.post('/login',data={'csrf':token(w,'/login'),'email':'w@example.test','password':'password123'})
    assert response.location.endswith('/report/new')
    response=p.post('/login/petugas',data={'csrf':token(p,'/login/petugas'),'email':'w@example.test','password':'password123'})
    assert 'Peran akun tidak sesuai'.encode() in response.data
    with p.session_transaction() as session:assert 'uid' not in session
    response=p.post('/login/petugas',data={'csrf':token(p,'/login/petugas'),'email':'p@example.test','password':'password123'})
    assert response.location.endswith('/dashboard')
    assert p.post('/logout',data={'csrf':token(p,'/dashboard')}).location.endswith('/login')
    assert p.get('/users').status_code==302


def test_diagram_save_before_preview_and_edit_preserves_staff_work(setup):
    app,store=setup;c=app.test_client();login(c,'warga');r=analyze(c);rid=r.location.rsplit('/',1)[-1]
    saved=store.report(rid);assert saved is not None
    assert saved['laporanId']==saved['idLaporan'] and saved['wargaId']==saved['idPengguna']
    assert saved['confidenceScore']==.73 and saved['kategoriKerusakan'] is None
    assert saved['citraKiri'] and saved['citraKanan'] and saved['citraAtas']
    store.update_report(rid,{'status':'Sedang Ditangani','catatanPetugas':'Ditinjau'})
    assert submit(c,rid).status_code==302
    assert len(store.reports())==1 and store.report(rid)['status']=='Sedang Ditangani'
    assert store.report(rid)['catatanPetugas']=='Ditinjau'
    assert store.report(rid)['waktuDiperbarui']==store.report(rid)['updatedAt']
    assert app.extensions['controller'].__class__.__name__=='FlaskApp'
    assert app.extensions['controller'].authService is app.extensions['authService']


def test_diagram_staff_category_and_scoped_status_events(setup):
    app,store=setup;w=app.test_client();staff=app.test_client();login(w,'warga');r=analyze(w);rid=r.location.rsplit('/',1)[-1];login(staff,'petugas')
    response=staff.post('/report/'+rid+'/status',data={'csrf':token(staff,'/report/'+rid),'status':'Sedang Ditangani','catatan':'Survei','kategoriKerusakan':'Rusak Berat'})
    assert response.status_code==302 and store.report(rid)['kategoriKerusakan']=='Rusak Berat'
    assert 'kategoriKerusakan' in staff.get('/report/'+rid).get_data(as_text=True)
    from realtime import report_events
    owner=store.user(store.report(rid)['idPengguna']);other=store.create_user('other2@example.test','password123','Other','warga')
    generator=report_events(app.extensions['firebaseService'],owner,duration=1)
    first=next(generator);generator.close();assert rid in first and 'Sedang Ditangani' in first
    generator=report_events(app.extensions['firebaseService'],other,duration=1)
    first=next(generator);generator.close();assert 'data: []' in first and rid not in first
    response=w.get('/api/reports/events',buffered=False)
    assert response.mimetype=='text/event-stream' and rid.encode() in next(response.response)
    response.close()


def test_diagram_saving_failure_rolls_back_photos(setup,monkeypatch):
    app,store=setup;c=app.test_client();login(c,'warga')
    def fail(report):raise DuplicateError('Ada laporan aktif dalam radius 30 meter. Laporan baru tidak dikirim.')
    monkeypatch.setattr(store,'save_report',fail)
    response=analyze(c);assert response.location.endswith('/report/new') and not store.reports()
    private=Path(app.config['PRIVATE'])
    assert not list(private.glob('draft-*')) and not list((private/'reports').glob('*'))


def test_diagram_session_revocation_is_persistent(tmp_path):
    from services import FirebaseService
    class Backend:
        def verify(self,token):return 'uid'
    service=FirebaseService(Backend(),tmp_path)
    assert service.verify('opaque-test-token')=='uid'
    service.hapusSesiAutentikasi('opaque-test-token')
    with pytest.raises(ValueError):service.verify('opaque-test-token')
    with pytest.raises(ValueError):FirebaseService(Backend(),tmp_path).verify('opaque-test-token')
    assert service.verify('other-session')=='uid'

def test_firestore_watch_scopes_updates_and_unsubscribes(tmp_path):
    from realtime import report_events
    from services import FirebaseService
    class Watch:
        stopped=False
        def unsubscribe(self):self.stopped=True
    class Snapshot:
        def __init__(self,data):self.data=data
        def to_dict(self):return dict(self.data)
    class Query:
        def __init__(self):self.watch=Watch();self.filtered=False
        def document(self,uid):return uid
        def where(self,**kw):self.filtered=True;return self
        def on_snapshot(self,callback):
            self.callback=callback
            callback([Snapshot({'idLaporan':'mine','idPengguna':'owner','status':'Menunggu Verifikasi'}),Snapshot({'idLaporan':'private-other','idPengguna':'other','status':'Selesai'})],[],None)
            return self.watch
    class Backend:
        def __init__(self):self.query=Query();self.db=self
        def collection(self,name):return self.query
        def user(self,uid):return {'uid':uid,'role':'warga','disabled':False}
        def normalize(self,data):return data
    backend=Backend();service=FirebaseService(backend,tmp_path)
    stream=report_events(service,{'uid':'owner','role':'warga'})
    first=next(stream);assert backend.query.filtered and 'mine' in first and 'private-other' not in first
    backend.query.callback([Snapshot({'idLaporan':'mine','idPengguna':'owner','status':'Selesai'})],[],None)
    assert 'Selesai' in next(stream)
    stream.close();assert backend.query.watch.stopped

def test_demo_cannot_bypass_password(setup):
    app,store=setup;c=app.test_client()
    assert c.post('/demo-login/petugas',data={'csrf':token(c)}).status_code==404
    assert c.get('/users').status_code==302
    page=c.post('/login/petugas',data={'csrf':token(c,'/login/petugas'),'email':'petugas@demo.local','password':'wrong'})
    assert page.status_code==200 and c.get('/users').status_code==302
    assert login(c,'petugas').status_code==200 and c.get('/users').status_code==200
    assert 'demo-login' not in app.test_client().get('/').get_data(as_text=True)
    assert 'privacy-tools' not in (Path(__file__).parents[1]/'static/app.js').read_text()


def test_automatic_face_plate_blur_and_missing_model_blocks_save(setup,tmp_path):
    from privacy import PrivacyDetector
    from services import YOLODetectionService
    import numpy as np
    class Regions:
        def detect(self,image):return [{'kind':'face','region':[.1,.1,.2,.2]},{'kind':'plate','region':[.5,.5,.25,.1]}]
    service=YOLODetectionService(FakeDetector(),privacyDetector=Regions())
    image=Image.fromarray(np.random.default_rng(9).integers(0,256,(640,640,3),dtype=np.uint8));before=image.tobytes()
    blurred,count,regions=service.terapkanGaussianBlur(image,[])
    assert count==2 and blurred.tobytes()!=before and image.tobytes()==before
    assert {r['kind'] for r in regions}=={'face','plate'}
    app,store=setup;c=app.test_client();login(c,'warga')
    app.extensions['laporanService'].yoloService.privacyDetector=Regions()
    response=analyze(c);rid=response.location.rsplit('/',1)[-1]
    assert all(f['blurCount']==2 and f['privacySource']=='automatic-face-plate' for f in store.report(rid)['foto'])
    store.update_report(rid,{'status':'Ditolak'})
    app.extensions['laporanService'].yoloService.privacyDetector=PrivacyDetector(tmp_path/'missing-models')
    response=analyze(c)
    assert response.location.endswith('/report/new') and len(store.reports())==1
    assert len(list(Path(app.config['PRIVATE']).glob('draft-*')))==1


def test_bundled_privacy_models_run_on_real_onnx():
    from privacy import PrivacyDetector
    model=PrivacyDetector(Path(__file__).parents[1]/'models/privacy')
    assert model.detect(Image.new('RGB',(640,640),'gray'))==[]
    assert model.detect(Image.new('RGB',(1200,900),'gray'))==[]


def test_home_has_no_demo_account_section(setup):
    app,_=setup;c=app.test_client();page=c.get('/').get_data(as_text=True)
    assert 'Coba dua peran' not in page and 'Akun contoh lokal' not in page
    assert '/demo-login/' not in page
    assert c.post('/demo-login/petugas',data={'csrf':token(c)}).status_code==404
    assert c.get('/users').status_code==302
    assert login(c,'petugas').status_code==200 and c.get('/users').status_code==200

def test_site_validation_and_sdi_categories(setup):
    app,store=setup;c=app.test_client()
    page=c.get('/register').get_data(as_text=True)
    assert 'novalidate' in page and 'validation.js' in page and 'minlength="8"' in page
    response=c.post('/register',data={'csrf':token(c,'/register'),'nama':'Test','email':'new@example.test','password':'1234567','confirm_password':'1234567'},follow_redirects=True)
    assert 'Password harus 8–128 karakter.' in response.get_data(as_text=True)
    assert not any(u['email']=='new@example.test' for u in store.users())
    login(c,'warga');response=analyze(c);rid=response.location.rsplit('/',1)[-1]
    staff=app.test_client();login(staff,'petugas')
    page=staff.get('/report/'+rid).get_data(as_text=True)
    for category in ('Baik','Sedang','Rusak','Rusak Berat'):assert 'value="'+category+'"' in page
    assert 'value="Ringan"' not in page and 'value="Berat"' not in page
    response=staff.post('/report/'+rid+'/status',data={'csrf':token(staff,'/report/'+rid),'status':'Ditolak','catatan':'   '})
    assert response.status_code==400 and 'Alasan penolakan wajib diisi.' in response.get_data(as_text=True)
    for sdi,category in [(50,'Baik'),(50.1,'Sedang'),(100,'Sedang'),(100.1,'Rusak'),(150,'Rusak'),(150.1,'Rusak Berat')]:
        response=staff.post('/report/'+rid+'/status',data={'csrf':token(staff,'/report/'+rid),'status':'Sedang Ditangani','catatan':'Survei','nilaiSDI':str(sdi),'kategoriKerusakan':category,'prioritasPenanganan':'Tinjauan lapangan oleh dinas'})
        assert response.status_code==302
        assert store.report(rid)['kategoriKerusakan']==category and store.report(rid)['kategoriSumber']=='surveyor'
    response=staff.post('/report/'+rid+'/status',data={'csrf':token(staff,'/report/'+rid),'status':'Sedang Ditangani','nilaiSDI':'151','kategoriKerusakan':'Baik'})
    assert response.status_code==400 and 'tidak sesuai nilai SDI' in response.get_data(as_text=True)
    assert store.report(rid)['kategoriKerusakan']=='Rusak Berat'
    assert 'value="Ringan"' not in c.get('/report/'+rid).get_data(as_text=True)
    assert 'report-map' in c.get('/report/'+rid).get_data(as_text=True)


def test_report_format_follows_agency_fields_and_keeps_facts(setup):
    from narrative import format_report
    app,store=setup;c=app.test_client();login(c,'warga');response=analyze(c);rid=response.location.rsplit('/',1)[-1];report=store.report(rid)
    assert report['formatDinasTerverifikasi'] is False
    narrative=report['narasiLaporan']
    for text in ('DRAF LAPORAN INDIKASI LUBANG JALAN','GPS foto (EXIF)','Foto 1: 1 kotak','Kotak #1: confidence 0.73','DATA PEMERIKSAAN LAPANGAN','Nilai SDI: Belum tersedia','Kategori kondisi jalan: Belum tersedia'):assert text in narrative
    assert len(narrative)<6500
    report.update(nilaiSDI=50,kategoriKerusakan='Baik',prioritasPenanganan='Ditetapkan petugas')
    rendered=format_report(report,'Deskripsi uji','Verifikasi lapangan')
    assert 'Nilai SDI: 50' in rendered and 'Kategori kondisi jalan: Baik' in rendered


def test_firebase_reports_do_not_silently_use_local_storage_or_template(tmp_path):
    from services import FirebaseService,LaporanService,YOLODetectionService,GeminiReportService
    backend=LocalStore(tmp_path/'demo.db');firebase=FirebaseService(backend,tmp_path,strict_cloud=True)
    service=LaporanService(firebase,YOLODetectionService(FakeDetector(),privacyDetector=FakePrivacy()),GeminiReportService(None,'test'),tmp_path,lambda a,b:{},.25)
    with pytest.raises(ValueError,match='Storage foto belum aktif'):service.prosesLaporanBaru([], 'owner')
    backend.bucket=object()
    with pytest.raises(ValueError,match='Gemini belum aktif'):service.prosesLaporanBaru([], 'owner')
    assert not backend.reports()


def test_live_dashboard_and_statistics_requery_current_filtered_data(setup):
    app,store=setup;w=app.test_client();p=app.test_client();login(w,'warga');r=analyze(w);rid=r.location.rsplit('/',1)[-1];login(p,'petugas')
    assert rid.encode() in p.get('/dashboard',headers={'X-Live-Refresh':'1'}).data
    store.update_report(rid,{'status':'Selesai','updatedAt':'2026-10-14T00:00:00+00:00'})
    filtered=p.get('/dashboard?status=Menunggu+Verifikasi',headers={'X-Live-Refresh':'1'}).get_data(as_text=True)
    assert 'data-report-row="'+rid+'"' not in filtered
    stats=p.get('/statistics').get_data(as_text=True)
    assert 'data-live-statistics' in stats and 'monthly-summary' in stats and 'regional-summary' in stats

def test_cloud_photo_names_and_compatibility(tmp_path):
    from services import FirebaseService
    class Blob:
        def __init__(self,key):self.key=key
        def upload_from_filename(self,path,content_type):assert Path(path).is_file() and content_type=='image/jpeg'
        def delete(self):pass
    class Bucket:
        name='test-bucket'
        def __init__(self):self.keys=[]
        def blob(self,key):self.keys.append(key);return Blob(key)
    backend=LocalStore(tmp_path/'db');backend.bucket=Bucket();service=FirebaseService(backend,tmp_path,strict_cloud=True)
    folder=tmp_path/'photos';folder.mkdir()
    for angle in ['foto1','foto2','foto3']:
        for kind in ['foto','deteksi']:Image.new('RGB',(640,640),'gray').save(folder/(kind+'_'+angle+'.jpg'))
    report={'idLaporan':'photo-test','narrativeSource':'gemini','idPengguna':'owner','latitude':1.4,'longitude':124.9,'timestamp':'2026-10-14T00:00:00+00:00','status':'Menunggu Verifikasi','foto':[],'confidenceScores':[]}
    saved=service.simpanDataLaporan(report,folder)
    assert saved['citraUrls']==['gs://test-bucket/laporan/photo-test/foto_'+name+'.jpg' for name in ['kiri','kanan','atas']]
    assert saved['citraKiri'].endswith('foto_kiri.jpg')
    assert saved['storageNames']=={'foto1':'kiri','foto2':'kanan','foto3':'atas'}


def test_cloud_gemini_failure_does_not_commit_report(tmp_path):
    from services import FirebaseService,LaporanService,YOLODetectionService,GeminiReportService
    from werkzeug.datastructures import FileStorage
    backend=LocalStore(tmp_path/'db');backend.bucket=object();firebase=FirebaseService(backend,tmp_path,strict_cloud=True)
    gemini=GeminiReportService('test-key','test-model');gemini.generateNarasiLaporan=lambda r:('Fallback','template','Unavailable')
    service=LaporanService(firebase,YOLODetectionService(FakeDetector(),privacyDetector=FakePrivacy()),gemini,tmp_path,lambda a,b:{'kabupaten':'Minahasa','alamatLokasi':'Tondano'},.25)
    uploads=[FileStorage(photo(),filename=str(i)+'.jpg') for i in range(3)]
    with pytest.raises(ValueError,match='Gemini belum berhasil'):service.prosesLaporanBaru(uploads,'owner')
    assert not backend.reports() and not list(tmp_path.glob('draft-*'))

def test_gemini_does_not_accept_invented_physical_measurements(monkeypatch):
    from narrative import generate
    from google import genai
    from types import SimpleNamespace
    report={'namaJalan':'Jalan Uji','kabupaten':'Minahasa','latitude':1.4,'longitude':124.9,'timestamp':'2026-10-14','keterangan':'','foto':[{'angle':'foto1','boxes':[]}]}
    monkeypatch.setattr(genai,'Client',lambda **kw:SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kw:SimpleNamespace(text='{"deskripsi":"Lubang memiliki kedalaman 10 cm dan SDI 200.","tindakLanjut":"Prioritas tinggi."}'))))
    text,source,warning=generate(report,'test-key','test-model')
    assert source=='template' and warning and '10 cm' not in text and 'SDI 200' not in text
