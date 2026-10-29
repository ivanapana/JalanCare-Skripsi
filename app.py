import io,json,math,os,re,secrets,shutil,uuid
from collections import Counter
from datetime import datetime,timedelta,timezone
from functools import wraps
from pathlib import Path
from werkzeug.exceptions import HTTPException
from flask import Response,Flask,abort,flash,g,jsonify,redirect,render_template,request,send_file,session,url_for
from dotenv import load_dotenv
from store import LocalStore,FirebaseStore,DuplicateError,duplicate,now,distance
from vision import Detector,ANGLES,read_photo,blur_private,annotate
from narrative import generate,DISCLAIMER,english_summary,DISCLAIMER_EN
from i18n import translate
from location import reverse_location
from services import FirebaseService,AuthService,LaporanService,YOLODetectionService,GeminiReportService
from controllers import FlaskApp
from privacy import PrivacyDetector
from dinas import GROUPS as DINAS_GROUPS,META as DINAS_META,NUMBERS as DINAS_NUMBERS,EN_OPTIONS,parse_survey,hole_class,category_display

BASE=Path(__file__).resolve().parent
load_dotenv(BASE/'.env')
STATUSES=['Menunggu Verifikasi','Sedang Ditangani','Selesai','Ditolak']
STATUS_EN={'Menunggu Verifikasi':'Pending verification','Sedang Ditangani':'In progress','Selesai':'Completed','Ditolak':'Rejected'}
PHOTO_LABELS={'foto1':('Foto 1','Photo 1'),'foto2':('Foto 2','Photo 2'),'foto3':('Foto 3','Photo 3'),'kiri':('Foto kiri','Left photo'),'kanan':('Foto kanan','Right photo'),'atas':('Foto atas','Top photo')}
CATEGORIES=['Baik','Sedang','Rusak','Rusak Berat']
CATEGORY_EN={'Baik':'Good','Sedang':'Fair','Rusak':'Minor damage','Rusak Ringan':'Minor damage','Rusak Berat':'Severely damaged'}
REGIONS=['Manado','Bitung','Tomohon','Kotamobagu','Minahasa','Minahasa Utara','Minahasa Selatan','Minahasa Tenggara','Bolaang Mongondow','Bolaang Mongondow Utara','Bolaang Mongondow Selatan','Bolaang Mongondow Timur','Kepulauan Sangihe','Kepulauan Talaud','Kepulauan Siau Tagulandang Biaro']

