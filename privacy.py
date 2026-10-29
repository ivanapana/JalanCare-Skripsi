"""Automatic face/plate detection on-device, independent of the pothole model."""
import threading
from pathlib import Path
import cv2,numpy as np

class PrivacyDetector:
    def __init__(self,model_dir):
        self.model_dir=Path(model_dir);self.face=None;self.plate=None;self.lock=threading.Lock()
    def _load(self):
        face=self.model_dir/'face_yunet.onnx';plate=self.model_dir/'plate_yolov8n.onnx'
        if not face.is_file() or not plate.is_file():raise ValueError('Model privasi belum lengkap. Salin folder models/privacy dari paket terbaru; laporan tidak disimpan.')
        if self.face is None:self.face=cv2.FaceDetectorYN.create(str(face),'',(320,320),.85,.3,5000)
        if self.plate is None:self.plate=cv2.dnn.readNetFromONNX(str(plate))
    @staticmethod
    def region(x1,y1,x2,y2,width,height,kind):
        x1,y1,x2,y2=map(float,(x1,y1,x2,y2))
        pad=max(3,(x2-x1)*.08);pad_y=max(3,(y2-y1)*.08)
        x1=max(0,x1-pad);y1=max(0,y1-pad_y);x2=min(width,x2+pad);y2=min(height,y2+pad_y)
        if x2-x1<2 or y2-y1<2:return None
        return dict(kind=kind,region=[x1/width,y1/height,(x2-x1)/width,(y2-y1)/height])
    def detect(self,image):
        with self.lock:
            try:
                self._load();bgr=cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR);height,width=bgr.shape[:2];found=[]
                scale=min(1,1600/max(width,height));small=cv2.resize(bgr,(max(1,round(width*scale)),max(1,round(height*scale))))
                self.face.setInputSize((small.shape[1],small.shape[0]));_,faces=self.face.detect(small)
                if faces is not None:
                    for face in faces:
                        x,y,w,h=face[:4]/scale;item=self.region(x,y,x+w,y+h,width,height,'face')
                        if item:found.append(item)
                # Ultralytics letterbox, single-class YOLOv8 export: [1,5,8400].
                scale=min(640/width,640/height);rw,rh=round(width*scale),round(height*scale)
                left,top=(640-rw)//2,(640-rh)//2
                canvas=np.full((640,640,3),114,dtype=np.uint8);canvas[top:top+rh,left:left+rw]=cv2.resize(bgr,(rw,rh))
                self.plate.setInput(cv2.dnn.blobFromImage(canvas,1/255,(640,640),swapRB=True,crop=False))
                prediction=np.squeeze(self.plate.forward())
                if prediction.ndim!=2:raise ValueError('Unsupported plate output')
                if prediction.shape[0]==5:prediction=prediction.T
                if prediction.shape[1]!=5:raise ValueError('Unsupported plate model shape')
                boxes=[];scores=[]
                for cx,cy,w,h,score in prediction:
                    if not np.isfinite([cx,cy,w,h,score]).all() or score<.3 or w<=0 or h<=0:continue
                    x,y=(cx-w/2-left)/scale,(cy-h/2-top)/scale
                    boxes.append([float(x),float(y),float(w/scale),float(h/scale)]);scores.append(float(score))
                indices=cv2.dnn.NMSBoxes(boxes,scores,.3,.45)
                for index in np.asarray(indices).reshape(-1):
                    x,y,w,h=boxes[int(index)];item=self.region(x,y,x+w,y+h,width,height,'plate')
                    if item:found.append(item)
                return found
            except ValueError:raise
            except Exception as e:raise ValueError('Pemeriksaan privasi otomatis gagal. Laporan tidak disimpan. Periksa model privasi dan coba lagi.') from e
