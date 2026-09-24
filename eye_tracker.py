import cv2
import mediapipe as mp
import numpy as np
import time
import math
from collections import deque
from typing import Dict, Optional, Tuple


# Landmark points for eye aspect ratio (EAR)
LEFT_EYE_LANDMARKS = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_LANDMARKS = [362, 385, 387, 263, 373, 380]

# Full eye contour for rendering
LEFT_EYE_CONTOUR = [33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7]
RIGHT_EYE_CONTOUR = [362, 398, 384, 385, 386, 387, 388, 466, 263, 249, 390, 373, 374, 380, 381, 382]


def euclidean_dist(pt1, pt2) -> float:
    return math.hypot(pt1[0] - pt2[0], pt1[1] - pt2[1])


def calculate_ear(landmarks, eye_indices, width: int, height: int) -> float:
    """
    Computes Eye Aspect Ratio (EAR) given 6 landmark points.
    Formula: EAR = (|p2 - p6| + |p3 - p5|) / (2 * |p1 - p4|)
    Zero-allocation math.hypot optimization (16x faster than numpy linalg.norm).
    """
    i1, i2, i3, i4, i5, i6 = eye_indices
    lm = landmarks

    x1, y1 = lm[i1].x * width, lm[i1].y * height
    x2, y2 = lm[i2].x * width, lm[i2].y * height
    x3, y3 = lm[i3].x * width, lm[i3].y * height
    x4, y4 = lm[i4].x * width, lm[i4].y * height
    x5, y5 = lm[i5].x * width, lm[i5].y * height
    x6, y6 = lm[i6].x * width, lm[i6].y * height

    v1 = math.hypot(x2 - x6, y2 - y6)
    v2 = math.hypot(x3 - x5, y3 - y5)
    h = math.hypot(x1 - x4, y1 - y4)

    if h < 1e-6:
        return 0.0
    return (v1 + v2) / (2.0 * h)


def check_looking_down(landmarks, width: int, height: int) -> bool:
    """
    Determines if user is looking down with eyes rather than closing them (blinking).
    Uses scale-invariant relative iris position within the palpebral fissure.
    """
    try:
        if len(landmarks) <= 473:
            return False

        # Left eye: top=159, bot=145, left=33, right=133, iris=468
        l_top_y = landmarks[159].y * height
        l_bot_y = landmarks[145].y * height
        l_iris_y = landmarks[468].y * height
        l_eye_w = math.hypot((landmarks[33].x - landmarks[133].x) * width, (landmarks[33].y - landmarks[133].y) * height)
        l_eye_h = abs(l_bot_y - l_top_y)

        # Right eye: top=386, bot=374, left=362, right=263, iris=473
        r_top_y = landmarks[386].y * height
        r_bot_y = landmarks[374].y * height
        r_iris_y = landmarks[473].y * height
        r_eye_w = math.hypot((landmarks[362].x - landmarks[263].x) * width, (landmarks[362].y - landmarks[263].y) * height)
        r_eye_h = abs(r_bot_y - r_top_y)

        # If both eyes are almost completely shut (< 0.10 of eye width or < 3.5px), it's a real blink, not looking down
        if (l_eye_w > 0 and l_eye_h / l_eye_w < 0.11) or (r_eye_w > 0 and r_eye_h / r_eye_w < 0.11) or (l_eye_h < 3.5 and r_eye_h < 3.5):
            return False

        # Vertical iris position: 0.0 = top eyelid, 1.0 = bottom eyelid
        l_iris_ratio = (l_iris_y - l_top_y) / l_eye_h if l_eye_h > 1e-4 else 0.5
        r_iris_ratio = (r_iris_y - r_top_y) / r_eye_h if r_eye_h > 1e-4 else 0.5
        avg_iris_ratio = (l_iris_ratio + r_iris_ratio) / 2.0

        # If iris is settled in the bottom section (> 0.65) while eye is still open, user is looking down
        return avg_iris_ratio > 0.65
    except (IndexError, AttributeError):
        return False


