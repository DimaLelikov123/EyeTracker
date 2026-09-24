import sys
import time
import psutil
from typing import Dict, Optional, Tuple
from enum import Enum

if sys.platform == "win32":
    try:
        import win32gui
        import win32process
    except ImportError:
        win32gui = None
        win32process = None
else:
    win32gui = None
    win32process = None


class ActivityType(str, Enum):
    GAMING = "GAMING"
    WORK = "WORK"
    VIDEO = "VIDEO"
    BROWSING = "BROWSING"
    SOCIAL = "SOCIAL"
    OTHER = "OTHER"


# Human-friendly titles and warm cozy colors for UI (Ukrainian & English)
ACTIVITY_META = {
    "UA": {
        ActivityType.GAMING: {"label": "Ігри", "icon": "🎮", "color": "#e07a5f"},
        ActivityType.WORK: {"label": "Робота / Код", "icon": "💻", "color": "#88a070"},
        ActivityType.VIDEO: {"label": "Кіно / Відео", "icon": "🎬", "color": "#e0a96d"},
        ActivityType.BROWSING: {"label": "Браузинг", "icon": "🌐", "color": "#86a789"},
        ActivityType.SOCIAL: {"label": "Спілкування", "icon": "💬", "color": "#c4a482"},
        ActivityType.OTHER: {"label": "Фонове завдання", "icon": "☕", "color": "#b08968"},
    },
    "EN": {
        ActivityType.GAMING: {"label": "Gaming", "icon": "🎮", "color": "#e07a5f"},
        ActivityType.WORK: {"label": "Work / Coding", "icon": "💻", "color": "#88a070"},
        ActivityType.VIDEO: {"label": "Movies / Video", "icon": "🎬", "color": "#e0a96d"},
        ActivityType.BROWSING: {"label": "Browsing", "icon": "🌐", "color": "#86a789"},
        ActivityType.SOCIAL: {"label": "Chat / Social", "icon": "💬", "color": "#c4a482"},
        ActivityType.OTHER: {"label": "Background Task", "icon": "☕", "color": "#b08968"},
    }
}

# Known process mappings
KNOWN_PROCESSES = {
    # Work & Coding
    "code.exe": ActivityType.WORK,
    "devenv.exe": ActivityType.WORK,
    "pycharm64.exe": ActivityType.WORK,
    "idea64.exe": ActivityType.WORK,
    "sublime_text.exe": ActivityType.WORK,
    "notepad++.exe": ActivityType.WORK,
    "windowsterminal.exe": ActivityType.WORK,
    "powershell.exe": ActivityType.WORK,
    "cmd.exe": ActivityType.WORK,
    "winword.exe": ActivityType.WORK,
    "excel.exe": ActivityType.WORK,
    "powerpnt.exe": ActivityType.WORK,
    "acrobat.exe": ActivityType.WORK,
    "notion.exe": ActivityType.WORK,
    "figma.exe": ActivityType.WORK,
    "obsidian.exe": ActivityType.WORK,
    "datagrip64.exe": ActivityType.WORK,

    # Social & Chat
    "telegram.exe": ActivityType.SOCIAL,
    "discord.exe": ActivityType.SOCIAL,
    "slack.exe": ActivityType.SOCIAL,
    "whatsapp.exe": ActivityType.SOCIAL,
    "skype.exe": ActivityType.SOCIAL,
    "teams.exe": ActivityType.SOCIAL,

    # Video Players
    "vlc.exe": ActivityType.VIDEO,
    "mpc-hc.exe": ActivityType.VIDEO,
    "mpc-hc64.exe": ActivityType.VIDEO,
    "potplayermini64.exe": ActivityType.VIDEO,
    "kmplayer.exe": ActivityType.VIDEO,
    "netflix.exe": ActivityType.VIDEO,

    # Games & Launchers
    "steam.exe": ActivityType.GAMING,
    "epicgameslauncher.exe": ActivityType.GAMING,
    "cs2.exe": ActivityType.GAMING,
    "dota2.exe": ActivityType.GAMING,
    "valorant.exe": ActivityType.GAMING,
    "league of legends.exe": ActivityType.GAMING,
    "javaw.exe": ActivityType.GAMING,  # Minecraft often uses javaw
    "genshinimpact.exe": ActivityType.GAMING,
    "overwatch.exe": ActivityType.GAMING,
    "gta5.exe": ActivityType.GAMING,
}

# Video keywords inside browser titles
VIDEO_TITLE_KEYWORDS = [
    "youtube", "netflix", "twitch", "кинопоиск", "kinopoisk",
    "anime", "аниме", "film", "фильм", "сериал", "vimeo",
    "rutube", "плеер", "player", "смотреть онлайн"
]

# Work keywords inside browser titles
WORK_TITLE_KEYWORDS = [
    "github", "gitlab", "stackoverflow", "stack overflow",
    "jira", "confluence", "google docs", "google sheets",
    "docs", "documentation", "notion"
]

BROWSER_PROCESSES = {
    "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe", "vivaldi.exe"
}


