"""Local demo and Firebase adapters; authorization remains in app.py."""
import json, sqlite3, uuid, math
from datetime import datetime, timezone
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

ACTIVE = ('Menunggu Verifikasi', 'Sedang Ditangani')
def now(): return datetime.now(timezone.utc).isoformat()
def distance(a,b,c,d):
    p,q=math.radians(a),math.radians(c)
    h=math.sin((q-p)/2)**2+math.cos(p)*math.cos(q)*math.sin(math.radians(d-b)/2)**2
    return 6371000*2*math.asin(min(1,math.sqrt(h)))
def duplicate(rows, report):
    return next((r for r in rows if r['status'] in ACTIVE and distance(report['latitude'],report['longitude'],r['latitude'],r['longitude'])<30),None)
class DuplicateError(Exception): pass

class LocalStore:
    def __init__(self,path):
        self.path=str(path)
        with self.conn() as c:
            c.execute('CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email TEXT UNIQUE, data TEXT)')
            c.execute('CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, data TEXT)')
    def conn(self): return sqlite3.connect(self.path, timeout=30)
    def users(self):
        with self.conn() as c: return [json.loads(r[0]) for r in c.execute('SELECT data FROM users')]
    def user(self,uid): return next((u for u in self.users() if u['uid']==uid),None)
    def create_user(self,email,password,name,role='warga'):
        u=dict(uid=uuid.uuid4().hex,email=email.lower(),nama=name,role=role,createdAt=now(),disabled=False,password=generate_password_hash(password))
        with self.conn() as c:c.execute('INSERT INTO users VALUES (?,?,?)',(u['uid'],u['email'],json.dumps(u)))
        return u
    def login(self,email,password):
        u=next((u for u in self.users() if u['email']==email.lower()),None)
        if not u or u.get('disabled') or not check_password_hash(u['password'],password): raise ValueError('Email atau password tidak sesuai.')
        return u, None
    def change_user(self,uid,values,password=None):
        u=self.user(uid);u.update(values)
        if password:u['password']=generate_password_hash(password)
        with self.conn() as c:c.execute('UPDATE users SET email=?,data=? WHERE id=?',(u['email'],json.dumps(u),uid))
    def delete_user(self,uid):
        with self.conn() as c:c.execute('DELETE FROM users WHERE id=?',(uid,))
    def reports(self):
        with self.conn() as c:return sorted([json.loads(r[0]) for r in c.execute('SELECT data FROM reports')],key=lambda r:r['timestamp'],reverse=True)
    def report(self,rid):return next((r for r in self.reports() if r['idLaporan']==rid),None)
    def save_report(self,r):
        with self.conn() as c:
            c.execute('BEGIN IMMEDIATE')
            rows=[json.loads(x[0]) for x in c.execute('SELECT data FROM reports')]
            if duplicate(rows,r):raise DuplicateError('Ada laporan aktif dalam radius 30 meter. Laporan baru tidak dikirim.')
            c.execute('INSERT INTO reports VALUES (?,?)',(r['idLaporan'],json.dumps(r)))
    def update_report(self,rid,values):
        with self.conn() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT data FROM reports WHERE id=?',(rid,)).fetchone()
            if not row:raise ValueError('Laporan tidak ditemukan.')
            r=json.loads(row[0]);r.update(values)
            c.execute('UPDATE reports SET data=? WHERE id=?',(json.dumps(r),rid))

