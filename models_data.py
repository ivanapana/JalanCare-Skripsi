"""Domain records from classdiagram3; legacy keys remain readable."""
from dataclasses import dataclass,field

@dataclass
class Pengguna:
    uid:str
    nama:str
    email:str
    role:str
    createdAt:object=None
    extra:dict=field(default_factory=dict)
    @classmethod
    def fromDict(cls,data):
        keys=('uid','nama','email','role','createdAt')
        return cls(**{k:data.get(k) for k in keys},extra={k:v for k,v in data.items() if k not in keys})
    def toDict(self):return dict(self.extra,uid=self.uid,nama=self.nama,email=self.email,role=self.role,createdAt=self.createdAt)

@dataclass
class Laporan:
    laporanId: str=None
    wargaId: str=None
    citraKiri: str=None
    citraKanan: str=None
    citraAtas: str=None
    koordinatLat: float=None
    koordinatLng: float=None
    boundingBox: list=field(default_factory=list)
    confidenceScore: float=None
    narasiLaporan: str=''
    kategoriKerusakan: str=None
    status: str='Menunggu Verifikasi'
    waktuDibuat: object=None
    waktuDiperbarui: object=None
    extra: dict=field(default_factory=dict)
    PAIRS={'laporanId':'idLaporan','wargaId':'idPengguna','koordinatLat':'latitude','koordinatLng':'longitude','waktuDibuat':'timestamp','waktuDiperbarui':'updatedAt','boundingBox':'boundingBoxes'}
    @classmethod
    def fromDict(cls,data):
        names=tuple(k for k in cls.__dataclass_fields__ if k!='extra');values={}
        for k in names:
            old=cls.PAIRS.get(k,k)
            if old in data:values[k]=data[old]
            elif k in data:values[k]=data[k]
        return cls(**values,extra={k:v for k,v in data.items() if k not in names})
    def toDict(self):
        r=dict(self.extra)
        for name in self.__dataclass_fields__:
            if name!='extra':r[name]=getattr(self,name)
        for diagram,legacy in self.PAIRS.items():r[legacy]=r[diagram]
        if r.get('confidenceScores'):r['confidenceScore']=max(r['confidenceScores'])
        urls=r.get('citraUrls',[])
        for i,key in enumerate(('citraKiri','citraKanan','citraAtas')):
            if len(urls)>i:r[key]=urls[i]
        return r
