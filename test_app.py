import sys
import time

# Ensure UTF-8 output for Windows console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("Running EyeTracker Verification Suite")
print("=" * 60)

# 1. Test Database Module
print("[1/3] Testing SQLite Database Module...")
import db
db.init_db()
session_id = db.start_session()
print(f" -> Session started successfully: ID = {session_id}")
db.record_minute_stat(session_id, 16, 16.0, "WORK", 0.28)
db.record_minute_stat(session_id, 8, 8.0, "GAMING", 0.25)
db.end_session(session_id, 24, 12.0, "WORK")
timeline = db.get_timeline_stats(session_id)
assert len(timeline) >= 2, f"Expected >= 2 timeline rows, got {len(timeline)}"
breakdown = db.get_activity_breakdown()
print(f" -> DB Stats verified. Timeline rows: {len(timeline)}, Activities: {len(breakdown)}")

# 2. Test Activity Tracker
print("\n[2/3] Testing Activity Tracker (Win32 Foreground Window)...")
from activity_tracker import ActivityTracker
tracker = ActivityTracker()
info = tracker.update()
print(f" -> Process: {info['process']}")
print(f" -> Window Title: {info['title']}")
print(f" -> Detected Activity: {info['label']} ({info['activity']})")
assert info['activity'] in ["GAMING", "WORK", "VIDEO", "BROWSING", "SOCIAL", "OTHER"]

# 3. Test MediaPipe Face Mesh Initialization
print("\n[3/3] Testing MediaPipe Face Mesh Initialization...")
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
# Test with a dummy black image to verify pipeline works without crashing
dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
results = face_mesh.process(dummy_frame)
face_mesh.close()
print(" -> MediaPipe Face Mesh initialized and executed on test frame successfully!")

print("\n" + "=" * 60)
print("ALL VERIFICATION CHECKS PASSED!")
print("=" * 60)
