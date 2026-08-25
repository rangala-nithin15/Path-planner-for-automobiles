# Adaptive Path Planning and Collision Avoidance Assistant

A prototype perception and roadside-awareness module for:

**Adaptive Path Planning and Collision Avoidance for Autonomous Vehicles on Unstructured Indian Roads**

## What this combines from the old project

### YOLO
The original project used YOLOv8 for road-object detection and tracking. This version keeps that approach and detects:

- Car
- Motorcycle
- Bus
- Truck
- Cat
- Dog
- Horse
- Sheep
- Cow
- Elephant
- Bear
- Zebra
- Giraffe

The model is run continuously, but only every few frames to reduce processing load.

### MediaPipe
The original MediaPipe setup is retained:

- Face Mesh
- Pose
- Hands

The visual landmark drawing style is also retained.

### Voice assistant
The assistant continuously converts the current scene into short spoken warnings such as:

- "Car ahead."
- "Dog on the left."
- "Human on the right."
- "Bus ahead. Caution."
- "Large obstacle in the forward path. Slow down."

Speech is throttled so it does not speak every video frame.

### Path-planning prototype
`path_planner.py` adds a simple perception layer that classifies the forward scene as:

- CLEAR
- MEDIUM RISK
- HIGH RISK

It also provides a basic "left/right appears more open" hint when possible.

## Important limitation

This is a perception/demo system, not a safety-certified autonomous-driving controller.

The current prototype estimates proximity from bounding-box size and uses image position. A real autonomous vehicle system needs calibrated cameras, depth/LiDAR/radar, vehicle speed, road geometry, lane/road-boundary detection, temporal tracking, sensor fusion and a validated motion planner.

## Project structure

```text
Adaptive_Path_Planning_Assistant/
│
├── app.py
├── detector.py
├── human_detector.py
├── scene_assistant.py
├── path_planner.py
├── config.py
├── requirements.txt
├── README.md
│
└── models/
    └── yolov8m.pt
```

## Installation

Create a virtual environment if desired:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python app.py
```

Press `Q` to stop.

## Camera

The default camera is:

```python
CAMERA_INDEX = 0
```

If the car camera appears as another device, change the index in `config.py`.

## Why this architecture is useful for the SIH project

```text
Car Camera
    |
    v
+-------------------+
| YOLOv8            |
| vehicles/animals  |
+-------------------+
    |
    +----------------------+
    |                      |
    v                      v
+-------------+      +-------------+
| MediaPipe   |      | Object      |
| human cues  |      | positions   |
+-------------+      +-------------+
    |                      |
    +----------+-----------+
               |
               v
       Scene Understanding
               |
               v
       Collision Risk Layer
               |
       +-------+-------+
       |               |
       v               v
   Voice Alert     Path Hint
```

This gives you a clean base for adding lane/road-boundary detection, depth estimation, Indian-road obstacle classes, and a real path planner later.
