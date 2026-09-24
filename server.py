import asyncio
import json
import time
import sys
from typing import Dict, List, Optional

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

import db
from eye_tracker import EyeTracker
from activity_tracker import ActivityTracker, ActivityType, ACTIVITY_META

app = FastAPI(title="EyeTracker Service")

# Subsystems
eye_tracker = EyeTracker(camera_index=0)
activity_tracker = ActivityTracker()
current_session_id: Optional[int] = None

# Background loop state
tracking_task = None
connected_websockets: List[WebSocket] = []

# App Settings
settings = {
    "sound_alerts": True,
    "blink_delay_threshold": 12.0,  # seconds
    "low_bpm_threshold": 8.0,
    "rule_20_20_20": True,
    "preview_enabled": True
}

# Aggregation helper
minute_buffer_blinks: int = 0
last_db_minute_record: float = time.time()


class ActivityOverrideRequest(BaseModel):
    activity: Optional[str] = None


class SettingsUpdateRequest(BaseModel):
    sound_alerts: Optional[bool] = None
    blink_delay_threshold: Optional[float] = None
    low_bpm_threshold: Optional[float] = None
    rule_20_20_20: Optional[bool] = None
    preview_enabled: Optional[bool] = None


@app.on_event("startup")
async def startup_event():
    global current_session_id, tracking_task
    db.init_db()
    current_session_id = db.start_session()
    eye_tracker.start()
    tracking_task = asyncio.create_task(tracking_worker())
    print(f"[Server] EyeTracker started. Session ID: {current_session_id}")


@app.on_event("shutdown")
async def shutdown_event():
    global current_session_id, tracking_task
    if tracking_task:
        tracking_task.cancel()
    telemetry = eye_tracker.get_telemetry()
    if current_session_id:
        db.end_session(
            current_session_id,
            telemetry["total_blinks"],
            telemetry["avg_bpm"],
            activity_tracker.current_activity.value
        )
    eye_tracker.stop()
    print("[Server] EyeTracker stopped.")


async def tracking_worker():
    """High-performance async loop running the camera capture and telemetry broadcasting."""
    global minute_buffer_blinks, last_db_minute_record

    last_activity_update = time.time()
    last_known_blinks = 0

    while True:
        try:
            # Process video frame
            telemetry = eye_tracker.process_frame(generate_preview=settings["preview_enabled"])

            # Check new blinks
            current_blinks = telemetry["total_blinks"]
            new_blinks = max(0, current_blinks - last_known_blinks)
            last_known_blinks = current_blinks
            minute_buffer_blinks += new_blinks

            now = time.time()

            # Poll activity every 1.5 seconds
            if now - last_activity_update >= 1.5:
                activity_tracker.update()
                last_activity_update = now

            # Save minute stat every 60 seconds
            if now - last_db_minute_record >= 60.0:
                if current_session_id:
                    db.record_minute_stat(
                        session_id=current_session_id,
                        blinks_count=minute_buffer_blinks,
                        bpm=float(telemetry["bpm"]),
                        activity=activity_tracker.current_activity.value,
                        avg_ear=float(telemetry["current_ear"])
                    )
                minute_buffer_blinks = 0
                last_db_minute_record = now

            # Broadcast to active WebSockets
            if connected_websockets:
                payload = build_full_payload(telemetry)
                msg = json.dumps(payload)
                dead_sockets = []
                for ws in connected_websockets:
                    try:
                        await ws.send_text(msg)
                    except Exception:
                        dead_sockets.append(ws)
                for ds in dead_sockets:
                    if ds in connected_websockets:
                        connected_websockets.remove(ds)

            # Sleep 30ms (~33 FPS)
            await asyncio.sleep(0.03)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[Worker Error] {e}")
            await asyncio.sleep(0.1)


def build_full_payload(telemetry: Dict) -> Dict:
    act_info = {
        "activity": activity_tracker.current_activity.value,
        "label": ACTIVITY_META[activity_tracker.current_activity]["label"],
        "icon": ACTIVITY_META[activity_tracker.current_activity]["icon"],
        "color": ACTIVITY_META[activity_tracker.current_activity]["color"],
        "process": activity_tracker.current_process_name,
        "title": activity_tracker.current_window_title,
        "manual_override": activity_tracker.manual_override.value if activity_tracker.manual_override else None,
        "durations": activity_tracker.activity_durations
    }

    # Determine alert triggers
    alert = None
    if settings["sound_alerts"]:
        if telemetry["seconds_since_blink"] >= settings["blink_delay_threshold"]:
            alert = {
                "type": "DELAYED_BLINK",
                "message": f"Вы не моргали уже {int(telemetry['seconds_since_blink'])} секунд! Поморгайте, чтобы увлажнить глаза."
            }
        elif telemetry["bpm"] < settings["low_bpm_threshold"] and telemetry["session_duration_sec"] > 60:
            alert = {
                "type": "LOW_BPM",
                "message": f"Частота морганий снизилась до {telemetry['bpm']} в минуту. Глаза устают!"
            }

    return {
        "telemetry": telemetry,
        "activity": act_info,
        "alert": alert,
        "settings": settings,
        "timestamp": time.time()
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            cmd = json.loads(data)
            action = cmd.get("action")
            if action == "override_activity":
                activity_tracker.set_manual_override(cmd.get("activity"))
            elif action == "reset_session":
                global current_session_id
                telemetry = eye_tracker.get_telemetry()
                if current_session_id:
                    db.end_session(
                        current_session_id,
                        telemetry["total_blinks"],
                        telemetry["avg_bpm"],
                        activity_tracker.current_activity.value
                    )
                eye_tracker.total_blinks = 0
                eye_tracker.blink_timestamps.clear()
                eye_tracker.session_start_time = time.time()
                current_session_id = db.start_session()
            elif action == "toggle_preview":
                settings["preview_enabled"] = not settings["preview_enabled"]
    except WebSocketDisconnect:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)


def generate_camera_frames():
    """Generates MJPEG stream for the frontend preview."""
    while True:
        if not settings["preview_enabled"] or eye_tracker.latest_annotated_frame is None:
            time.sleep(0.1)
            continue

        frame = eye_tracker.latest_annotated_frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.04)  # ~25 FPS


@app.get("/api/video_feed")
def video_feed():
    return StreamingResponse(
        generate_camera_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/api/stats/timeline")
def get_timeline():
    data = db.get_timeline_stats(current_session_id, limit=60)
    return JSONResponse(content={"timeline": data})


@app.get("/api/stats/activities")
def get_activities():
    data = db.get_activity_breakdown()
    return JSONResponse(content={"activities": data})


@app.get("/api/stats/today")
def get_today():
    data = db.get_today_summary()
    return JSONResponse(content=data)


@app.get("/api/settings")
def get_settings():
    return JSONResponse(content=settings)


@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    if req.sound_alerts is not None:
        settings["sound_alerts"] = req.sound_alerts
    if req.blink_delay_threshold is not None:
        settings["blink_delay_threshold"] = req.blink_delay_threshold
    if req.low_bpm_threshold is not None:
        settings["low_bpm_threshold"] = req.low_bpm_threshold
    if req.rule_20_20_20 is not None:
        settings["rule_20_20_20"] = req.rule_20_20_20
    if req.preview_enabled is not None:
        settings["preview_enabled"] = req.preview_enabled
    return JSONResponse(content=settings)


@app.post("/api/activity/override")
def override_activity(req: ActivityOverrideRequest):
    activity_tracker.set_manual_override(req.activity)
    return JSONResponse(content={"status": "ok", "override": req.activity})


# Mount static frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
