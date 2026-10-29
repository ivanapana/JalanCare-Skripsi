"""Application services named and wired as in the thesis diagrams."""
import hashlib,io,json,logging,math,os,shutil,sqlite3,time,uuid
from pathlib import Path
from PIL import Image
from store import DuplicateError,duplicate,distance,now
from vision import read_photo,blur_private,annotate,ANGLES
from narrative import generate,DISCLAIMER
from models_data import Pengguna,Laporan

class FirebaseService:
    """Firebase adapter in production; LocalStore is the explicit demo substitute."""
    def __init__(self,backend,private,strict_cloud=False):
        self.backend=backend;self.private=Path(private);self.strict_cloud=strict_cloud
        self.projectId=getattr(getattr(backend,'app',None),'project_id',None)
        self.credential=os.getenv('FIREBASE_CREDENTIALS')
        self.firestoreClient=getattr(backend,'db',None)
        self.sessions=self.private/'revoked_sessions.sqlite3'
        with sqlite3.connect(self.sessions) as db:db.execute('CREATE TABLE IF NOT EXISTS revoked (digest TEXT PRIMARY KEY, expires REAL)')
    def __getattr__(self,name):return getattr(self.backend,name)
    def buatAkunBaru(self,email,password,name,role='warga'):
        return Pengguna.fromDict(self.backend.create_user(email,password,name,role)).toDict()
    def verifikasiKredensial(self,email,password):return self.backend.login(email,password)
    def hapusSesiAutentikasi(self,token=None):
        # Revoke this server-managed Firebase session without signing out other devices.
        if token:
            with sqlite3.connect(self.sessions) as db:
                db.execute('DELETE FROM revoked WHERE expires<?',(time.time(),))
                db.execute('INSERT OR REPLACE INTO revoked VALUES (?,?)',(hashlib.sha256(token.encode()).hexdigest(),time.time()+8*3600))
    def verify(self,token):
        with sqlite3.connect(self.sessions) as db:
            if db.execute('SELECT 1 FROM revoked WHERE digest=? AND expires>?',(hashlib.sha256(token.encode()).hexdigest(),time.time())).fetchone():raise ValueError('Sesi sudah berakhir.')
        return self.backend.verify(token)
    def simpanAkun(self,data):
        self.backend.change_user(data['uid'],{k:v for k,v in data.items() if k!='uid'})
    def updateAkun(self,uid,data,password=None):self.backend.change_user(uid,data,password)
    def hapusAkunFirebase(self,uid):self.backend.delete_user(uid)
    def getSeluruhAkun(self):return [Pengguna.fromDict(u).toDict() for u in self.backend.users()]
    def cekLokasiDuplikat(self,report):return duplicate(self.queryLaporan(),report)
    def queryLaporan(self):return [Laporan.fromDict(r).toDict() for r in self.backend.reports()]
    def queryDetailLaporan(self,rid):
        r=self.backend.report(rid)
        return Laporan.fromDict(r).toDict() if r else None
    def simpanDataLaporan(self,report,folder):
        r=dict(report);bucket=getattr(self.backend,'bucket',None)
        supabase=getattr(self.backend,'photo_storage',None)
        if self.strict_cloud and not (supabase or bucket):raise ValueError('Storage foto belum aktif. Lengkapi konfigurasi Supabase pada .env.')
        if self.strict_cloud and r.get('narrativeSource')!='gemini':raise ValueError('Gemini belum berhasil membuat narasi. Laporan tidak disimpan; coba lagi.')
        uploaded=[];supabase_uploaded=[];photos=None;target=self.private/'reports'/r['idLaporan']
        try:
            r['citraUrls']=[]
            if supabase:
                photos=self.backend.photo_access(r['idPengguna'],r['idLaporan'],write=True)
                for angle in ANGLES:
                    for kind in ('foto','deteksi'):
                        filename=f'{kind}_{angle}.jpg'
                        # Include an attempted upload in rollback after network ambiguity.
                        supabase_uploaded.append(filename)
                        path=photos.upload_file(filename,folder/filename)
                        if kind=='foto':r['citraUrls'].append(f'supabase://{supabase.bucket}/{path}')
                r['storage']='supabase'
            elif bucket:
                r['storageNames']={'foto1':'kiri','foto2':'kanan','foto3':'atas'}
                for angle in ANGLES:
                    for kind in ('foto','deteksi'):
                        key=f"laporan/{r['idLaporan']}/{kind}_{r['storageNames'][angle]}.jpg";blob=bucket.blob(key)
                        blob.upload_from_filename(str(folder/f'{kind}_{angle}.jpg'),content_type='image/jpeg');uploaded.append(blob)
                        if kind=='foto':r['citraUrls'].append(f'gs://{bucket.name}/{key}')
                r['storage']='firebase'
            else:
                target.parent.mkdir(exist_ok=True);shutil.copytree(folder,target)
                r['storage']='local';r['citraUrls']=[f"/media/{r['idLaporan']}/foto/{angle}" for angle in ANGLES]
            r=Laporan.fromDict(r).toDict();self.backend.save_report(r)
            return r
        except Exception:
            if photos and supabase_uploaded:
                # A timeout can occur after a Firestore commit. Never remove its photos.
                try:committed=self.backend.report(r['idLaporan']) is not None
                except Exception:committed=True
                if not committed:
                    try:photos.remove_failed_uploads(supabase_uploaded)
                    except Exception:logging.getLogger(__name__).warning('Periksa sisa upload Supabase laporan %s',r['idLaporan'])
            for blob in uploaded:
                try:blob.delete()
                except Exception:pass
            shutil.rmtree(target,ignore_errors=True);raise
    def updateStatusLaporan(self,rid,data):
        values=dict(data)
        if 'updatedAt' in values:values['waktuDiperbarui']=values['updatedAt']
        self.backend.update_report(rid,values)
    # Legacy interface for existing routes and old reports.
    def reports(self):return self.queryLaporan()
    def report(self,rid):return self.queryDetailLaporan(rid)
    def update_report(self,rid,data):return self.updateStatusLaporan(rid,data)