def create_app(config=None):
    app=Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=32*1024*1024,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE','false').lower()=='true',PERMANENT_SESSION_LIFETIME=timedelta(hours=8),MODE=os.getenv('APP_MODE','demo'),PRIVATE=BASE/'private',MODEL_PATH=Path(os.getenv('MODEL_PATH',str(BASE/'models/best_potholes.pt'))),CONFIDENCE=float(os.getenv('YOLO_CONFIDENCE','0.25')))
    if config:app.config.update(config)
    private=Path(app.config['PRIVATE']);private.mkdir(exist_ok=True,parents=True)
    key=os.getenv('SECRET_KEY')
    if not key:
        keyfile=private/'session.key'
        if not keyfile.exists():keyfile.write_text(secrets.token_hex(32))
        key=keyfile.read_text().strip()
    app.secret_key=key
    if app.config['MODE'] not in ('demo','firebase'):raise ValueError('APP_MODE harus demo atau firebase.')
    if not 0<=app.config['CONFIDENCE']<=1:raise ValueError('YOLO_CONFIDENCE harus 0 sampai 1.')
    store=app.config.get('STORE')
    if not store:
        credential=Path(os.getenv('FIREBASE_CREDENTIALS','secrets/firebase-service-account.json'))
        if not credential.is_absolute():credential=BASE/credential
        if app.config['MODE']=='demo':
            store=LocalStore(private/'demo.sqlite3')
        else:
            # Supabase stores only files. Firebase Auth and Firestore stay intact.
            from photo_storage import SupabasePhotoStorage
            photos=SupabasePhotoStorage(os.getenv('SUPABASE_URL'),os.getenv('SUPABASE_PUBLISHABLE_KEY'),os.getenv('SUPABASE_STORAGE_BUCKET','laporan-foto')) if os.getenv('SUPABASE_URL') else None
            store=FirebaseStore(str(credential),os.getenv('FIREBASE_STORAGE_BUCKET'),os.environ['FIREBASE_WEB_API_KEY'],photo_storage=photos)
    app.extensions['store']=store
    detector=app.config.get('DETECTOR') or Detector(app.config['MODEL_PATH'],app.config['CONFIDENCE'])
    firebase=FirebaseService(store,private,strict_cloud=app.config['MODE']=='firebase')
    authService=AuthService(firebase)
    privacyDetector=app.config.get('PRIVACY_DETECTOR') or PrivacyDetector(BASE/'models/privacy')
    yoloService=YOLODetectionService(detector,privacyDetector=privacyDetector)
    geminiService=GeminiReportService(os.getenv('GEMINI_API_KEY'),os.getenv('GEMINI_MODEL','gemini-2.5-flash'))
    laporanService=LaporanService(firebase,yoloService,geminiService,private,app.config.get('LOCATION_LOOKUP',lambda a,b:reverse_location(a,b,private/'location_cache.sqlite3')),app.config['CONFIDENCE'])
    if app.config['MODE']=='demo':
        marker=private/'demo-passwords-v2_5.initialized'
        if not marker.exists():
            for role,name,password in [('warga','Warga Demo',os.getenv('DEMO_RESIDENT_PASSWORD','WargaDemo2026!')),('petugas','Petugas Demo',os.getenv('DEMO_STAFF_PASSWORD','PetugasDemo2026!'))]:
                email=role+'@demo.local';user=next((u for u in store.users() if u['email']==email),None)
                if user:store.change_user(user['uid'],dict(email=email,nama=name,role=role,disabled=False),password)
                else:store.create_user(email,password,name,role)
            marker.write_text('Local demonstration accounts require passwords. Never used in Firebase mode.')
    store=firebase
    controller=FlaskApp(app,authService,laporanService)
    app.extensions.update(controller=controller,authService=authService,laporanService=laporanService,firebaseService=firebase)
    attempts={}

    def csrf():
        if 'csrf' not in session:session['csrf']=secrets.token_hex(24)
        return session['csrf']
    def protected(role=None):
        def decorate(fn):
            @wraps(fn)
            def wrapped(*a,**k):
                if not g.user:return redirect(url_for('login'))
                if role and g.user['role']!=role:abort(403)
                return fn(*a,**k)
            return wrapped
        return decorate
    @app.before_request
    def before():
        g.user=None
        if app.config['MODE']=='demo' and session.get('uid') and session.get('auth_version')!='2.5.1':
            language=session.get('lang','id');session.clear();session['lang']=language
        if session.get('uid'):
            try:
                uid=store.verify(session['firebase_session']) if app.config['MODE']=='firebase' else session['uid']
                u=store.user(uid)
                if u and not u.get('disabled'):g.user=u
                else:session.clear()
            except Exception:session.clear()
        if request.method=='POST':
            token=request.form.get('csrf') or request.headers.get('X-CSRF-Token','')
            if not token or not secrets.compare_digest(token,session.get('csrf','')):abort(400,description='Sesi formulir kedaluwarsa. Muat ulang halaman.')
    def ui_text(value):return translate(value,session.get('lang','id'))
    @app.context_processor
    def inject():return dict(status_text=lambda s:STATUS_EN.get(s,s) if session.get('lang','id')=='en' else s,photo_text=lambda s:PHOTO_LABELS.get(s,(s,s))[1 if session.get('lang','id')=='en' else 0],badge_class=lambda s:{'Selesai':'done','Sedang Ditangani':'working','Ditolak':'rejected'}.get(s,''),user=g.user,csrf=csrf,version='2.8',dinas_groups=DINAS_GROUPS,dinas_meta=DINAS_META,dinas_numbers=DINAS_NUMBERS,dinas_option=lambda v:EN_OPTIONS.get(v,v) if session.get('lang')=='en' else v,hole_class=hole_class,categories=CATEGORIES,category_text=lambda c:CATEGORY_EN.get(c,'Previous category — reassessment required') if session.get('lang')=='en' else category_display(c),ui_text=ui_text,english_summary=english_summary,disclaimer_en=DISCLAIMER_EN,map_tiles=os.getenv('MAP_TILE_URL','https://tile.openstreetmap.org/{z}/{x}/{y}.png'),map_attribution=os.getenv('MAP_ATTRIBUTION','© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'),mode=app.config['MODE'],statuses=STATUSES,regions=REGIONS,lang=session.get('lang','id'),t=lambda a,b:a if session.get('lang','id')=='id' else b,confidence=app.config['CONFIDENCE'])
    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options']='nosniff';response.headers['X-Frame-Options']='DENY';response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
        if request.endpoint!='static':response.headers['Cache-Control']='no-store'
        return response
    @app.errorhandler(413)
    def too_large(e):return render_template('error.html',message='Ukuran unggahan terlalu besar. Maksimal 10 MB per foto.'),413
    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    def errors(e):return render_template('error.html',message=e.description),e.code
    @app.errorhandler(Exception)
    def unexpected(e):
        if isinstance(e,HTTPException):return render_template('error.html',message=e.description),e.code
        app.logger.error('Application failure: %s',type(e).__name__)
        return render_template('error.html',message='Proses belum berhasil. Periksa koneksi dan konfigurasi layanan, lalu coba lagi.'),500
    @app.get('/')
    def home():return render_template('home.html')
    @app.post('/language')
    def language():
        session['lang']='en' if request.form.get('lang')=='en' else 'id'
        path=request.form.get('return_path','')
        if not path.startswith('/') or path.startswith('//') or '\\' in path:path=url_for('dashboard') if g.user else url_for('home')
        return redirect(path)
    def rate_limit():
        key=request.remote_addr;time=datetime.now().timestamp()
        attempts[key]=[x for x in attempts.get(key,[]) if time-x<300]
        if len(attempts[key])>=10:raise ValueError('Terlalu banyak percobaan. Tunggu 5 menit.')
        attempts[key].append(time)
    def fields():
        email=request.form.get('email','').strip().lower();name=request.form.get('nama','').strip();password=request.form.get('password','')
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email) or len(email)>254 or not name or len(name)>100:raise ValueError('Isi nama dan email yang valid.')
        if len(password)<8 or len(password)>128:raise ValueError('Password harus 8–128 karakter.')
        return email,name,password
    @app.route('/register',methods=['GET','POST'])
    def register():
        if request.method=='POST':
            try:
                rate_limit();email,name,password=fields()
                if request.form.get('confirm_password')!=password:raise ValueError('Konfirmasi password tidak sama.')
                authService.registrasiAkun(email,password,name)
                flash('Akun berhasil dibuat. Silakan masuk.','success');return redirect(url_for('login'))
            except ValueError as e:flash(str(e),'error')
            except Exception:flash('Registrasi gagal. Email mungkin sudah digunakan atau layanan belum dikonfigurasi.','error')
        return render_template('auth.html',register=True)
    @app.route('/login/petugas',methods=['GET','POST'],endpoint='login_petugas')
    @app.route('/login',methods=['GET','POST'])
    def login():
        if request.method=='POST':
            try:
                password=request.form.get('password','')
                if not 8<=len(password)<=128:raise ValueError('Password harus 8–128 karakter.')
                rate_limit();u,token=authService.login(request.form.get('email','').strip(),request.form.get('password',''),'petugas' if request.path=='/login/petugas' else 'warga')
                language=session.get('lang','id');session.clear();session.update(uid=u['uid'],lang=language,auth_version='2.5.1');session.permanent=True
                if token:session['firebase_session']=token
                return redirect(url_for('dashboard' if u['role']=='petugas' else 'new_report'))
            except ValueError as e:flash(str(e),'error')
            except Exception:flash('Login belum berhasil. Periksa pengaturan Firebase.','error')
        return render_template('auth.html',register=False,staff_login=request.path=='/login/petugas')
    @app.post('/logout')
    def logout():
        authService.logout(session.get('firebase_session'));language=session.get('lang','id');session.clear();session['lang']=language
        return redirect(url_for('login'))
    def visible():return [r for r in laporanService.getSeluruhLaporan() if g.user['role']=='petugas' or r['idPengguna']==g.user['uid']]
    def filtered():
        rows=visible()
        for key,field in [('status','status'),('kabupaten','kabupaten')]:
            value=request.args.get(key)
            if key=='kabupaten' and value=='Tondano':rows=[r for r in rows if 'tondano' in (r.get('daerah','')+' '+r.get('alamatLokasi','')).lower()]
            elif value:rows=[r for r in rows if r.get(field)==value]
        start=request.args.get('start','');end=request.args.get('end','')
        if start:rows=[r for r in rows if r['timestamp'][:10]>=start]
        if end:rows=[r for r in rows if r['timestamp'][:10]<=end]
        return rows
    def accessible(rid):
        r=laporanService.getDetailLaporan(rid)
        if not r:abort(404)
        if g.user['role']!='petugas' and r['idPengguna']!=g.user['uid']:abort(403)
        return r
    @app.get('/dashboard')
    @protected()
    def dashboard():
        rows=filtered();all_rows=visible()
        return render_template('dashboard.html',rows=rows,counts=Counter(r['status'] for r in all_rows),total=len(all_rows))
    @app.get('/statistics')
    @protected('petugas')
    def statistics():
        rows=filtered()
        return render_template('statistics.html',rows=rows,**laporanService.getRekapStatistik(rows),map_points=[dict(lat=r['latitude'],lon=r['longitude'],label=r.get('alamatLokasi') or r['namaJalan'],status=r['status']) for r in rows])
    @app.get('/report/new')
    @protected('warga')
    def new_report():return render_template('new_report.html')
    @app.post('/api/photos/location')
    @protected('warga')
    def preview_location():
        try:
            uploads=request.files.getlist('photos')
            if len(uploads)!=3:raise ValueError('Pilih tepat tiga foto.')
            locations=[]
            for upload in uploads:
                _,point,_=read_photo(upload)
                if point:locations.append(point)
            if not locations:raise ValueError('GPS EXIF tidak ditemukan. Gunakan foto asli yang menyimpan lokasi.')
            lat,lon=locations[0]
            if any(not math.isfinite(v) for point in locations for v in point) or not -.6<=lat<=6 or not 122<=lon<=128:raise ValueError('GPS foto tidak valid atau berada di luar rentang Sulawesi Utara.')
            if any(distance(lat,lon,*p)>30 for p in locations[1:]):raise ValueError('GPS antar foto berbeda lebih dari 30 meter.')
            location=app.config.get('LOCATION_LOOKUP',lambda a,b:reverse_location(a,b,private/'location_cache.sqlite3'))(lat,lon)
            return jsonify(latitude=lat,longitude=lon,source='EXIF',**location)
        except ValueError as e:return jsonify(error=ui_text(str(e))),400
    @app.post('/report/analyze')
    @protected('warga')
    def analyze():
        try:
            report,warning=laporanService.prosesLaporanBaru(request.files.getlist('photos'),g.user['uid'],request.form.get('namaJalan','').strip(),request.form.get('keterangan','').strip(),json.loads(request.form.get('blur_regions','{}')))
            if warning:flash(warning,'warning')
            flash('Laporan tersimpan. Periksa hasil dan narasi laporan.','success')
            return redirect(url_for('preview',rid=report['idLaporan']))
        except (ValueError,DuplicateError,json.JSONDecodeError,TypeError) as e:
            flash(str(e),'error');return redirect(url_for('new_report'))
    def draft(rid):
        if len(rid)!=32 or not all(c in '0123456789abcdef' for c in rid):abort(404)
        folder=private/f'draft-{rid}'
        if not (folder/'report.json').exists():abort(404)
        r=json.loads((folder/'report.json').read_text(encoding='utf8'))
        if r['idPengguna']!=g.user['uid']:abort(403)
        if datetime.now().timestamp()-folder.stat().st_mtime>86400:abort(404,description='Draf kedaluwarsa. Unggah foto kembali.')
        return r,folder
    @app.get('/report/preview/<rid>')
    @protected('warga')
    def preview(rid):
        r,_=draft(rid);return render_template('detail.html',report=r,preview=True)
    @app.post('/report/submit/<rid>')
    @protected('warga')
    def submit(rid):
        r,folder=draft(rid);text=request.form.get('narasi','').strip()
        if not text or len(text)>6500:abort(400,description='Draf laporan wajib diisi, maksimal 6.500 karakter.')
        if request.form.get('reviewed')!='yes':abort(400,description='Periksa foto, privasi, dan draf sebelum mengirim.')
        existing=store.report(rid)
        if existing:accessible(rid)
        else:firebase.simpanDataLaporan(r,folder)  # Migrate an unsubmitted revision-2.3 preview.
        # Analysis already saved this report, as in the sequence diagram.
        # Staff may have begun verification; never overwrite their status or fields.
        laporanService.perbaruiStatusLaporan(rid,{'narasiLaporan':text,'updatedAt':now()})
        shutil.rmtree(folder,ignore_errors=True)
        flash('Narasi laporan diperbarui.','success')
        return redirect(url_for('detail',rid=rid))
    @app.get('/report/<rid>')
    @protected()
    def detail(rid):return render_template('detail.html',report=accessible(rid),preview=False)
    @app.get('/api/reports/events')
    @protected()
    def events():
        from realtime import report_events
        response=Response(report_events(firebase,dict(g.user),session.get('firebase_session')),mimetype='text/event-stream')
        response.headers['X-Accel-Buffering']='no'
        return response
    @app.get('/api/report/<rid>/status')
    @protected()
    def report_status(rid):
        r=accessible(rid)
        return jsonify(status=r['status'],label=STATUS_EN.get(r['status'],r['status']) if session.get('lang')=='en' else r['status'],note=r.get('catatanPetugas',''))
    @app.get('/media/<rid>/<kind>/<angle>')
    @protected()
    def media(rid,kind,angle):
        if kind not in ('foto','deteksi') or angle not in (*ANGLES,'kiri','kanan','atas'):abort(404)
        if request.args.get('preview')=='1':r,folder=draft(rid)
        else:r=accessible(rid);folder=private/'reports'/rid
        source_kind='foto' if kind=='deteksi' else kind
        if request.args.get('preview')!='1' and r.get('storage')=='supabase':
            photos=store.photo_access(g.user['uid'],rid)
            data=io.BytesIO(photos.download(f'{source_kind}_{angle}.jpg'))
        elif request.args.get('preview')!='1' and r.get('storage')=='firebase':
            data=io.BytesIO(store.bucket.blob(f"laporan/{rid}/{source_kind}_{r.get('storageNames',{}).get(angle,angle)}.jpg").download_as_bytes())
        else:data=folder/f'{source_kind}_{angle}.jpg'
        if kind=='deteksi':
            # Redraw only existing detections on the already privacy-processed photo.
            # No inference, original unblurred file access, or report mutation.
            from PIL import Image
            photo=next((f for f in r['foto'] if f['angle']==angle),None)
            if photo is None:abort(404)
            with Image.open(data) as image:result=annotate(image.convert('RGB'),photo['boxes'])
            output=io.BytesIO();result.save(output,format='JPEG',quality=90);output.seek(0)
            return send_file(output,mimetype='image/jpeg')
        return send_file(data,mimetype='image/jpeg')
    @app.post('/report/<rid>/status')
    @protected('petugas')
    def change_status(rid):
        r=accessible(rid);status=request.form.get('status')
        if status not in STATUSES:abort(400)
        note=request.form.get('catatan','').strip()
        if len(note)>2000:abort(400,description='Catatan petugas maksimal 2.000 karakter.')
        values={'status':status,'catatanPetugas':note,'updatedAt':now(),'verifiedBy':g.user['uid']}
        for field in ('jumlahLubang','panjangCm','lebarCm','kedalamanCm','nilaiSDI'):
            raw=request.form.get(field,'').strip()
            if raw:
                try:
                    v=float(raw)
                    if not math.isfinite(v) or v<0 or (field=='jumlahLubang' and v!=int(v)):raise ValueError()
                except ValueError:abort(400,description='Pengukuran harus berupa angka nonnegatif; jumlah lubang berupa bilangan bulat.')
                values[field]=int(v) if field=='jumlahLubang' else v
            else:values[field]=None
        if status in ('Selesai','Ditolak') and not values['catatanPetugas'].strip():abort(400,description='Alasan penolakan wajib diisi.' if status=='Ditolak' else 'Catatan penyelesaian wajib diisi.')
        category=request.form.get('kategoriKerusakan','')
        if category not in ('',*CATEGORIES):abort(400,description='Kategori kerusakan tidak valid.')
        values['kategoriKerusakan']=(category or None) if 'kategoriKerusakan' in request.form else r.get('kategoriKerusakan')
        if category and values.get('nilaiSDI') is not None:
            n=values['nilaiSDI'];expected='Baik' if n<=50 else 'Sedang' if n<=100 else 'Rusak' if n<=150 else 'Rusak Berat'
            if category!=expected:abort(400,description='Kategori yang dipilih tidak sesuai nilai SDI hasil survei.')
        if 'kategoriKerusakan' in request.form:
            values['kategoriStandar']='SDI_Bina_Marga' if category else None
            values['kategoriSumber']='surveyor' if category else None
        if r.get('kategoriKerusakan') and r['kategoriKerusakan'] not in CATEGORIES:values['kategoriSebelumnya']=r['kategoriKerusakan']
        priority=request.form.get('prioritasPenanganan')
        if priority is not None:
            if len(priority)>500:abort(400,description='Prioritas penanganan maksimal 500 karakter.')
            values['prioritasPenanganan']=priority.strip() or None
        try:
            if 'dinas_form' in request.form:
                values['surveiDinas']=parse_survey(request.form,r.get('surveiDinas'))
                last=values['surveiDinas'].get('sdiBekasRoda')
                if last is not None and values.get('nilaiSDI') is not None and abs(last-values['nilaiSDI'])>1e-9:raise ValueError('SDI tahap bekas roda dan nilai SDI akhir harus sama.')
        except ValueError as e:abort(400,description=str(e))
        values['alasanPenolakan']=values['catatanPetugas'] if status=='Ditolak' else ''
        laporanService.perbaruiStatusLaporan(rid,values);flash('Status dan hasil pemeriksaan diperbarui.','success');return redirect(url_for('detail',rid=rid))
    @app.get('/reference/<name>')
    @protected('petugas')
    def dinas_reference(name):
        if name not in ('form_dinas.pdf','panduan_kerusakan.pdf'):abort(404)
        return send_file(BASE/'references'/name,mimetype='application/pdf',as_attachment=True)
    @app.get('/report/<rid>/form-dinas.pdf')
    @protected('petugas')
    def form_dinas(rid):
        from exports import build_export
        data,mime=build_export([accessible(rid)],'pdf-agency')
        return send_file(data,mimetype=mime,as_attachment=True,download_name='form_survei_'+rid+'.pdf')
    @app.route('/users',methods=['GET','POST'])
    @protected('petugas')
    def users():
        if request.method=='POST':
            try:
                action=request.form.get('action');uid=request.form.get('uid');role=request.form.get('role')
                if action=='create':
                    email,name,password=fields()
                    if role not in ('warga','petugas'):raise ValueError('Role tidak valid.')
                    authService.tambahAkun(email,password,name,role)
                else:
                    u=store.user(uid)
                    if not u:abort(404)
                    # No self-deletion/demotion; preserves at least the current administrator.
                    if uid==g.user['uid']:raise ValueError('Akun yang sedang digunakan tidak dapat diubah/dihapus di menu ini.')
                    if action=='delete':authService.hapusAkun(uid)
                    elif action=='update':
                        name=request.form.get('nama','').strip();email=request.form.get('email','').strip().lower();password=request.form.get('password','')
                        if not name or len(name)>100 or '@' not in email or len(email)>254 or role not in ('warga','petugas'):raise ValueError('Data akun tidak valid.')
                        if password and not 8<=len(password)<=128:raise ValueError('Password baru harus 8–128 karakter.')
                        authService.ubahAkun(uid,dict(nama=name,email=email,role=role,disabled=request.form.get('disabled')=='yes'),password or None)
                    else:abort(400)
                flash('Perubahan akun tersimpan.','success')
            except ValueError as e:flash(str(e),'error')
            except Exception:flash('Perubahan akun gagal. Periksa email dan konfigurasi layanan.','error')
            return redirect(url_for('users'))
        return render_template('users.html',users=authService.getSeluruhAkun())
    @app.get('/export/<fmt>')
    @protected('petugas')
    def export(fmt):
        from exports import build_export
        if fmt not in ('pdf','xlsx'):abort(404)
        data,mime=laporanService.eksporLaporan(filtered(),fmt)
        return send_file(data,mimetype=mime,as_attachment=True,download_name='laporan_jalan.'+fmt)
    controller.bind()
    return app

if __name__=='__main__':
    app=create_app();app.run(host='127.0.0.1',port=5000,debug=False)
