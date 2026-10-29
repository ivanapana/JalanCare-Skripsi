"""Reverse geocode only photo EXIF coordinates; cached, rate limited, no device GPS."""
import json,os,sqlite3,threading,time
import requests
_LOCK=threading.Lock();_LAST=0

def parse_address(data):
    address=data.get('address',{})
    if not isinstance(address,dict):address={}
    county=address.get('county') or address.get('regency') or address.get('state_district') or address.get('city') or ''
    # Keep administrative labels separate from settlements such as Tondano.
    region=county.replace('Kabupaten ','').replace('Kota ','').strip()
    locality=address.get('town') or address.get('city') or address.get('municipality') or address.get('village') or address.get('hamlet') or address.get('suburb') or ''
    district=address.get('city_district') or address.get('district') or address.get('subdistrict') or ''
    parts=list(dict.fromkeys(v for v in [address.get('road'),locality,district,county,address.get('state')] if v))
    return dict(alamatLokasi=', '.join(parts) or data.get('display_name',''),daerah=locality or district or county,kabupaten=region or 'Belum teridentifikasi',locationLookup='OpenStreetMap / Nominatim')

def reverse_location(latitude,longitude,cache_path):
    global _LAST
    endpoint=os.getenv('GEOCODER_URL','https://nominatim.openstreetmap.org/reverse')
    fallback=dict(alamatLokasi='',daerah='',kabupaten='Belum teridentifikasi',locationLookup='unavailable')
    key=f'v2:{latitude:.6f},{longitude:.6f}'
    with _LOCK:
        with sqlite3.connect(cache_path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS addresses (key TEXT PRIMARY KEY,data TEXT,created REAL)')
            row=db.execute('SELECT data FROM addresses WHERE key=? AND created>?',(key,time.time()-30*86400)).fetchone()
            if row:return json.loads(row[0])
        try:
            time.sleep(max(0,1.05-(time.monotonic()-_LAST)))
            _LAST=time.monotonic()
            response=requests.get(endpoint,params={'lat':latitude,'lon':longitude,'format':'jsonv2','addressdetails':1,'zoom':18,'accept-language':'id'},headers={'User-Agent':os.getenv('GEOCODER_USER_AGENT','JalanCareSkripsi/2.1 (provincial road reporting research)')},timeout=8)
            response.raise_for_status();data=response.json()
            if not isinstance(data,dict) or data.get('error'):return fallback
            result=parse_address(data)
            if not result['alamatLokasi']:return fallback
            with sqlite3.connect(cache_path) as db:db.execute('INSERT OR REPLACE INTO addresses VALUES (?,?,?)',(key,json.dumps(result),time.time()))
            return result
        except (requests.RequestException,ValueError,TypeError):return fallback
