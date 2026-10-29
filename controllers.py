"""HTTP controller from classdiagram3. Route adapters retain Flask validation."""
class FlaskApp:
    def __init__(self,app,authService,laporanService):
        self.app=app;self.authService=authService;self.laporanService=laporanService;self.handlers={}
    def bind(self):
        routes={'register':'handleRegistrasi','login':'handleLogin','login_petugas':'handleLoginPetugas','logout':'handleLogout','analyze':'handleUnggahFoto','dashboard':'handleKelolaLaporanMasuk','detail':'handleDetailLaporan','change_status':'handlePerbaruiStatus','statistics':'handleRekapStatistik','export':'handleEksporLaporan','users':'handleKelolaAkun'}
        for endpoint,method in routes.items():
            self.handlers[endpoint]=self.app.view_functions[endpoint]
            self.app.view_functions[endpoint]=getattr(self,method)
    def handleRegistrasi(self):return self.handlers['register']()
    def handleLogin(self):return self.handlers['login']()
    def handleLoginPetugas(self):return self.handlers['login_petugas']()
    def handleLogout(self):return self.handlers['logout']()
    def handleUnggahFoto(self):return self.handlers['analyze']()
    def handleKelolaLaporanMasuk(self):return self.handlers['dashboard']()
    def handleDetailLaporan(self,rid):return self.handlers['detail'](rid)
    def handlePerbaruiStatus(self,rid):return self.handlers['change_status'](rid)
    def handleRekapStatistik(self):return self.handlers['statistics']()
    def handleEksporLaporan(self,fmt):return self.handlers['export'](fmt)
    def handleKelolaAkun(self):return self.handlers['users']()