class FirebaseStore:
    def __init__(self,credential,bucket,api_key,photo_storage=None):
        import firebase_admin
        from firebase_admin import credentials, firestore, auth, storage
        self.auth=auth;self.fs=firestore;self.api_key=api_key
        self.app=firebase_admin.initialize_app(credentials.Certificate(credential), {'storageBucket':bucket} if bucket else {})
        self.db=firestore.client(self.app)
        self.bucket=storage.bucket(app=self.app) if bucket else None
        self.photo_storage=photo_storage
    def photo_access(self,uid,report_id,write=False):
        """Issue a server-only, report-scoped Firebase ID token for Storage.

        Callers supply the UID from the verified website session. Firestore is
        still authoritative for roles; no persistent custom claims are changed.
        The login cookie/password flow is untouched. Both existing and new
        users receive role=authenticated on these storage-only ID tokens.
        """
        import re,requests
        from photo_storage import PhotoStorageError
        if not self.photo_storage:raise PhotoStorageError('Supabase Storage belum dikonfigurasi.')
        if not isinstance(report_id,str) or not re.fullmatch(r'[a-f0-9]{32}',report_id):raise PhotoStorageError('ID laporan tidak valid.')
        user=self.user(uid)
        if not user or user.get('disabled') or user.get('role') not in ('warga','petugas'):
            raise PhotoStorageError('Profil pengguna belum aktif. Hubungi pengelola.')
        account=self.auth.get_user(uid,app=self.app)
        if account.disabled:raise PhotoStorageError('Profil pengguna belum aktif. Hubungi pengelola.')
        report=self.report(report_id)
        if write:
            if user['role']!='warga' or report is not None:raise PhotoStorageError('Upload foto untuk laporan ini tidak diizinkan.')
            owner=uid
        else:
            if not report or (user['role']!='petugas' and report['idPengguna']!=uid):
                raise PhotoStorageError('Anda tidak memiliki akses ke foto laporan ini.')
            owner=report['idPengguna']
        claims={'role':'authenticated','jalancare_report':report_id,
                'jalancare_action':'upload' if write else 'read',
                'jalancare_staff':user['role']=='petugas'}
        try:
            custom=self.auth.create_custom_token(uid,developer_claims=claims,app=self.app)
            if isinstance(custom,bytes):custom=custom.decode('utf8')
            response=requests.post('https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken',
                params={'key':self.api_key},json={'token':custom,'returnSecureToken':True},
                timeout=(10,20),allow_redirects=False)
            if not response.ok:raise PhotoStorageError('Token akses foto Firebase belum berhasil dibuat. Periksa konfigurasi Firebase.')
            # Discard the returned refresh token; nothing is sent to the browser.
            token=response.json()['idToken']
            verified=self.auth.verify_id_token(token,check_revoked=True,app=self.app)
            if verified.get('uid')!=uid or any(verified.get(k)!=v for k,v in claims.items()):
                raise PhotoStorageError('Token akses foto Firebase tidak sesuai.')
        except (requests.RequestException,KeyError,TypeError,ValueError):
            raise PhotoStorageError('Token akses foto Firebase belum berhasil dibuat. Periksa konfigurasi Firebase.') from None
        return self.photo_storage.scoped(token,owner,report_id)
    def users(self):return [s.to_dict() for s in self.db.collection('pengguna').stream()]
    def user(self,uid):
        s=self.db.collection('pengguna').document(uid).get();return s.to_dict() if s.exists else None
    def create_user(self,email,password,name,role='warga'):
        user=self.auth.create_user(email=email,password=password,display_name=name,app=self.app)
        u=dict(uid=user.uid,email=email.lower(),nama=name,role=role,createdAt=datetime.now(timezone.utc),disabled=False)
        try:self.db.collection('pengguna').document(user.uid).set(u)
        except Exception:
            self.auth.delete_user(user.uid,app=self.app);raise
        return u
    def login(self,email,password):
        import requests
        resp=requests.post('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword',params={'key':self.api_key},json={'email':email,'password':password,'returnSecureToken':True},timeout=20)
        if not resp.ok:raise ValueError('Email atau password tidak sesuai, atau login Firebase belum diaktifkan.')
        from datetime import timedelta
        token=self.auth.create_session_cookie(resp.json()['idToken'],expires_in=timedelta(hours=8),app=self.app)
        uid=self.auth.verify_session_cookie(token,check_revoked=True,app=self.app)['uid']
        u=self.user(uid)
        if not u or u.get('disabled'):raise ValueError('Profil pengguna belum aktif. Hubungi pengelola.')
        return u,token
    def verify(self,token):return self.auth.verify_session_cookie(token,check_revoked=True,app=self.app)['uid']
    def change_user(self,uid,values,password=None):
        args=dict(email=values['email'],display_name=values['nama'],disabled=values.get('disabled',False))
        if password:args['password']=password
        self.auth.update_user(uid,app=self.app,**args)
        self.db.collection('pengguna').document(uid).update(values)
        self.auth.revoke_refresh_tokens(uid,app=self.app)
    def delete_user(self,uid):
        self.auth.delete_user(uid,app=self.app);self.db.collection('pengguna').document(uid).delete()
    def normalize(self,r):
        if hasattr(r.get('idPengguna'),'id'):r['idPengguna']=r['idPengguna'].id
        for k in ('timestamp','createdAt','updatedAt','waktuDibuat','waktuDiperbarui'):
            if hasattr(r.get(k),'isoformat'):r[k]=r[k].isoformat()
        return r
    def reports(self):return sorted([self.normalize(s.to_dict()) for s in self.db.collection('laporan').stream()],key=lambda r:r['timestamp'],reverse=True)
    def report(self,rid):
        s=self.db.collection('laporan').document(rid).get();return self.normalize(s.to_dict()) if s.exists else None
    def save_report(self,r):
        from google.cloud.firestore_v1.base_query import FieldFilter
        lock=self.db.collection('_locks').document('report_submission')
        ref=self.db.collection('laporan').document(r['idLaporan'])
        @self.fs.transactional
        def commit(tx):
            lock.get(transaction=tx)
            delta=30/111000
            query=self.db.collection('laporan').where(filter=FieldFilter('latitude','>=',r['latitude']-delta)).where(filter=FieldFilter('latitude','<=',r['latitude']+delta))
            rows=[self.normalize(s.to_dict()) for s in query.stream(transaction=tx)]
            if duplicate(rows,r):raise DuplicateError('Ada laporan aktif dalam radius 30 meter. Laporan baru tidak dikirim.')
            value=dict(r);value['idPengguna']=self.db.collection('pengguna').document(r['idPengguna'])
            value['timestamp']=datetime.fromisoformat(r['timestamp'])
            value['waktuDibuat']=value['timestamp']
            for key in ('updatedAt','waktuDiperbarui'):
                if isinstance(value.get(key),str):value[key]=datetime.fromisoformat(value[key])
            tx.set(lock,{'updatedAt':self.fs.SERVER_TIMESTAMP});tx.create(ref,value)
        commit(self.db.transaction())
    def update_report(self,rid,values):
        data=dict(values)
        for key in ('updatedAt','waktuDiperbarui'):
            if isinstance(data.get(key),str):data[key]=datetime.fromisoformat(data[key])
        self.db.collection('laporan').document(rid).update(data)
