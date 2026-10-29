"""Firestore watch -> authenticated SSE. Local demo polls SQLite, not Firestore."""
import json,queue,time
from google.cloud.firestore_v1.base_query import FieldFilter

def report_events(firebase,user,token=None,duration=120):
    backend=firebase.backend;watch=None;events=queue.Queue(maxsize=1)
    def visible(rows):return [r for r in rows if user['role']=='petugas' or r.get('idPengguna')==user['uid']]
    def event(rows):
        # Return only report status metadata within this user's authorization scope.
        return 'event: reports\ndata: '+json.dumps([dict(id=r['idLaporan'],status=r['status'],note=r.get('catatanPetugas',''),updatedAt=str(r.get('updatedAt',''))) for r in visible(rows)],ensure_ascii=False)+'\n\n'
    def callback(snapshots,changes,read_time):
        rows=[backend.normalize(s.to_dict()) for s in snapshots]
        try:events.put_nowait(rows)
        except queue.Full:
            try:events.get_nowait()
            except queue.Empty:pass
            try:events.put_nowait(rows)
            except queue.Full:pass
    try:
        if hasattr(backend,'db'):
            query=backend.db.collection('laporan')
            if user['role']!='petugas':query=query.where(filter=FieldFilter('idPengguna','==',backend.db.collection('pengguna').document(user['uid'])))
            watch=query.on_snapshot(callback)
        previous=None;deadline=time.monotonic()+duration
        while time.monotonic()<deadline:
            account=firebase.user(user['uid'])
            if not account or account.get('disabled') or account.get('role')!=user['role']:return
            if token:
                try:firebase.verify(token)
                except Exception:return
            if watch:
                try:rows=events.get(timeout=15)
                except queue.Empty:
                    yield ': heartbeat\n\n';continue
            else:rows=firebase.queryLaporan()
            message=event(rows)
            if message!=previous:yield message;previous=message
            elif not watch:yield ': heartbeat\n\n'
            if not watch:time.sleep(1)
    finally:
        if watch:watch.unsubscribe()