class AuthService:
    def __init__(self,firebaseService):self.firebaseService=firebaseService
    def registrasiAkun(self,email,password,name):return self.firebaseService.buatAkunBaru(email,password,name,'warga')
    def login(self,email,password,expectedRole='warga'):
        user,token=self.firebaseService.verifikasiKredensial(email,password)
        if user.get('role')!=expectedRole:raise ValueError('Peran akun tidak sesuai. Gunakan halaman login warga atau petugas yang benar.')
        return user,token
    def logout(self,token=None):self.firebaseService.hapusSesiAutentikasi(token)
    def tambahAkun(self,email,password,name,role):return self.firebaseService.buatAkunBaru(email,password,name,role)
    def ubahAkun(self,uid,data,password=None):return self.firebaseService.updateAkun(uid,data,password)
    def hapusAkun(self,uid):return self.firebaseService.hapusAkunFirebase(uid)
    def getSeluruhAkun(self):return self.firebaseService.getSeluruhAkun()

class YOLODetectionService:
    def __init__(self,detector,auto_faces=False,privacyDetector=None):
        self.detector=detector;self.auto_faces=auto_faces;self.privacyDetector=privacyDetector
        self.modelPath=getattr(detector,'path',None);self.confidenceThreshold=getattr(detector,'confidence',None)
    def praprosesDanBacaGPS(self,fotoList):
        import cv2,numpy as np
        result=[]
        for upload in fotoList:
            image,loc,stamp=read_photo(upload)
            # EXIF is read before decoding orientation-normalized RGB pixels with OpenCV.
            bgr=cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR)
            rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
            result.append((Image.fromarray(rgb),loc,stamp))
        return result
    def deteksiLubang(self,citra):return self.detector.predict(citra)
    def terapkanGaussianBlur(self,citra,regions):
        if self.privacyDetector is None:raise ValueError('Model privasi belum lengkap. Salin folder models/privacy dari paket terbaru; laporan tidak disimpan.')
        detections=self.privacyDetector.detect(citra)
        blurred,count=blur_private(citra,[d['region'] for d in detections]+regions,auto_faces=False)
        return blurred,count,detections

class GeminiReportService:
    def __init__(self,apiKey,modelName):self.apiKey=apiKey;self.modelName=modelName
    def generateNarasiLaporan(self,hasilDeteksi):return generate(hasilDeteksi,self.apiKey,self.modelName)

