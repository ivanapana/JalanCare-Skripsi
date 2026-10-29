"""Agency survey schema. Blank is unknown, never code 1 (absence)."""
import math,re
from datetime import date
AREA=('Tidak ada','<10% luas','10–30% luas','>30% luas')
GROUPS=[
 ('Permukaan Perkerasan','Pavement surface',[
 ('susunan','Susunan','Texture',('Baik/Rapat','Kasar')),
 ('kondisi','Kondisi/Keadaan','Condition',('Baik/tidak ada kelainan','Aspal berlebihan','Lepas-lepas','Hancur')),
 ('penurunan','% Penurunan','Depressed area',AREA),('tambalan','% Tambalan','Patched area',AREA)]),
 ('Retak-retak','Cracks',[
 ('retakJenis','Jenis','Type',('Tidak ada','Tidak berhubungan','Saling berhubungan (berbidang luas)','Saling berhubungan (berbidang sempit)')),
 ('retakLebar','Lebar','Width',('Tidak ada','Halus <1 mm','Sedang 1–5 mm','Lebar >5 mm')),
 ('retakLuas','% Luas','Affected area',AREA)]),
 ('Kerusakan Lain','Other damage',[
 ('jumlahKode','Jumlah lubang / 200 m','Potholes / 200 m',('Tidak ada','1–2 / 200 meter','3–9 / 200 meter','≥10 / 200 meter')),
 ('ukuranKode','Ukuran lubang','Pothole size',('Tidak ada','Kecil-dangkal','Kecil-dalam','Besar-dangkal','Besar-dalam')),
 ('bekasRoda','Bekas roda','Rutting',('Tidak ada','<1 cm dalam','1–3 cm dalam','>3 cm dalam')),
 ('tepiKiri','Kerusakan tepi kiri','Left edge damage',('Tidak ada','Ringan','Berat')),
 ('tepiKanan','Kerusakan tepi kanan','Right edge damage',('Tidak ada','Ringan','Berat'))]),
 ('Bahu, Saluran Samping dan Lain-lain','Shoulders, drains and other features',[
 (bagian+side,f'{label} {indo}',f'{english} {en}',opts) for label,english,bagian,opts in [
 ('Kondisi bahu','Shoulder condition','Bahu',('Tidak ada','Baik/Rata','Bekas roda/Erosi ringan','Bekas roda/Erosi berat')),
 ('Permukaan bahu','Shoulder surface','Permukaan',('Tidak ada','Di atas permukaan jalan','Rata dengan permukaan jalan','Di bawah permukaan jalan','>10 cm di bawah permukaan jalan')),
 ('Kondisi saluran','Drain condition','Saluran',('Tidak ada','Bersih','Tertutup/Tersumbat','Erosi')),
 ('Kerusakan lereng','Slope damage','Lereng',('Tidak ada','Longsor/Runtuh')),
 ('Trotoar','Sidewalk','Trotoar',('Tidak ada','Baik/Aman','Berbahaya'))
 ] for side,indo,en in [('Kiri','kiri','Left'),('Kanan','kanan','Right')]])]
FIELDS=[f for _,_,fields in GROUPS for f in fields]
META=[('nomorRuas','Nomor ruas','Route number'),('namaRuas','Nama ruas','Route name'),('statusFungsi','Status/fungsi N/P/M/K','Road status N/P/M/K'),('aksesKeJalan','Akses ke jalan N/P/K (opsional)','Access road N/P/K (optional)'),('staAwal','STA awal (contoh 0+000)','Start chainage (e.g. 0+000)'),('staAkhir','STA akhir (contoh 0+200)','End chainage (e.g. 0+200)'),('tanggalSurvei','Tanggal survei','Survey date'),('surveyor','Nama surveyor','Surveyor name'),('kodeKondisi','Kode kondisi dinas (opsional)','Agency condition code (optional)')]
NUMBERS=[('panjangRuasKm','Panjang seluruh ruas (km)','Full route length (km)'),('lebarRuasM','Lebar ruas (m)','Road width (m)'),('jumlahLubangSegmen','Jumlah lubang unik dalam segmen 200 m','Unique potholes in the 200 m segment'),('diameterCm','Diameter lubang yang diukur (cm)','Measured pothole diameter (cm)'),('sdiRetakLuas','SDI tahap retak luas (surveyor)','SDI after crack area (surveyor)'),('sdiRetakLebar','SDI tahap retak lebar (surveyor)','SDI after crack width (surveyor)'),('sdiLubang','SDI tahap jumlah lubang (surveyor)','SDI after potholes (surveyor)'),('sdiBekasRoda','SDI tahap bekas roda (surveyor)','SDI after rutting (surveyor)')]
EN_OPTIONS={'Tidak ada':'None','Baik/Rapat':'Good/dense','Kasar':'Rough','Baik/tidak ada kelainan':'Good/no abnormality','Aspal berlebihan':'Excess asphalt','Lepas-lepas':'Loose material','Hancur':'Disintegrated','<10% luas':'<10% area','10–30% luas':'10–30% area','>30% luas':'>30% area','Tidak berhubungan':'Unconnected','Saling berhubungan (berbidang luas)':'Connected (large areas)','Saling berhubungan (berbidang sempit)':'Connected (small areas)','Halus <1 mm':'Fine <1 mm','Sedang 1–5 mm':'Medium 1–5 mm','Lebar >5 mm':'Wide >5 mm','1–2 / 200 meter':'1–2 / 200 metres','3–9 / 200 meter':'3–9 / 200 metres','≥10 / 200 meter':'≥10 / 200 metres','Kecil-dangkal':'Small/shallow','Kecil-dalam':'Small/deep','Besar-dangkal':'Large/shallow','Besar-dalam':'Large/deep','<1 cm dalam':'<1 cm deep','1–3 cm dalam':'1–3 cm deep','>3 cm dalam':'>3 cm deep','Ringan':'Minor','Berat':'Severe','Baik/Rata':'Good/level','Bekas roda/Erosi ringan':'Minor rutting/erosion','Bekas roda/Erosi berat':'Severe rutting/erosion','Di atas permukaan jalan':'Above road surface','Rata dengan permukaan jalan':'Level with road surface','Di bawah permukaan jalan':'Below road surface','>10 cm di bawah permukaan jalan':'>10 cm below road surface','Bersih':'Clear','Tertutup/Tersumbat':'Covered/blocked','Erosi':'Erosion','Longsor/Runtuh':'Landslide/collapse','Baik/Aman':'Good/safe','Berbahaya':'Hazardous'}
def category_display(value):return 'Rusak Ringan' if value=='Rusak' else value

