import sqlite3
import time
from typing import Dict, List, Optional
from datetime import datetime, date


DB_FILE = "eyetracker.db"


def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP,
        total_blinks INTEGER DEFAULT 0,
        avg_bpm REAL DEFAULT 0.0,
        primary_activity TEXT DEFAULT 'OTHER',
        duration_sec INTEGER DEFAULT 0,
        breaks_count INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS minute_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        blinks_count INTEGER DEFAULT 0,
        bpm REAL DEFAULT 0.0,
        activity TEXT DEFAULT 'OTHER',
        avg_ear REAL DEFAULT 0.0,
        process_name TEXT DEFAULT '',
        FOREIGN KEY (session_id) REFERENCES sessions (id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_activity_cache (
        day DATE,
        activity TEXT,
        total_seconds REAL DEFAULT 0,
        total_blinks INTEGER DEFAULT 0,
        PRIMARY KEY (day, activity)
    )
    """)

    # Safe migrations for existing databases
    for col, col_def in [("duration_sec", "INTEGER DEFAULT 0"), ("breaks_count", "INTEGER DEFAULT 0")]:
        try:
            cursor.execute(f"ALTER TABLE sessions ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass

    try:
        cursor.execute("ALTER TABLE minute_stats ADD COLUMN process_name TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


def start_session() -> int:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sessions (start_time) VALUES (CURRENT_TIMESTAMP)")
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id


def end_session(session_id: int, total_blinks: int, avg_bpm: float, primary_activity: str, duration_sec: int = 0, breaks_count: int = 0):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE sessions
        SET end_time = CURRENT_TIMESTAMP,
            total_blinks = ?,
            avg_bpm = ?,
            primary_activity = ?,
            duration_sec = ?,
            breaks_count = ?
        WHERE id = ?
    """, (total_blinks, avg_bpm, primary_activity, duration_sec, breaks_count, session_id))
    conn.commit()
    conn.close()


def record_minute_stat(session_id: int, blinks_count: int, bpm: float, activity: str, avg_ear: float, process_name: str = ""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO minute_stats (session_id, blinks_count, bpm, activity, avg_ear, process_name)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, blinks_count, bpm, activity, avg_ear, process_name))
    conn.commit()
    conn.close()


