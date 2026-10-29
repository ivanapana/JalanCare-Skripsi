import io, json, math, threading
from PIL import Image, ImageOps, ImageFilter, UnidentifiedImageError
MODEL_LOCK=threading.Lock()
ANGLES=('foto1','foto2','foto3')

def gps(image):
    try:
        data=image.getexif().get_ifd(34853)
        def decimal(v):return float(v[0])+float(v[1])/60+float(v[2])/3600
        lat=decimal(data[2])*(-1 if data[1]=='S' else 1)
        lon=decimal(data[4])*(-1 if data[3]=='W' else 1)
        return lat,lon
    except (KeyError,TypeError,ValueError,ZeroDivisionError):return None

def read_photo(upload):
    data=upload.read(10*1024*1024+1)
    if len(data)>10*1024*1024:raise ValueError('Maksimal 10 MB untuk setiap foto.')
    try:
        img=Image.open(io.BytesIO(data))
        if img.format not in ('JPEG','PNG'):raise ValueError('Foto harus JPG/JPEG atau PNG.')
        if min(img.size)<640:raise ValueError('Lebar dan tinggi foto minimal 640 piksel.')
        if img.width*img.height>60_000_000:raise ValueError('Resolusi terlalu besar (maksimal 60 megapiksel).')
        location=gps(img);stamp=img.getexif().get(36867)
        img.load();img=ImageOps.exif_transpose(img).convert('RGB')
        return img,location,stamp
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError) as e:raise ValueError('Foto tidak valid atau tidak dapat dibaca.') from e

def blur_private(image,regions,auto_faces=False):
    """Blur selected regions only by default; experimental face blur is opt-in."""
    all_regions=list(regions)
    if auto_faces:
        import cv2, numpy as np
        gray=cv2.cvtColor(np.array(image),cv2.COLOR_RGB2GRAY)
        scale=min(1,1000/image.width);small=cv2.resize(gray,None,fx=scale,fy=scale)
        cascade=cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml')
        faces=cascade.detectMultiScale(small,scaleFactor=1.1,minNeighbors=5,minSize=(24,24))
        all_regions.extend([[x/scale/image.width,y/scale/image.height,w/scale/image.width,h/scale/image.height] for x,y,w,h in faces])
    result=image.copy()
    for x,y,w,h in all_regions:
        if not all(math.isfinite(v) for v in (x,y,w,h)) or w<=0 or h<=0 or min(x,y)<0 or x+w>1.001 or y+h>1.001:raise ValueError('Area blur tidak valid.')
        box=(int(x*image.width),int(y*image.height),min(image.width,int((x+w)*image.width)),min(image.height,int((y+h)*image.height)))
        if box[2]<=box[0] or box[3]<=box[1]:continue
        import cv2,numpy as np
        array=np.asarray(result.crop(box))
        crop=Image.fromarray(cv2.GaussianBlur(array,(0,0),sigmaX=max(18,min(box[2]-box[0],box[3]-box[1])/8)))
        result.paste(crop,box)
    return result,len(all_regions)

class Detector:
    def __init__(self,path,confidence):self.path=path;self.confidence=confidence;self.model=None
    def predict(self,image):
        with MODEL_LOCK:
            if self.model is None:
                if not self.path.is_file():raise ValueError('Model belum ada. Salin best_potholes.pt ke folder models.')
                from ultralytics import YOLO
                self.model=YOLO(str(self.path))
            prediction=self.model.predict(image,imgsz=640,conf=self.confidence,verbose=False)[0]
            boxes=[{'confidence':round(float(b.conf[0]),4),'xyxy':[round(float(x),2) for x in b.xyxy[0].tolist()]} for b in prediction.boxes if int(b.cls[0])==0]
            return boxes

def annotate(image,boxes):
    from PIL import ImageDraw,ImageFont
    size=max(20,round(max(image.size)/32))
    font=ImageFont.load_default(size=size)
    out=image.copy();d=ImageDraw.Draw(out);line=max(3,round(max(image.size)/220));pad=max(5,size//5)
    occupied=[]
    for index,b in enumerate(boxes,1):
        d.rectangle(b['xyxy'],outline='#1764dc',width=line)
        label=f"#{index} Pothole {b['confidence']:.2f}"
        bounds=d.textbbox((0,0),label,font=font);w=bounds[2]-bounds[0]+2*pad;h=bounds[3]-bounds[1]+2*pad
        x=max(0,min(round(b['xyxy'][0]),image.width-w));y=max(0,min(round(b['xyxy'][1])-h,image.height-h))
        for _ in boxes:
            if not any(x<ox+ow and x+w>ox and y<oy+oh and y+h>oy for ox,oy,ow,oh in occupied):break
            y=min(image.height-h,y+h+pad)
        occupied.append((x,y,w,h));d.rectangle((x,y,x+w,y+h),fill='#1457b9')
        d.text((x+pad,y+pad-bounds[1]),label,fill='white',font=font)
    return out
