import threading
import time
import re
import pyttsx3

from config import (
    SPEECH_RATE,
    KNOWN_OBJECT_REPEAT,
    NEW_OBJECT_COOLDOWN,
)


class SceneAssistant:

    def __init__(self):

        # ============================================================
        # NAVIGATION STATE
        # ============================================================

        self.navigation_mode = False

        # ============================================================
        # TEXT TO SPEECH
        # ============================================================

        self.engine = pyttsx3.init()

        self.engine.setProperty(
            "rate",
            SPEECH_RATE
        )

        # ============================================================
        # SPEECH THREADING
        # ============================================================

        self.speech_lock = threading.Lock()

        self.pending_messages = []

        self.pending_lock = threading.Lock()

        self.speech_thread = None

        # ============================================================
        # OBJECT TRACKING
        # ============================================================

        # Stores:
        #
        # object_key -> last time announced
        #
        self.last_announced = {}

        # ============================================================
        # RISK WARNING
        # ============================================================

        self.last_risk_message = ""

        self.last_risk_time = 0

    # ================================================================
    # DIRECTION
    # ================================================================

    @staticmethod
    def direction(
        bbox,
        frame_width
    ):

        if bbox is None:
            return "ahead"

        x1, y1, x2, y2 = bbox

        center_x = (
            x1 + x2
        ) / 2

        ratio = (
            center_x /
            float(frame_width)
        )

        if ratio < 0.34:

            return "left"

        elif ratio > 0.66:

            return "right"

        else:

            return "ahead"

    # ================================================================
    # NORMALIZE LABEL
    # ================================================================

    @staticmethod
    def normalize_label(
        label
    ):

        if label is None:
            return ""

        return re.sub(
            r"[^a-zA-Z0-9]+",
            " ",
            str(label)
        ).strip().lower()

    # ================================================================
    # OBJECT POSITION
    # ================================================================

    def object_key(
        self,
        obj
    ):

        """
        Create a stable key for an object.

        We DON'T use the exact bounding box because the box moves
        slightly every frame.

        Example:

        Human at x=310
        Human at x=315
        Human at x=320

        should still be considered the SAME human.
        """

        label = self.normalize_label(
            obj.get("label")
        )

        bbox = obj.get(
            "bbox"
        )

        if bbox is None:

            return None

        x1, y1, x2, y2 = bbox

        center_x = (
            x1 + x2
        ) / 2

        center_y = (
            y1 + y2
        ) / 2

        # Coarse position buckets.

        position_x = int(
            center_x / 120
        )

        position_y = int(
            center_y / 120
        )

        return (
            f"{label}:"
            f"{position_x}:"
            f"{position_y}"
        )

    # ================================================================
    # ACTIVATE NAVIGATION
    # ================================================================

    def activate_navigation(self):

        if self.navigation_mode:

            return

        self.navigation_mode = True

        print(
            "NAVIGATION MODE: ON"
        )

        self.say_immediate(
            "Navigation mode activated."
        )

    # ================================================================
    # DEACTIVATE NAVIGATION
    # ================================================================

    def deactivate_navigation(self):

        if not self.navigation_mode:

            return

        self.navigation_mode = False

        print(
            "NAVIGATION MODE: OFF"
        )

        self.say_immediate(
            "Navigation mode stopped."
        )

    # ================================================================
    # HANDLE JARVIS COMMAND
    # ================================================================

    def handle_wake_command(
        self,
        command
    ):

        if command is None:

            return

        command = command.lower().strip()

        print(
            "Jarvis command:",
            command
        )

        # ------------------------------------------------------------
        # NAVIGATION ON
        # ------------------------------------------------------------

        if (
            "navigate" in command
            or
            "start navigation" in command
            or
            "navigation on" in command
            or
            "begin navigation" in command
        ):

            self.activate_navigation()

            return

        # ------------------------------------------------------------
        # NAVIGATION OFF
        # ------------------------------------------------------------

        if (
            "stop navigation" in command
            or
            "navigation off" in command
            or
            "cancel navigation" in command
            or
            "exit navigation" in command
        ):

            self.deactivate_navigation()

            return

        # ------------------------------------------------------------
        # SLEEP
        # ------------------------------------------------------------

        if (
            "sleep" in command
            or
            "stand by" in command
            or
            "stop listening" in command
        ):

            self.navigation_mode = False

            self.say_immediate(
                "Okay. I am standing by."
            )

            return

        # ------------------------------------------------------------
        # WHAT DO YOU SEE
        # ------------------------------------------------------------

        if (
            "what do you see" in command
            or
            "what is ahead" in command
            or
            "what's ahead" in command
        ):

            self.say_immediate(
                "I am checking the road."
            )

            return

        # ------------------------------------------------------------
        # HELLO
        # ------------------------------------------------------------

        if (
            "hello" in command
            or
            command == "hi"
            or
            "hey" in command
        ):

            self.say_immediate(
                "Hello. I am here."
            )

            return

        # ------------------------------------------------------------
        # HOW ARE YOU
        # ------------------------------------------------------------

        if "how are you" in command:

            self.say_immediate(
                "I am working normally."
            )

            return

        # ------------------------------------------------------------
        # UNKNOWN COMMAND
        # ------------------------------------------------------------

        self.say_immediate(
            "I heard you. Say navigate to start navigation."
        )

    # ================================================================
    # CREATE SPEECH MESSAGE
    # ================================================================

    def create_object_message(
        self,
        obj,
        frame_width
    ):

        label = obj.get(
            "label",
            "Object"
        )

        bbox = obj.get(
            "bbox"
        )

        if bbox is None:

            return None

        direction = self.direction(
            bbox,
            frame_width
        )

        if direction == "ahead":

            return (
                f"{label} ahead."
            )

        elif direction == "left":

            return (
                f"{label} on the left."
            )

        else:

            return (
                f"{label} on the right."
            )

    # ================================================================
    # UPDATE SCENE
    # ================================================================

    def update(
        self,
        objects,
        plan
    ):

        """
        Called continuously from app.py.

        IMPORTANT:

        If navigation mode is OFF:
            Do nothing.

        If navigation mode is ON:
            New objects are announced immediately.
            Existing objects repeat after KNOWN_OBJECT_REPEAT seconds.
        """

        # ============================================================
        # NAVIGATION OFF
        # ============================================================

        if not self.navigation_mode:

            return

        # ============================================================
        # CURRENT TIME
        # ============================================================

        now = time.time()

        # ============================================================
        # FRAME WIDTH
        # ============================================================

        frame_width = plan.get(
            "frame_width",
            640
        )

        # ============================================================
        # VALID OBJECTS
        # ============================================================

        valid_objects = []

        for obj in objects:

            if not isinstance(
                obj,
                dict
            ):

                continue

            label = obj.get(
                "label"
            )

            bbox = obj.get(
                "bbox"
            )

            if not label:

                continue

            if bbox is None:

                continue

            if len(bbox) != 4:

                continue

            x1, y1, x2, y2 = bbox

            if x2 <= x1:

                continue

            if y2 <= y1:

                continue

            valid_objects.append(
                obj
            )

        # ============================================================
        # PROCESS EVERY OBJECT
        # ============================================================

        for obj in valid_objects:

            label = obj.get(
                "label"
            )

            key = self.object_key(
                obj
            )

            if key is None:

                continue

            # --------------------------------------------------------
            # LAST TIME THIS OBJECT WAS SPOKEN
            # --------------------------------------------------------

            last_time = self.last_announced.get(
                key
            )

            # ========================================================
            # NEW OBJECT
            # ========================================================

            if last_time is None:

                message = self.create_object_message(
                    obj,
                    frame_width
                )

                if message:

                    print(
                        "SPEAK:",
                        message
                    )

                    self.queue_speech(
                        message
                    )

                    self.last_announced[
                        key
                    ] = now

                continue

            # ========================================================
            # EXISTING OBJECT
            # ========================================================

            elapsed = (
                now -
                last_time
            )

            # --------------------------------------------------------
            # REPEAT AFTER 4 SECONDS
            # --------------------------------------------------------

            if elapsed >= KNOWN_OBJECT_REPEAT:

                message = self.create_object_message(
                    obj,
                    frame_width
                )

                if message:

                    print(
                        "SPEAK:",
                        message
                    )

                    self.queue_speech(
                        message
                    )

                    self.last_announced[
                        key
                    ] = now

        # ============================================================
        # REMOVE OLD OBJECT KEYS
        # ============================================================

        active_keys = set()

        for obj in valid_objects:

            key = self.object_key(
                obj
            )

            if key:

                active_keys.add(
                    key
                )

        cleaned = {}

        for key, timestamp in self.last_announced.items():

            # Keep objects currently visible.

            if key in active_keys:

                cleaned[key] = timestamp

                continue

            # Keep recently disappeared objects for a short time.
            # This prevents them becoming "new" immediately because
            # of one missed detection frame.

            if (
                now - timestamp
                < 2.0
            ):

                cleaned[key] = timestamp

        self.last_announced = cleaned

        # ============================================================
        # COLLISION WARNING
        # ============================================================

        risk = plan.get(
            "risk",
            "clear"
        )

        if risk == "high":

            warning = (
                "Collision risk ahead. Slow down."
            )

            # Don't repeat every frame.

            if (
                warning !=
                self.last_risk_message
                or
                now -
                self.last_risk_time
                >= 4
            ):

                print(
                    "SPEAK:",
                    warning
                )

                self.queue_speech(
                    warning
                )

                self.last_risk_message = (
                    warning
                )

                self.last_risk_time = (
                    now
                )

        else:

            # Reset so a future high-risk situation
            # can trigger immediately.

            self.last_risk_message = ""

    # ================================================================
    # QUEUE SPEECH
    # ================================================================

    def queue_speech(
        self,
        text
    ):

        if not text:

            return

        with self.pending_lock:

            # --------------------------------------------------------
            # IMPORTANT:
            #
            # Don't add the exact same message repeatedly.
            # --------------------------------------------------------

            if text in self.pending_messages:

                return

            self.pending_messages.append(
                text
            )

        self.start_speech_worker()

    # ================================================================
    # START SPEECH WORKER
    # ================================================================

    def start_speech_worker(
        self
    ):

        if (
            self.speech_thread
            and
            self.speech_thread.is_alive()
        ):

            return

        self.speech_thread = threading.Thread(
            target=self.speech_worker,
            daemon=True
        )

        self.speech_thread.start()

    # ================================================================
    # SPEECH WORKER
    # ================================================================

    def speech_worker(
        self
    ):

        while True:

            with self.pending_lock:

                if not self.pending_messages:

                    return

                text = (
                    self.pending_messages.pop(
                        0
                    )
                )

            # --------------------------------------------------------
            # SPEAK
            # --------------------------------------------------------

            with self.speech_lock:

                try:

                    self.engine.say(
                        text
                    )

                    self.engine.runAndWait()

                except Exception as error:

                    print(
                        "Speech error:",
                        error
                    )

    # ================================================================
    # IMMEDIATE SPEECH
    # ================================================================

    def say_immediate(
        self,
        text
    ):

        if not text:

            return

        def speak_now():

            with self.speech_lock:

                try:

                    self.engine.say(
                        text
                    )

                    self.engine.runAndWait()

                except Exception as error:

                    print(
                        "Speech error:",
                        error
                    )

        threading.Thread(
            target=speak_now,
            daemon=True
        ).start()

    # ================================================================
    # CLOSE
    # ================================================================

    def close(self):

        try:

            with self.pending_lock:

                self.pending_messages.clear()

        except Exception:

            pass

        try:

            self.engine.stop()

        except Exception:

            pass