def sta_m(value):
    match=re.fullmatch(r'(\d{1,5})\+(\d{3})',value or '')
    if not match:raise ValueError('STA harus memakai format km+meter, misalnya 0+000.')
    return int(match[1])*1000+int(match[2])

def hole_class(diameter,depth):
    if diameter is None or depth is None:return None
    return ('Kecil' if diameter<50 else 'Besar')+'-'+('dangkal' if depth<5 else 'dalam')

def parse_survey(form,previous):
    if 'dinas_form' not in form:return previous
    data={}
    for key,label,_ in META:
        value=form.get('dinas_'+key,'').strip()
        if len(value)>150:raise ValueError(label+' maksimal 150 karakter.')
        data[key]=value or None
    if data['statusFungsi'] and data['statusFungsi'] not in ('N','P','M','K'):raise ValueError('Status/fungsi ruas harus N, P, M, atau K.')
    if data['aksesKeJalan'] and data['aksesKeJalan'] not in ('N','P','K'):raise ValueError('Akses ke jalan harus N, P, atau K.')
    if data['tanggalSurvei']:
        try:date.fromisoformat(data['tanggalSurvei'])
        except ValueError:raise ValueError('Tanggal survei tidak valid.')
    for key,label,_ in NUMBERS:
        raw=form.get('dinas_'+key,'').strip();data[key]=None
        if raw:
            try:
                value=float(raw)
                if not math.isfinite(value) or value<0 or (key=='jumlahLubangSegmen' and not value.is_integer()):raise ValueError()
                if key in ('panjangRuasKm','lebarRuasM') and value==0:raise ValueError()
            except ValueError:raise ValueError(label+' harus berupa angka yang valid dan nonnegatif; panjang/lebar ruas harus positif.')
            data[key]=int(value) if key=='jumlahLubangSegmen' else value
    for key,label,_,options in FIELDS:
        raw=form.get('dinas_'+key,'');data[key]=None
        if raw:
            if raw not in [str(n) for n in range(1,len(options)+1)]:raise ValueError('Kode '+label+' tidak valid.')
            data[key]=int(raw)
    for key in ('staAwal','staAkhir'):
        if data[key]:sta_m(data[key])
    if bool(data['staAwal'])!=bool(data['staAkhir']):raise ValueError('Isi STA awal dan akhir bersama-sama.')
    if data['staAwal']:
        start,end=sta_m(data['staAwal']),sta_m(data['staAkhir'])
        if end-start!=200:raise ValueError('Formulir ini memakai segmen survei 200 meter; STA akhir harus 200 meter setelah STA awal.')
        if data['panjangRuasKm'] is not None and end>data['panjangRuasKm']*1000:raise ValueError('STA akhir melebihi panjang seluruh ruas.')
    if data['jumlahLubangSegmen'] is not None:
        if not data['staAwal']:raise ValueError('Jumlah lubang per segmen memerlukan STA awal dan akhir 200 meter.')
        n=data['jumlahLubangSegmen'];expected=1 if n==0 else 2 if n<=2 else 3 if n<=9 else 4
        if data['jumlahKode'] and data['jumlahKode']!=expected:raise ValueError('Kode jumlah lubang tidak sesuai jumlah hasil survei segmen 200 meter.')
        data['jumlahKode']=expected
        if n==0 and data['ukuranKode'] not in (None,1):raise ValueError('Segmen tanpa lubang tidak dapat memiliki kode ukuran lubang.')
        if n>0 and data['ukuranKode']==1:raise ValueError('Segmen dengan lubang tidak dapat memakai ukuran Tidak ada.')
    data['standar']='Form PUPRD Sulut - jalan aspal';return data

def survey_lines(report):
    d=report.get('surveiDinas') or {};waiting='Belum disurvei'
    lines=['FORMULIR SURVEI KONDISI JALAN ASPAL (DRAF DIGITAL)','Provinsi: Sulawesi Utara; nomor provinsi: 50']
    for key,label,_ in META:lines.append(label+': '+str(d.get(key) or waiting))
    for title,_,fields in GROUPS:
        lines.append(title.upper())
        for key,label,_,opts in fields:
            code=d.get(key);lines.append(label+': '+(str(code)+' - '+opts[code-1] if isinstance(code,int) and 1<=code<=len(opts) else waiting))
    lines.extend(['Nilai SDI: '+str(report.get('nilaiSDI') if report.get('nilaiSDI') is not None else waiting),'Kondisi ruas: '+str(category_display(report.get('kategoriKerusakan')) or waiting)])
    return lines
