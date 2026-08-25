import cv2
import time

from detector import RoadObjectDetector
from human_detector import MediaPipeHumanDetector
from scene_assistant import SceneAssistant
from path_planner import PathPlanner
from voice_listener import JarvisListener

from config import (
    CAMERA_INDEX,
    FRAME_WIDTH,
    FRAME_HEIGHT,
    YOLO_EVERY_N_FRAMES,
)


def main():

    # ============================================================
    # CAMERA
    # ============================================================

    # Your Windows camera was confirmed to work with index 0.
    camera = cv2.VideoCapture(CAMERA_INDEX)

    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        FRAME_WIDTH
    )

    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        FRAME_HEIGHT
    )

    camera.set(
        cv2.CAP_PROP_BUFFERSIZE,
        1
    )

    if not camera.isOpened():

        raise RuntimeError(
            f"Could not open camera index {CAMERA_INDEX}"
        )

    print()
    print("==============================================")
    print(" ADAPTIVE ROAD ASSISTANT")
    print("==============================================")
    print("Camera opened successfully.")
    print("Camera index:", CAMERA_INDEX)
    print()

    # ============================================================
    # AI MODELS
    # ============================================================

    print("Loading YOLO...")

    yolo = RoadObjectDetector()

    print("YOLO loaded.")

    print("Loading MediaPipe...")

    human = MediaPipeHumanDetector()

    print("MediaPipe loaded.")

    # ============================================================
    # ASSISTANT
    # ============================================================

    assistant = SceneAssistant()

    planner = PathPlanner()

    # ============================================================
    # JARVIS MICROPHONE
    # ============================================================

    listener = JarvisListener(
        assistant
    )

    microphone_started = listener.start()

    if microphone_started:

        print()
        print("Jarvis microphone is ACTIVE.")
        print()
        print("Say:")
        print("  Jarvis, navigate")
        print()
        print("to start navigation mode.")
        print()
        print("Say:")
        print("  Jarvis, stop navigation")
        print()
        print("to stop navigation mode.")

    else:

        print()
        print("WARNING:")
        print("Jarvis microphone could not be started.")
        print("Camera detection will still work.")

    print()
    print("Press Q to quit.")
    print("==============================================")
    print()

    # ============================================================
    # VARIABLES
    # ============================================================

    frame_count = 0

    # Store latest YOLO detections.
    last_objects = []

    # Store latest planner result.
    last_plan = {
        "risk": "clear",
        "message": "Road appears clear.",
        "frame_width": FRAME_WIDTH
    }

    # Prevent printing the exact same detection every frame.
    last_debug_detection = ""
    last_debug_time = 0

    try:

        # ========================================================
        # MAIN LIVE CAMERA LOOP
        # ========================================================

        while True:

            # ----------------------------------------------------
            # READ CAMERA
            # ----------------------------------------------------

            ret, frame = camera.read()

            if not ret or frame is None:

                print(
                    "WARNING: Camera frame could not be read."
                )

                time.sleep(0.05)

                continue

            # ----------------------------------------------------
            # MIRROR CAMERA
            # ----------------------------------------------------

            frame = cv2.flip(
                frame,
                1
            )

            # ----------------------------------------------------
            # RESIZE
            # ----------------------------------------------------

            frame = cv2.resize(
                frame,
                (
                    FRAME_WIDTH,
                    FRAME_HEIGHT
                )
            )

            # ====================================================
            # YOLO DETECTION
            # ====================================================

            if frame_count % YOLO_EVERY_N_FRAMES == 0:

                last_objects = yolo.detect(
                    frame
                )

            # ====================================================
            # MEDIAPIPE HUMAN DETECTION
            # ====================================================

            human_result = human.detect(
                frame
            )

            # ====================================================
            # COMBINE DETECTIONS
            # ====================================================

            objects = list(
                last_objects
            )

            # IMPORTANT:
            # Only add MediaPipe Human when it actually has
            # a valid bounding box.
            #
            # This prevents:
            #
            # bbox = None
            #
            # from crashing path_planner.py.

            if (
                human_result.get("detected")
                and human_result.get("bbox") is not None
            ):

                human_bbox = human_result["bbox"]

                # Validate bounding box.

                if (
                    len(human_bbox) == 4
                    and human_bbox[2] > human_bbox[0]
                    and human_bbox[3] > human_bbox[1]
                ):

                    objects.append(
                        {
                            "label": "Human",

                            "category": "human",

                            "bbox": human_bbox,

                            "confidence":
                                human_result.get(
                                    "confidence",
                                    0.0
                                ),

                            "source":
                                "mediapipe",

                            "track_id":
                                None
                        }
                    )

            # ====================================================
            # DRAW YOLO
            # ====================================================

            yolo.draw(
                frame,
                last_objects
            )

            # ====================================================
            # DRAW MEDIAPIPE
            # ====================================================

            human.draw(
                frame,
                human_result
            )

            # ====================================================
            # PATH / COLLISION ANALYSIS
            # ====================================================

            last_plan = planner.analyze(
                objects,
                FRAME_WIDTH,
                FRAME_HEIGHT
            )

            # ====================================================
            # DEBUG DETECTION OUTPUT
            # ====================================================

            if objects:

                detection_text = ", ".join(
                    [
                        f"{obj['label']} "
                        f"{obj.get('confidence', 0):.2f}"
                        for obj in objects
                    ]
                )

                current_time = time.time()

                # Print only when detection changes
                # or every 2 seconds.

                if (
                    detection_text !=
                    last_debug_detection
                    or
                    current_time -
                    last_debug_time > 2
                ):

                    print(
                        "DETECTED:",
                        detection_text
                    )

                    last_debug_detection = (
                        detection_text
                    )

                    last_debug_time = (
                        current_time
                    )

            # ====================================================
            # JARVIS / VOICE ASSISTANT
            # ====================================================

            # IMPORTANT:
            #
            # SceneAssistant itself decides whether
            # navigation mode is ON.
            #
            # Therefore:
            #
            # Standby:
            #     no object speech
            #
            # Navigation ON:
            #     object speech
            #
            assistant.update(
                objects,
                last_plan
            )

            # ====================================================
            # HUD
            # ====================================================

            if assistant.navigation_mode:

                mode_text = "NAVIGATION ON"

            else:

                mode_text = "STANDBY"

            # Background.

            cv2.rectangle(
                frame,
                (0, 0),
                (FRAME_WIDTH, 85),
                (20, 20, 20),
                -1
            )

            # Mode.

            cv2.putText(
                frame,
                f"Mode: {mode_text}",
                (15, 27),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 255),
                2
            )

            # Risk.

            risk = last_plan.get(
                "risk",
                "clear"
            )

            cv2.putText(
                frame,
                f"Risk: {risk.upper()}",
                (15, 55),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.60,
                (255, 255, 255),
                2
            )

            # Instruction.

            cv2.putText(
                frame,
                "Say: Jarvis, navigate",
                (260, 27),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (220, 220, 220),
                1
            )

            # Quit instruction.

            cv2.putText(
                frame,
                "Q = Quit",
                (260, 55),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (220, 220, 220),
                1
            )

            # ====================================================
            # SHOW CAMERA
            # ====================================================

            cv2.imshow(
                "Adaptive Road Assistant",
                frame
            )

            # ====================================================
            # KEYBOARD
            # ====================================================

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):

                print()
                print("Stopping assistant...")

                break

            # ----------------------------------------------------
            # NEXT FRAME
            # ----------------------------------------------------

            frame_count += 1

    except KeyboardInterrupt:

        print()
        print("Interrupted by user.")

    except Exception as error:

        print()
        print("==============================================")
        print("APPLICATION ERROR")
        print("==============================================")
        print(error)
        print()
        print(
            "The camera will now be released."
        )

    finally:

        # ========================================================
        # CLEANUP
        # ========================================================

        print("Stopping microphone...")

        try:

            listener.stop()

        except Exception as error:

            print(
                "Microphone cleanup error:",
                error
            )

        print("Releasing camera...")

        try:

            camera.release()

        except Exception as error:

            print(
                "Camera cleanup error:",
                error
            )

        print("Closing MediaPipe...")

        try:

            human.close()

        except Exception as error:

            print(
                "MediaPipe cleanup error:",
                error
            )

        print("Closing voice assistant...")

        try:

            assistant.close()

        except Exception as error:

            print(
                "Voice cleanup error:",
                error
            )

        cv2.destroyAllWindows()

        print("Assistant stopped.")


# ================================================================
# PROGRAM START
# ================================================================

if __name__ == "__main__":

    main()