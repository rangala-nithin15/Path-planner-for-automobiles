from ultralytics import YOLO
import cv2
import torch
from config import MODEL_PATH, YOLO_CONFIDENCE, YOLO_IOU, YOLO_IMGSZ

VEHICLE_CLASSES={2:"Car",3:"Motorcycle",5:"Bus",7:"Truck"}
ANIMAL_CLASSES={15:"Cat",16:"Dog",17:"Horse",18:"Sheep",19:"Cow",20:"Elephant",21:"Bear",22:"Zebra",23:"Giraffe"}

class RoadObjectDetector:
    def __init__(self):
        self.model=YOLO(MODEL_PATH)
        self.device=0 if torch.cuda.is_available() else "cpu"
    def detect(self, frame):
        detections=[]
        try:
            results=self.model.track(frame,persist=True,conf=YOLO_CONFIDENCE,iou=YOLO_IOU,imgsz=YOLO_IMGSZ,device=self.device,verbose=False)
        except Exception as e:
            print("YOLO error:",e); return detections
        if not results or results[0].boxes is None: return detections
        r=results[0]; boxes=r.boxes.xyxy.cpu().numpy(); classes=r.boxes.cls.cpu().numpy(); confs=r.boxes.conf.cpu().numpy()
        ids=r.boxes.id.cpu().numpy() if r.boxes.id is not None else None
        for i,(box,cls,conf) in enumerate(zip(boxes,classes,confs)):
            cls=int(cls)
            if cls in VEHICLE_CLASSES: label,cat=VEHICLE_CLASSES[cls],"vehicle"
            elif cls in ANIMAL_CLASSES: label,cat=ANIMAL_CLASSES[cls],"animal"
            else: continue
            x1,y1,x2,y2=map(int,box)
            if x2<=x1 or y2<=y1: continue
            detections.append({"label":label,"category":cat,"bbox":(x1,y1,x2,y2),"confidence":float(conf),"source":"yolo","track_id":int(ids[i]) if ids is not None and i<len(ids) else None})
        return detections
    def draw(self,frame,detections):
        for o in detections:
            b=o.get("bbox")
            if not b: continue
            x1,y1,x2,y2=b
            cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)
            cv2.putText(frame,f'{o["label"]} {o["confidence"]:.2f}',(x1,max(20,y1-8)),cv2.FONT_HERSHEY_SIMPLEX,.55,(0,255,0),2)