def get_timeline_stats(session_id: Optional[int] = None, limit: int = 60) -> List[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    if session_id:
        cursor.execute("""
            SELECT strftime('%H:%M:%S', timestamp) as time_str, blinks_count, bpm, activity, avg_ear
            FROM minute_stats
            WHERE session_id = ?
            ORDER BY id DESC LIMIT ?
        """, (session_id, limit))
    else:
        cursor.execute("""
            SELECT strftime('%H:%M:%S', timestamp) as time_str, blinks_count, bpm, activity, avg_ear
            FROM minute_stats
            ORDER BY id DESC LIMIT ?
        """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]


def get_activity_breakdown() -> List[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            activity,
            COUNT(*) as minutes_count,
            SUM(blinks_count) as total_blinks,
            AVG(bpm) as avg_bpm
        FROM minute_stats
        WHERE date(timestamp) = date('now', 'localtime')
        GROUP BY activity
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_today_summary() -> Dict:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COALESCE(SUM(blinks_count), 0) as total_blinks,
            COALESCE(AVG(bpm), 0.0) as avg_bpm,
            COUNT(*) as total_tracked_minutes
        FROM minute_stats
        WHERE date(timestamp) = date('now', 'localtime')
    """)
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {"total_blinks": 0, "avg_bpm": 0.0, "total_tracked_minutes": 0}


def get_eye_strain_ranking(days: int = 7) -> List[Dict]:
    """
    Returns application and activity categories ranked by eye strain level
    over the given period (default 7 days). Lower BPM = higher eye strain / dryness.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            activity,
            COALESCE(process_name, '') as process_name,
            COUNT(*) as minutes_count,
            SUM(blinks_count) as total_blinks,
            ROUND(AVG(bpm), 1) as avg_bpm
        FROM minute_stats
        WHERE timestamp >= datetime('now', '-' || ? || ' days', 'localtime')
        GROUP BY activity, process_name
        HAVING minutes_count > 0
        ORDER BY avg_bpm ASC, minutes_count DESC
    """, (days,))
    rows = cursor.fetchall()
    conn.close()

    ranking = []
    for r in rows:
        item = dict(r)
        avg_bpm = float(item["avg_bpm"] or 0.0)
        # Eye strain classification
        if avg_bpm >= 15.0:
            item["status"] = "EXCELLENT"
            item["badge_ua"] = "відмінно 🌿"
            item["badge_en"] = "excellent 🌿"
            item["color"] = "#8da775"  # sage green
        elif avg_bpm >= 10.0:
            item["status"] = "MODERATE"
            item["badge_ua"] = "помірний фокус 💻"
            item["badge_en"] = "moderate focus 💻"
            item["color"] = "#d9a877"  # warm latte
        else:
            item["status"] = "DRY_EYES"
            item["badge_ua"] = "очі пересихають ⚠️"
            item["badge_en"] = "eyes drying out ⚠️"
            item["color"] = "#cf6657"  # soft coral / rust
        ranking.append(item)

    return ranking


def get_weekly_history(limit_days: int = 7) -> Dict:
    """
    Returns day-by-day stats and summary for the last 7 days:
    screen time, blinks, average blink rate, and completed breaks count.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Query daily aggregates
    cursor.execute("""
        SELECT 
            date(m.timestamp) as day_date,
            COUNT(m.id) as tracked_minutes,
            SUM(m.blinks_count) as day_blinks,
            ROUND(AVG(m.bpm), 1) as day_avg_bpm
        FROM minute_stats m
        WHERE m.timestamp >= datetime('now', '-' || ? || ' days', 'localtime')
        GROUP BY date(m.timestamp)
        ORDER BY date(m.timestamp) DESC
    """, (limit_days,))
    day_rows = cursor.fetchall()

    # Query breaks per day from sessions table
    cursor.execute("""
        SELECT 
            date(start_time) as day_date,
            SUM(COALESCE(breaks_count, 0)) as day_breaks,
            SUM(COALESCE(duration_sec, 0)) as day_duration_sec
        FROM sessions
        WHERE start_time >= datetime('now', '-' || ? || ' days', 'localtime')
        GROUP BY date(start_time)
    """, (limit_days,))
    session_rows = {r["day_date"]: dict(r) for r in cursor.fetchall()}

    conn.close()

    daily_list = []
    total_week_minutes = 0
    total_week_blinks = 0
    total_week_breaks = 0
    total_bpm_acc = 0.0
    day_count = len(day_rows)

    for r in day_rows:
        day_date = r["day_date"]
        s_info = session_rows.get(day_date, {})
        day_breaks = int(s_info.get("day_breaks") or 0)
        day_dur_sec = int(s_info.get("day_duration_sec") or (r["tracked_minutes"] * 60))
        mins = max(r["tracked_minutes"], day_dur_sec // 60)
        blinks = int(r["day_blinks"] or 0)
        bpm = float(r["day_avg_bpm"] or 0.0)

        total_week_minutes += mins
        total_week_blinks += blinks
        total_week_breaks += day_breaks
        total_bpm_acc += bpm

        daily_list.append({
            "date": day_date,
            "minutes": mins,
            "formatted_time": f"{mins // 60}г {mins % 60:02d}хв" if mins >= 60 else f"{mins} хв",
            "blinks": blinks,
            "avg_bpm": bpm,
            "breaks_count": day_breaks
        })

    week_avg_bpm = round(total_bpm_acc / max(1, day_count), 1) if day_count > 0 else 0.0

    return {
        "daily": daily_list,
        "total_minutes": total_week_minutes,
        "formatted_total_time": f"{total_week_minutes // 60}г {total_week_minutes % 60:02d}хв" if total_week_minutes >= 60 else f"{total_week_minutes} хв",
        "total_blinks": total_week_blinks,
        "total_breaks": total_week_breaks,
        "week_avg_bpm": week_avg_bpm
    }
