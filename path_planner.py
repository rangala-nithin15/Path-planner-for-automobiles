from config import CENTER_ZONE_RATIO,NEAR_OBJECT_AREA_RATIO,HIGH_RISK_AREA_RATIO
class PathPlanner:
    def analyze(self,objects,frame_width,frame_height):
        valid=[o for o in objects if isinstance(o,dict) and o.get("bbox") and len(o["bbox"])==4]
        risk="clear"; msg="Road appears clear."; cl=frame_width*(.5-CENTER_ZONE_RATIO/2); cr=frame_width*(.5+CENTER_ZONE_RATIO/2); centers=[]
        for o in valid:
            x1,y1,x2,y2=o["bbox"]
            if x2<=x1 or y2<=y1: continue
            area=((x2-x1)*(y2-y1))/float(frame_width*frame_height); cx=(x1+x2)/2
            if cl<=cx<=cr:
                centers.append((o,area))
                if area>=HIGH_RISK_AREA_RATIO: risk="high"
                elif area>=NEAR_OBJECT_AREA_RATIO and risk!="high": risk="medium"
        if risk=="high": msg="Large obstacle in the forward path. Slow down."
        elif risk=="medium": msg="Obstacle is close to the forward path. Use caution."
        elif centers: msg="Object detected in the forward path."
        return {"risk":risk,"message":msg,"frame_width":frame_width}
