import speech_recognition as sr
from config import WAKE_WORD
class JarvisListener:
    def __init__(self,assistant):
        self.assistant=assistant; self.r=sr.Recognizer(); self.r.dynamic_energy_threshold=True; self.r.pause_threshold=.7; self.stop_fn=None
    def start(self):
        try:
            mic=sr.Microphone()
            with mic as source: self.r.adjust_for_ambient_noise(source,duration=.8)
            self.stop_fn=self.r.listen_in_background(mic,self.callback,phrase_time_limit=5)
            print("Jarvis listener started. Say: Jarvis navigate")
            return True
        except Exception as e:
            print("Microphone listener unavailable:",e); return False
    def callback(self,recognizer,audio):
        try:text=recognizer.recognize_google(audio).lower().strip()
        except (sr.UnknownValueError,sr.RequestError):return
        print("Heard:",text)
        if WAKE_WORD not in text:return
        cmd=text.split(WAKE_WORD,1)[1].strip()
        if cmd:
            self.assistant.handle_wake_command(cmd)
        else:self.assistant.say("Yes. What do you need?")
    def stop(self):
        if self.stop_fn:self.stop_fn(wait_for_stop=False); self.stop_fn=None