class ActivityTracker:
    def __init__(self):
        self.current_activity: ActivityType = ActivityType.OTHER
        self.current_window_title: str = ""
        self.current_process_name: str = ""
        self.manual_override: Optional[ActivityType] = None
        self.last_check_time: float = time.time()
        self.activity_durations: Dict[str, float] = {act.value: 0.0 for act in ActivityType}

        # Fast memory caches to eliminate repeated Win32 / psutil OS handle allocations
        self._pid_name_cache: Dict[int, str] = {}
        self._last_hwnd = None
        self._last_pid = None
        self._last_proc_name = "unknown"
        self._last_title = ""
        self._last_hwnd_check = 0.0
        self._cached_act_info: Optional[Dict] = None

    def set_manual_override(self, activity: Optional[str]):
        if activity and activity in ActivityType.__members__:
            self.manual_override = ActivityType(activity)
        else:
            self.manual_override = None
        self._cached_act_info = None

    def get_foreground_window_info(self) -> Tuple[str, str]:
        """Returns (process_name, window_title) for the active window with high-speed caching."""
        now = time.time()
        try:
            if sys.platform == "win32" and win32gui is not None:
                hwnd = win32gui.GetForegroundWindow()
                if not hwnd:
                    return ("unknown", "Desktop / No Active Window")

                # Avoid re-querying title and process if same HWND was queried less than 400ms ago
                if hwnd == self._last_hwnd and (now - self._last_hwnd_check) < 0.4:
                    return (self._last_proc_name, self._last_title)

                self._last_hwnd = hwnd
                self._last_hwnd_check = now

                title = win32gui.GetWindowText(hwnd) or ""
                self._last_title = title

                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid:
                    if pid == self._last_pid and self._last_proc_name not in ("unknown", "error"):
                        return (self._last_proc_name, title)

                    self._last_pid = pid
                    cached_name = self._pid_name_cache.get(pid)
                    if cached_name is not None:
                        self._last_proc_name = cached_name
                        return (cached_name, title)

                    try:
                        proc = psutil.Process(pid)
                        proc_name = proc.name().lower()
                        if len(self._pid_name_cache) > 256:
                            self._pid_name_cache.clear()
                        self._pid_name_cache[pid] = proc_name
                        self._last_proc_name = proc_name
                        return (proc_name, title)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        self._last_proc_name = "system"
                        return ("system", title)

                return ("unknown", title)

            elif sys.platform == "darwin":
                # macOS support
                try:
                    from AppKit import NSWorkspace
                    active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
                    if active_app:
                        name = active_app.localizedName().lower()
                        return (name, active_app.localizedName())
                except Exception:
                    pass
                return ("desktop", "macOS Active Window")

            elif sys.platform.startswith("linux"):
                # Linux support (via xdotool if installed, or fallback)
                try:
                    import subprocess
                    out = subprocess.check_output(["xdotool", "getactivewindow", "getwindowname"], timeout=0.3).decode("utf-8", errors="ignore").strip()
                    if out:
                        return ("desktop", out)
                except Exception:
                    pass
                return ("desktop", "Linux Active Window")

            return ("unknown", "Desktop / Active Window")
        except Exception as e:
            return ("error", str(e))

    def classify_activity(self, proc_name: str, title: str) -> ActivityType:
        """Determines activity category based on process name and window title."""
        if self.manual_override:
            return self.manual_override

        proc_lower = proc_name.lower()
        title_lower = title.lower()

        # 1. Check known process mappings
        if proc_lower in KNOWN_PROCESSES:
            return KNOWN_PROCESSES[proc_lower]

        # 2. Check browsers (differentiate between video, work, and general browsing)
        if proc_lower in BROWSER_PROCESSES:
            for kw in VIDEO_TITLE_KEYWORDS:
                if kw in title_lower:
                    return ActivityType.VIDEO
            for kw in WORK_TITLE_KEYWORDS:
                if kw in title_lower:
                    return ActivityType.WORK
            return ActivityType.BROWSING

        # 3. Check for game launchers / fullscreen game hints
        if any(g in proc_lower for g in ["game", "steam", "unreal", "unity"]):
            return ActivityType.GAMING

        # 4. Fallback based on title
        for kw in VIDEO_TITLE_KEYWORDS:
            if kw in title_lower:
                return ActivityType.VIDEO

        if any(w in title_lower for w in ["visual studio", "terminal", "bash", "python", "debug"]):
            return ActivityType.WORK

        return ActivityType.OTHER

    def update(self, lang: str = "UA") -> Dict:
        """Polls current foreground window and updates duration accumulation."""
        now = time.time()
        elapsed = max(0.0, now - self.last_check_time)
        self.last_check_time = now

        proc_name, title = self.get_foreground_window_info()
        self.current_process_name = proc_name
        self.current_window_title = title

        activity = self.classify_activity(proc_name, title)
        self.current_activity = activity
        self.activity_durations[activity.value] += elapsed

        lang_key = "EN" if lang.upper() == "EN" else "UA"
        palette = ACTIVITY_META.get(lang_key, ACTIVITY_META["UA"])
        meta = palette.get(activity, palette[ActivityType.OTHER])

        info = {
            "activity": activity.value,
            "label": meta["label"],
            "icon": meta["icon"],
            "color": meta["color"],
            "process": proc_name,
            "title": title[:80] + "..." if len(title) > 80 else title,
            "manual_override": self.manual_override.value if self.manual_override else None,
            "durations": self.activity_durations
        }
        self._cached_act_info = info
        return info

    def get_cached_info(self, lang: str = "UA") -> Dict:
        """Returns the latest cached activity info in <0.001 ms with zero OS calls."""
        if not self._cached_act_info:
            return self.update(lang)

        lang_key = "EN" if lang.upper() == "EN" else "UA"
        palette = ACTIVITY_META.get(lang_key, ACTIVITY_META["UA"])
        meta = palette.get(self.current_activity, palette[ActivityType.OTHER])

        # Return updated localized labels
        self._cached_act_info["label"] = meta["label"]
        self._cached_act_info["icon"] = meta["icon"]
        self._cached_act_info["color"] = meta["color"]
        return self._cached_act_info