class LaporanService:
    def __init__(self,firebaseService,yoloService,geminiService,private,lookup,confidence):
        self.firebaseService=firebaseService;self.yoloService=yoloService;self.geminiService=geminiService
        self.private=Path(private);self.lookup=lookup;self.confidence=confidence
    def prosesLaporanBaru(self,fotoList,uid,name='',note='',regions=None):
        if self.firebaseService.strict_cloud:
            if not (getattr(self.firebaseService.backend,'photo_storage',None) or getattr(self.firebaseService.backend,'bucket',None)):raise ValueError('Storage foto belum aktif. Lengkapi konfigurasi Supabase pada .env.')
            if not self.geminiService.apiKey:raise ValueError('Gemini belum aktif. Lengkapi konfigurasi untuk membuat laporan pada mode Firebase.')
        if len(name)>200:raise ValueError('Nama jalan maksimal 200 karakter.')
        if len(note)>2000:raise ValueError('Keterangan maksimal 2.000 karakter.')
        if len(fotoList)!=3 or any(not f.filename for f in fotoList):raise ValueError('Pilih tepat tiga foto dalam satu unggahan.')
        regions=regions if regions is not None else {}
        if not isinstance(regions,dict):raise ValueError('Area privasi tidak valid.')
        photos=self.yoloService.praprosesDanBacaGPS(fotoList)
        locations=[loc for _,loc,_ in photos if loc]
        if not locations:raise ValueError('GPS EXIF tidak ditemukan pada ketiga foto. Aktifkan lokasi untuk kamera dan unggah file foto asli yang menyimpan lokasi; lokasi perangkat saat upload tidak digunakan.')
        lat,lon=locations[0]
        if any(not math.isfinite(v) for loc in locations for v in loc) or not -.6<=lat<=6 or not 122<=lon<=128:raise ValueError('GPS foto tidak valid atau berada di luar rentang Sulawesi Utara.')
        if any(distance(lat,lon,*loc)>30 for loc in locations[1:]):raise ValueError('GPS antar foto berbeda lebih dari 30 meter. Periksa foto yang dipilih.')
        location=self.lookup(lat,lon)
        r=dict(idLaporan=uuid.uuid4().hex,idPengguna=uid,namaJalan=name or location.get('alamatLokasi') or 'Lokasi berdasarkan GPS foto',kabupaten=location.get('kabupaten','Belum teridentifikasi'),keterangan=note,latitude=lat,longitude=lon,locationSource='EXIF',timestamp=now(),status='Menunggu Verifikasi',foto=[],disclaimer=DISCLAIMER,threshold=self.confidence,captureTimes=[stamp for _,_,stamp in photos],kategoriKerusakan=None)
        r.update(location);r['updatedAt']=r['timestamp']
        if self.firebaseService.cekLokasiDuplikat(r):raise DuplicateError('Ada laporan aktif dalam radius 30 meter. Laporan baru tidak dikirim.')
        for angle,(image,_,_) in zip(ANGLES,photos):
            boxes=self.yoloService.deteksiLubang(image)
            r['foto'].append(dict(angle=angle,boxes=boxes,width=image.width,height=image.height,blurCount=0))
        r['jumlahDeteksi']=sum(len(f['boxes']) for f in r['foto']);r['jumlahLubang']=None
        if not r['jumlahDeteksi']:raise ValueError('Tidak ada lubang terdeteksi pada ketiga foto. Laporan tidak dibuat. Periksa foto dan batas confidence.')
        r['boundingBoxes']=[dict(angle=f['angle'],xyxy=b['xyxy']) for f in r['foto'] for b in f['boxes']]
        r['confidenceScores']=[b['confidence'] for f in r['foto'] for b in f['boxes']]
        r['narasiLaporan'],r['narrativeSource'],warning=self.geminiService.generateNarasiLaporan(r)
        if self.firebaseService.strict_cloud and r['narrativeSource']!='gemini':raise ValueError('Gemini belum berhasil membuat narasi. Laporan tidak disimpan; coba lagi.')
        r['formatLaporan']='draft-laporan-lubang-sesuai-cakupan';r['formatDinasTerverifikasi']=False
        for old in self.private.glob('draft-*'):
            if time.time()-old.stat().st_mtime>86400:shutil.rmtree(old,ignore_errors=True)
        folder=self.private/('draft-'+r['idLaporan']);folder.mkdir()
        try:
            for f,(image,_,_) in zip(r['foto'],photos):
                selected=regions.get(f['angle'],[])
                if not isinstance(selected,list) or len(selected)>50:raise ValueError('Maksimal 50 area privasi per foto.')
                if any(not isinstance(x,list) or len(x)!=4 or any(not isinstance(v,(int,float)) for v in x) for x in selected):raise ValueError('Area privasi tidak valid.')
                blurred,f['blurCount'],f['privacyDetections']=self.yoloService.terapkanGaussianBlur(image,selected)
                f['privacySource']='automatic-face-plate'
                blurred.save(folder/f"foto_{f['angle']}.jpg",quality=90)
                annotate(blurred,f['boxes']).save(folder/f"deteksi_{f['angle']}.jpg",quality=90)
            (folder/'report.json').write_text(json.dumps(r,ensure_ascii=False),encoding='utf8')
            r=self.firebaseService.simpanDataLaporan(r,folder)
            try:(folder/'report.json').write_text(json.dumps(r,ensure_ascii=False),encoding='utf8')
            except OSError:pass  # Initial preview remains usable; committed report is canonical.
        except Exception:
            # A successfully committed report must survive failure of its preview file.
            shutil.rmtree(folder,ignore_errors=True);raise
        return r,warning
    def getSeluruhLaporan(self):return self.firebaseService.queryLaporan()
    def getDetailLaporan(self,rid):return self.firebaseService.queryDetailLaporan(rid)
    def perbaruiStatusLaporan(self,rid,data):return self.firebaseService.updateStatusLaporan(rid,data)
    def getRekapStatistik(self,rows):
        from collections import Counter
        return dict(by_status=Counter(r['status'] for r in rows),by_region=Counter(r['kabupaten'] for r in rows),by_month=dict(sorted(Counter(r['timestamp'][:7] for r in rows).items())),total=len(rows))
    def eksporLaporan(self,rows,format):
        from exports import build_export
        return build_export(rows,format)