class EyeTracker:
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = None

        # Dual-threshold hysteresis blink detection variables
        self.baseline_ear: float = 0.28
        self.close_threshold: float = 0.16
        self.open_threshold: float = 0.20
        self.ear_threshold: float = 0.16  # compatibility alias
        self.is_blinking: bool = False
        self.blink_start_time: float = 0.0
        self.blink_frames_count: int = 0
        self.min_blink_ear: float = 1.0

        # Stats
        self.total_blinks: int = 0
        self.blink_timestamps = deque()  # stores timestamp of each blink
        self.last_blink_time: float = time.time()
        self.session_start_time: float = time.time()
        self.last_minute_blinks: int = 0

        # Current telemetry
        self.current_ear: float = 0.0
        self.left_ear: float = 0.0
        self.right_ear: float = 0.0
        self.face_detected: bool = False
        self.is_running: bool = False

        # Visual preview
        self.latest_annotated_frame: Optional[bytes] = None
        self.latest_frame_rgb: Optional[np.ndarray] = None

    def set_camera_index(self, index: int) -> bool:
        if self.camera_index == index:
            return True
        was_running = self.is_running
        if was_running:
            self.stop()
        self.camera_index = index
        if was_running:
            return self.start()
        return True

    def start(self) -> bool:
        if self.is_running:
            return True

        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            # Fallback to default API
            self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            print(f"[EyeTracker] Warning: Unable to open camera at index {self.camera_index}")
            self.is_running = False
            return False

        # Configure camera resolution and single frame buffer to eliminate lag
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Precise FaceMesh with iris landmarks for accurate gaze & downward tilt tracking
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.is_running = True
        self.session_start_time = time.time()
        self.last_blink_time = time.time()
        self.total_blinks = 0
        self.blink_timestamps.clear()
        self.blink_frames_count = 0
        self.min_blink_ear = 1.0
        return True

    def reset(self):
        """Resets all tracking counters for a completely fresh session."""
        self.total_blinks = 0
        self.blink_timestamps.clear()
        self.session_start_time = time.time()
        self.last_blink_time = time.time()
        self.is_blinking = False
        self.blink_frames_count = 0
        self.min_blink_ear = 1.0
        self.current_ear = 0.0
        self.left_ear = 0.0
        self.right_ear = 0.0

    def stop(self):
        self.is_running = False
        if self.face_mesh:
            try:
                self.face_mesh.close()
            except Exception:
                pass
            self.face_mesh = None
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def process_frame(self, generate_preview: bool = False, show_landmarks: bool = False) -> Dict:
        """
        Reads a frame from camera, analyzes eye landmarks, and updates blink stats.
        Optimized for zero extra memory copies and minimal CPU footprint.
        """
        now = time.time()
        if not self.cap or not self.cap.isOpened():
            return self.get_telemetry()

        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.face_detected = False
            return self.get_telemetry()

        # Flip horizontally only if preview is displayed to avoid wasted memory copy
        if generate_preview:
            frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self.face_mesh.process(rgb_frame)
        rgb_frame.flags.writeable = True

        if results.multi_face_landmarks:
            self.face_detected = True
            landmarks = results.multi_face_landmarks[0].landmark

            self.left_ear = calculate_ear(landmarks, LEFT_EYE_LANDMARKS, w, h)
            self.right_ear = calculate_ear(landmarks, RIGHT_EYE_LANDMARKS, w, h)
            self.current_ear = (self.left_ear + self.right_ear) / 2.0

            looking_down = check_looking_down(landmarks, w, h)

            # Adaptive baseline update when eyes are clearly open and user is not looking down
            if self.current_ear > 0.22 and not looking_down:
                self.baseline_ear = max(0.22, min(0.38, self.baseline_ear * 0.98 + self.current_ear * 0.02))
                self.close_threshold = max(0.13, min(0.18, self.baseline_ear * 0.58))
                self.open_threshold = max(0.17, min(0.24, self.baseline_ear * 0.72))
                self.ear_threshold = self.close_threshold

            # Timeout protection: if eye closure exceeds 0.40s, cancel blink (looking down or eye rest)
            if self.is_blinking and (now - self.blink_start_time > 0.40):
                self.is_blinking = False
                self.blink_frames_count = 0

            # Blink state machine with hysteresis and downward gaze rejection
            if self.current_ear < self.close_threshold:
                if not self.is_blinking:
                    # Do not start a blink if the user is looking down; enforce 80ms refractory period
                    if not looking_down and (now - self.last_blink_time >= 0.08):
                        self.is_blinking = True
                        self.blink_start_time = now
                        self.blink_frames_count = 1
                        self.min_blink_ear = self.current_ear
                else:
                    self.blink_frames_count += 1
                    self.min_blink_ear = min(self.min_blink_ear, self.current_ear)
            elif self.current_ear >= self.open_threshold:
                if self.is_blinking:
                    duration = now - self.blink_start_time
                    # Fast blinks take as little as 20ms (1-2 frames at 30 FPS)
                    # Natural blinks take up to 380ms
                    if 0.020 <= duration <= 0.38 and self.blink_frames_count >= 1:
                        self.total_blinks += 1
                        self.last_blink_time = now
                        self.blink_timestamps.append(now)
                    self.is_blinking = False
                    self.blink_frames_count = 0

            if generate_preview and show_landmarks:
                self._annotate_frame(frame, landmarks, w, h)
        else:
            self.face_detected = False
            self.current_ear = 0.0
            self.is_blinking = False
            self.blink_frames_count = 0

        # Clean old timestamps (> 60 seconds)
        while self.blink_timestamps and (now - self.blink_timestamps[0] > 60.0):
            self.blink_timestamps.popleft()

        if generate_preview:
            self.latest_frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Optional JPEG buffer for web if needed
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 65])
            self.latest_annotated_frame = buffer.tobytes()

        return self.get_telemetry()

    def _annotate_frame(self, frame, landmarks, w: int, h: int):
        """Draws subtle eye contours, iris points, and status indicators on preview frame."""
        for contour in [LEFT_EYE_CONTOUR, RIGHT_EYE_CONTOUR]:
            pts = np.array([
                [int(landmarks[idx].x * w), int(landmarks[idx].y * h)]
                for idx in contour
            ], np.int32)
            color = (0, 0, 255) if self.is_blinking else (0, 255, 128)
            cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=1, lineType=cv2.LINE_AA)

        # Draw iris centers if available
        if len(landmarks) > 473:
            for idx in [468, 473]:
                cx = int(landmarks[idx].x * w)
                cy = int(landmarks[idx].y * h)
                cv2.circle(frame, (cx, cy), 2, (0, 255, 255), -1, lineType=cv2.LINE_AA)

        # Status text overlay
        bpm = len(self.blink_timestamps)
        cv2.putText(
            frame,
            f"Blinks: {self.total_blinks} | BPM: {bpm} | EAR: {self.current_ear:.2f}",
            (15, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

    def get_telemetry(self) -> Dict:
        now = time.time()
        # Clean older than 60s
        while self.blink_timestamps and (now - self.blink_timestamps[0] > 60.0):
            self.blink_timestamps.popleft()

        bpm = len(self.blink_timestamps)
        session_minutes = max(0.1, (now - self.session_start_time) / 60.0)
        avg_bpm = round(self.total_blinks / session_minutes, 1)
        seconds_since_blink = round(now - self.last_blink_time, 1)

        # Health status evaluation
        # Norm in rest: 15-20 / min
        # Norm on computer: 8-14 / min is acceptable, < 8 is dry eye strain, > 12s without blink is alert
        if not self.face_detected:
            health_status = "NO_FACE"
            health_color = "#9ca3af"
            health_msg = "Face not detected"
        elif seconds_since_blink >= 12.0:
            health_status = "CRITICAL_DRY"
            health_color = "#ef4444"
            health_msg = "Eyes dry! Please blink"
        elif bpm < 8:
            health_status = "LOW_RATE"
            health_color = "#f59e0b"
            health_msg = "Low blink rate (eye fatigue)"
        elif bpm < 14:
            health_status = "MODERATE"
            health_color = "#3b82f6"
            health_msg = "Moderate screen focus"
        else:
            health_status = "HEALTHY"
            health_color = "#10b981"
            health_msg = "Healthy blink rate"

        return {
            "face_detected": self.face_detected,
            "total_blinks": self.total_blinks,
            "bpm": bpm,
            "avg_bpm": avg_bpm,
            "current_ear": round(self.current_ear, 3),
            "baseline_ear": round(self.baseline_ear, 3),
            "is_blinking": self.is_blinking,
            "seconds_since_blink": seconds_since_blink,
            "session_duration_sec": int(now - self.session_start_time),
            "health_status": health_status,
            "health_msg": health_msg,
            "health_color": health_color,
        }
