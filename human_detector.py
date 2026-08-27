import cv2
import mediapipe as mp

class MediaPipeHumanDetector:
    def __init__(self):
        self.mp_face=mp.solutions.face_mesh; self.mp_pose=mp.solutions.pose; self.mp_hands=mp.solutions.hands; self.mp_draw=mp.solutions.drawing_utils
        self.face_mesh=self.mp_face.FaceMesh(max_num_faces=5,refine_landmarks=True,min_detection_confidence=.75,min_tracking_confidence=.75)
        self.pose=self.mp_pose.Pose(model_complexity=0,min_detection_confidence=.75,min_tracking_confidence=.75)
        self.hands=self.mp_hands.Hands(max_num_hands=2,min_detection_confidence=.75,min_tracking_confidence=.75)
    def detect(self,frame):
        rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB); fr=self.face_mesh.process(rgb); pr=self.pose.process(rgb); hr=self.hands.process(rgb)
        bbox=None; visible=0
        if pr.pose_landmarks:
            visible=sum(1 for lm in pr.pose_landmarks.landmark if lm.visibility>.45)
            if visible>=5:
                xs=[lm.x for lm in pr.pose_landmarks.landmark if lm.visibility>.45]; ys=[lm.y for lm in pr.pose_landmarks.landmark if lm.visibility>.45]
                if xs and ys: bbox=(max(0,int(min(xs)*frame.shape[1])),max(0,int(min(ys)*frame.shape[0])),min(frame.shape[1]-1,int(max(xs)*frame.shape[1])),min(frame.shape[0]-1,int(max(ys)*frame.shape[0])))
        face=bool(fr.multi_face_landmarks)
        if bbox is None and face:
            f=fr.multi_face_landmarks[0]; xs=[lm.x for lm in f.landmark]; ys=[lm.y for lm in f.landmark]
            bbox=(max(0,int(min(xs)*frame.shape[1])),max(0,int(min(ys)*frame.shape[0])),min(frame.shape[1]-1,int(max(xs)*frame.shape[1])),min(frame.shape[0]-1,int(max(ys)*frame.shape[0])))
        return {"detected":bbox is not None,"confidence":.92 if visible>=5 else (.86 if face else 0),"bbox":bbox,"face_results":fr,"pose_results":pr,"hand_results":hr}
    def draw(self,frame,r):
        fr,pr,hr=r["face_results"],r["pose_results"],r["hand_results"]
        if fr.multi_face_landmarks:
            for f in fr.multi_face_landmarks: self.mp_draw.draw_landmarks(frame,f,self.mp_face.FACEMESH_TESSELATION,None,self.mp_draw.DrawingSpec(color=(180,180,180),thickness=1))
        if pr.pose_landmarks: self.mp_draw.draw_landmarks(frame,pr.pose_landmarks,self.mp_pose.POSE_CONNECTIONS,self.mp_draw.DrawingSpec(color=(0,255,255),thickness=2),self.mp_draw.DrawingSpec(color=(255,0,0),thickness=2))
        if hr.multi_hand_landmarks:
            for h in hr.multi_hand_landmarks: self.mp_draw.draw_landmarks(frame,h,self.mp_hands.HAND_CONNECTIONS,self.mp_draw.DrawingSpec(color=(0,255,0),thickness=2),self.mp_draw.DrawingSpec(color=(0,0,255),thickness=2))
        if r["detected"] and r["bbox"]:
            x1,y1,x2,y2=r["bbox"]; cv2.rectangle(frame,(x1,y1),(x2,y2),(255,255,0),2); cv2.putText(frame,"Human",(x1,max(20,y1-8)),cv2.FONT_HERSHEY_SIMPLEX,.6,(255,255,0),2)
    def close(self): self.face_mesh.close(); self.pose.close(); self.hands.close()
