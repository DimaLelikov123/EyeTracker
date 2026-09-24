import sys
import time
import threading
import os
import json
from datetime import datetime
from typing import Tuple, Dict, List, Optional
import tkinter as tk
import customtkinter as ctk

# Cross-platform conditional imports
if sys.platform == "win32":
    try:
        import win32gui
        import win32con
    except ImportError:
        win32gui = None
        win32con = None
    try:
        from win11toast import toast
    except ImportError:
        toast = None
else:
    win32gui = None
    win32con = None
    toast = None

# Ensure UTF-8 output for console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


def open_folder_cross_platform(folder_path: str):
    """Opens a folder in default system file manager (Explorer, Finder, or Linux file manager)."""
    abs_path = os.path.abspath(folder_path)
    os.makedirs(abs_path, exist_ok=True)
    try:
        if sys.platform == "win32":
            os.startfile(abs_path)
        elif sys.platform == "darwin":
            import subprocess
            subprocess.run(["open", abs_path], check=False)
        else:
            import subprocess
            subprocess.run(["xdg-open", abs_path], check=False)
    except Exception as e:
        print(f"[Open Folder Error] {e}")

import db
from eye_tracker import EyeTracker
from activity_tracker import ActivityTracker, ActivityType, ACTIVITY_META

# Warm Cozy Aesthetic Palette (Fields of Mistria inspired)
COZY_PALETTE = {
    "bg": "#181513",              # Deep warm espresso
    "card": "#241f1c",            # Warm cocoa card background
    "card_alt": "#2d2621",        # Slightly lighter warm panel / slot
    "border": "#46392f",          # Crisp warm wooden frame border
    "border_light": "#5c493c",    # Subtle highlight border
    "text_main": "#f6eee3",        # Warm cream text
    "text_muted": "#aba092",       # Soft warm gray/beige
    "text_dim": "#7d7266",         # Dim coffee text
    "accent_primary": "#d48144",   # Warm terracotta / caramel
    "accent_hover": "#be6e33",     # Darker warm caramel
    "accent_stop": "#ba5444",      # Soft rust terracotta for stop
    "accent_stop_hover": "#a54536",
    "sage_green": "#8da775",       # Gentle matcha / sage for normal status
    "warm_latte": "#d9a877",       # Warm screen normal
    "soft_coral": "#cf6657",       # Warm gentle warning
    "alert_bg": "#3d221e",         # Cozy deep rust banner
    "alert_border": "#874338",
}

# Complete Ukrainian & English Localizations (Russian removed)
TRANSLATIONS = {
    "UA": {
        "title": "EyeTracker — Турбота про ваш зір ☕",
        "app_name": "✦ EyeTracker ✦",
        "tagline": "Мінімалістичний трекер кліпань",
        "btn_start": "✦  Запустити",
        "btn_stop": "⏹  Зупинити",
        "btn_test": "✨",
        "btn_sessions": "📊",
        "btn_sessions_tooltip": "Історія та рейтинг навантаження",
        "reminders": "Нагадування",
        "alert_text": "🕯️ Час розім'яти очі: погляньте вдаль на 20–30 секунд та зробіть легку розминку ✨",
        "btn_blinked": "Відпочив ✨",
        "camera_label": "📷 Камера:",
        "break_label": "🌿 Розминка:",
        "break_options": ["15 хв", "30 хв (рекомендовано)", "45 хв", "60 хв (1 год)"],
        "default_camera": "0: Основна камера",
        "bpm_title": "✦ ТЕМП КЛІПАНЬ ✦",
        "bpm_unit": " кліпань на хвилину (норма: 15–20)",
        "bpm_unit_short": "кліп/хв",
        "health_ready": "🌿 Натисніть «Запустити», щоб розпочати дбайливий трекінг",
        "health_healthy": "🌿 Очі зволожені та розслаблені",
        "health_moderate": "💻 Помірний екранний фокус",
        "health_fatigue": "☕ Очі втомлюються: зробіть коротку паузу",
        "health_no_face": "👀 Обличчя поки не в кадрі",
        "cam_waiting": "Камера очікує старту",
        "cam_connecting": "Підключення...",
        "cam_not_found": "❌ Камеру не знайдено",
        "cam_active": "🟢 Трекінг активний",
        "cam_looking": "👀 Пошук обличчя",
        "cam_in_frame": "🟢 Погляд у кадрі",
        "cam_stopped": "Зупинено",
        "cam_selected": "Камера #{idx} обрана",
        "cam_paused": "⏸️ На паузі",
        "auto_paused": "☕ Автопауза: ви відійшли від ПК",
        "auto_resumed": "🌿 З поверненням! Трекінг відновлено ✨",
        "activity_title": "✦ ПОТОЧНЕ ЗАНЯТТЯ ✦",
        "activity_modes": ["🤖 Авто", "💻 Робота", "🎮 Ігри", "🎬 Відео", "🌐 Серфінг", "💬 Чат"],
        "activity_waiting": "Очікування активного вікна...",
        "desktop": "Робочий стіл",
        "metric_total": "✦ Кліпання",
        "metric_pause": "✦ Пауза",
        "metric_session": "✦ Сесія",
        "footer_note": "🌿 Камера працює у фоні без показу відео. Нагадування розминки з'являються тихо через вибраний інтервал.",
        "toast_break_title": "EyeTracker 🌿 Розминка для очей",
        "toast_break_msg": "Минуло {mins} хв! За цей час ви кліпнули {blinks} разів ({bpm} кліп/хв). Погляньте вдаль на 20-30 с та розімніть очі ☕",
        "toast_test_title": "EyeTracker 🌿 Тест розминки",
        "toast_test_msg": "Тестове нагадування: за {mins} хв зафіксовано {blinks} кліпань ({bpm} кліп/хв). Час перевести погляд вдаль ✨",
        "in_app_break": "🌿 Час розім'яти очі: {mins} хв за екраном, {blinks} кліпань ({bpm} кліп/хв). Погляньте вдаль на 20-30 с ✨",
        "modal_session_title": "☕ Підсумок сесії",
        "modal_session_saved": "Сесію збережено у файл:",
        "modal_total_time": "Час сесії:",
        "modal_total_blinks": "Всього кліпань:",
        "modal_avg_rate": "Середній темп:",
        "modal_activity_col": "Активність",
        "modal_duration_col": "Тривалість",
        "modal_blinks_col": "Кліпань",
        "modal_rate_col": "Темп (кліп/хв)",
        "modal_btn_open_folder": "📂 Відкрити папку сесій",
        "modal_btn_close": "Зрозуміло ✨",
        "toast_session_saved": "Сесію збережено! Натисніть «Сесії» для перегляду.",
        "modal_history_title": "☕ Історія та навантаження на очі",
        "modal_history_subtitle": "Аналітика за останні 7 днів та поденна історія",
        "tab_ranking": "🏆 Рейтинг навантаження",
        "tab_history": "📅 Тижневий звіт",
        "stat_week_time": "Час за 7 днів:",
        "stat_week_rate": "Середній темп:",
        "stat_week_breaks": "Виконано розминок:",
        "ranking_app_col": "Додаток / Заняття",
        "ranking_time_col": "Час",
        "ranking_rate_col": "Темп кліпань",
        "ranking_status_col": "Стан очей",
        "history_date_col": "Дата",
        "history_time_col": "Екранний час",
        "history_blinks_col": "Кліпань",
        "history_rate_col": "Темп (кліп/хв)",
        "history_breaks_col": "Розминки",
        "today": "Сьогодні",
        "yesterday": "Вчора",
        "no_ranking_data": "🌿 Поки що немає записів. Попрацюйте з трекером, щоб побачити рейтинг додатків!",
        "no_history_data": "🌿 Історія за попередні дні поки що порожня. Завершіть першу сесію!",
        "btn_open_sessions_folder": "📂 Папка сесій",
    },
    "EN": {
        "title": "EyeTracker — Gentle Care for Your Eyes ☕",
        "app_name": "✦ EyeTracker ✦",
        "tagline": "Minimalist blink tracker",
        "btn_start": "✦  Start",
        "btn_stop": "⏹  Stop",
        "btn_test": "✨",
        "btn_sessions": "📊",
        "btn_sessions_tooltip": "History & Eye Load Analytics",
        "reminders": "Reminders",
        "alert_text": "🕯️ Time for an eye break: look into the distance for 20–30 seconds and stretch your eyes ✨",
        "btn_blinked": "Rested ✨",
        "camera_label": "📷 Camera:",
        "break_label": "🌿 Eye Break:",
        "break_options": ["15 min", "30 min (recommended)", "45 min", "60 min (1 hr)"],
        "default_camera": "0: Primary Camera",
        "bpm_title": "✦ BLINK RATE ✦",
        "bpm_unit": " blinks per minute (norm: 15–20)",
        "bpm_unit_short": "bpm",
        "health_ready": "🌿 Click 'Start' to begin gentle tracking",
        "health_healthy": "🌿 Eyes are moisturized and relaxed",
        "health_moderate": "💻 Moderate screen focus",
        "health_fatigue": "☕ Eye fatigue: take a short break",
        "health_no_face": "👀 Face not detected yet",
        "cam_waiting": "Camera waiting for start",
        "cam_connecting": "Connecting...",
        "cam_not_found": "❌ Camera not found",
        "cam_active": "🟢 Tracking active",
        "cam_looking": "👀 Searching for face",
        "cam_in_frame": "🟢 Face detected",
        "cam_stopped": "Stopped",
        "cam_selected": "Camera #{idx} selected",
        "cam_paused": "⏸️ Paused",
        "auto_paused": "☕ Auto-paused: away from PC",
        "auto_resumed": "🌿 Welcome back! Tracking resumed ✨",
        "activity_title": "✦ CURRENT ACTIVITY ✦",
        "activity_modes": ["🤖 Auto", "💻 Work", "🎮 Gaming", "🎬 Video", "🌐 Browsing", "💬 Chat"],
        "activity_waiting": "Waiting for active window...",
        "desktop": "Desktop",
        "metric_total": "✦ Blinks",
        "metric_pause": "✦ Pause",
        "metric_session": "✦ Session",
        "footer_note": "🌿 Camera runs in background without video. Eye break reminders appear silently at selected intervals.",
        "toast_break_title": "EyeTracker 🌿 Eye Stretch Break",
        "toast_break_msg": "It's been {mins} min! You blinked {blinks} times ({bpm} bpm). Look into the distance for 20-30 s and stretch your eyes ☕",
        "toast_test_title": "EyeTracker 🌿 Break Test",
        "toast_test_msg": "Test reminder: {blinks} blinks tracked over {mins} min ({bpm} bpm). Time to look into the distance ✨",
        "in_app_break": "🌿 Time for an eye break: {mins} min on screen, {blinks} blinks ({bpm} bpm). Look into the distance ✨",
        "modal_session_title": "☕ Session Summary",
        "modal_session_saved": "Session saved to file:",
        "modal_total_time": "Session Duration:",
        "modal_total_blinks": "Total Blinks:",
        "modal_avg_rate": "Average Rate:",
        "modal_activity_col": "Activity",
        "modal_duration_col": "Duration",
        "modal_blinks_col": "Blinks",
        "modal_rate_col": "Rate (bpm)",
        "modal_btn_open_folder": "📂 Open Sessions Folder",
        "modal_btn_close": "Got it ✨",
        "toast_session_saved": "Session saved! Click 'Sessions' to view.",
        "modal_history_title": "☕ History & Eye Load Analytics",
        "modal_history_subtitle": "Analytics for the last 7 days and daily history",
        "tab_ranking": "🏆 Eye Strain Ranking",
        "tab_history": "📅 Weekly Report",
        "stat_week_time": "7-Day Screen Time:",
        "stat_week_rate": "Average Rate:",
        "stat_week_breaks": "Completed Breaks:",
        "ranking_app_col": "App / Activity",
        "ranking_time_col": "Time",
        "ranking_rate_col": "Blink Rate",
        "ranking_status_col": "Eye Strain",
        "history_date_col": "Date",
        "history_time_col": "Screen Time",
        "history_blinks_col": "Blinks",
        "history_rate_col": "Rate (bpm)",
        "history_breaks_col": "Breaks",
        "today": "Today",
        "yesterday": "Yesterday",
        "no_ranking_data": "🌿 No records yet. Use applications with tracker active to view ranking!",
        "no_history_data": "🌿 Daily history is empty yet. Complete your first session!",
        "btn_open_sessions_folder": "📂 Sessions Folder",
    }
}


def get_available_cameras(lang: str = "UA"):
    """Detects available camera devices with friendly names."""
    devices = []
    try:
        from pygrabber.dshow_graph import FilterGraph
        names = FilterGraph().get_input_devices()
        for idx, name in enumerate(names):
            devices.append(f"{idx}: {name}")
    except Exception:
        pass
    if not devices:
        def_name = TRANSLATIONS[lang]["default_camera"]
        devices = [def_name]
    return devices


def generate_session_txt(session_data: dict, lang: str = "UA") -> str:
    """Generates a warm, human-readable session summary in pure UTF-8."""
    is_ua = (lang == "UA")
    sep = "=" * 54
    subsep = "-" * 54

    title = "☕ EyeTracker — Звіт сесії" if is_ua else "☕ EyeTracker — Session Report"
    lbl_date = "Дата:" if is_ua else "Date:"
    lbl_start = "Початок:" if is_ua else "Start Time:"
    lbl_end = "Завершення:" if is_ua else "End Time:"
    lbl_dur = "Тривалість:" if is_ua else "Duration:"
    lbl_blinks = "Всього кліпань:" if is_ua else "Total Blinks:"
    lbl_bpm = "Середній темп:" if is_ua else "Average Rate:"
    lbl_norm = "кліп/хв (норма: 15–20)" if is_ua else "blinks/min (norm: 15–20)"
    lbl_breakdown = "РОЗПОДІЛ ЗА АКТИВНІСТЮ:" if is_ua else "ACTIVITY BREAKDOWN:"
    lbl_footer = "🌿 Дбайливий догляд за вашим зором" if is_ua else "🌿 Gentle care for your eyes"

    lines = [
        sep,
        title,
        sep,
        f"{lbl_date:<24} {session_data.get('date', '')}",
        f"{lbl_start:<24} {session_data.get('start_time', '')}",
        f"{lbl_end:<24} {session_data.get('end_time', '')}",
        f"{lbl_dur:<24} {session_data.get('total_duration_formatted', '')} ({session_data.get('total_duration_sec', 0)} с)",
        f"{lbl_blinks:<24} {session_data.get('total_blinks', 0)}",
        f"{lbl_bpm:<24} {session_data.get('average_bpm', 0.0)} {lbl_norm}",
        "",
        subsep,
        lbl_breakdown,
        subsep,
    ]

    for act in session_data.get("activities", []):
        act_name = act.get("label_ua" if is_ua else "label_en") or act.get("label", act.get("activity"))
        icon = act.get("icon", "☕")
        dur = act.get("duration_formatted", "00:00")
        dur_s = act.get("duration_sec", 0)
        blinks = act.get("blinks", 0)
        bpm = act.get("bpm", 0.0)

        lines.append(f"  {icon} {act_name} ({act.get('activity')}):")
        if is_ua:
            lines.append(f"     • Тривалість: {dur} ({dur_s} с)")
            lines.append(f"     • Кліпань:    {blinks}")
            lines.append(f"     • Темп:       {bpm:.1f} кліп/хв")
        else:
            lines.append(f"     • Duration:   {dur} ({dur_s} s)")
            lines.append(f"     • Blinks:     {blinks}")
            lines.append(f"     • Rate:       {bpm:.1f} bpm")
        lines.append("")

    lines.append(sep)
    lines.append(lbl_footer)
    lines.append(sep)
    return "\n".join(lines)


class SessionSummaryModal(ctk.CTkToplevel):
    """Cozy dialog displaying session breakdown per activity."""
    def __init__(self, parent, session_data: dict, json_path: str, txt_path: str, lang: str = "UA"):
        super().__init__(parent)
        self.parent = parent
        self.session_data = session_data
        self.json_path = json_path
        self.txt_path = txt_path
        self.lang = lang
        self.t = TRANSLATIONS[lang]

        self.title(self.t["modal_session_title"])
        self.geometry("560x520")
        self.minsize(500, 440)
        self.configure(fg_color=COZY_PALETTE["bg"])

        # Center dialog over parent window
        try:
            self.update_idletasks()
            px = parent.winfo_x()
            py = parent.winfo_y()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            x = px + max(0, (pw - 560) // 2)
            y = py + max(0, (ph - 520) // 2)
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))
        self.focus_force()

        # Set modal icon
        ico_path = resource_path(os.path.join("assets", "icon.ico"))
        if sys.platform == "win32" and os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

        self._build_ui()

    def _build_ui(self):
        # 1. Header Card
        card_top = ctk.CTkFrame(
            self,
            corner_radius=14,
            fg_color=COZY_PALETTE["card"],
            border_color=COZY_PALETTE["border"],
            border_width=2
        )
        card_top.pack(fill="x", padx=16, pady=(14, 8))

        lbl_head = ctk.CTkLabel(
            card_top,
            text=self.t["modal_session_title"],
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COZY_PALETTE["text_main"]
        )
        lbl_head.pack(anchor="w", padx=14, pady=(10, 2))

        txt_name = os.path.basename(self.txt_path)
        lbl_file = ctk.CTkLabel(
            card_top,
            text=f"💾 {self.t['modal_session_saved']} {txt_name}",
            font=ctk.CTkFont(size=11),
            text_color=COZY_PALETTE["sage_green"]
        )
        lbl_file.pack(anchor="w", padx=14, pady=(0, 10))

        # 2. Key Metrics Row (3 cards)
        metrics_row = ctk.CTkFrame(self, fg_color="transparent")
        metrics_row.pack(fill="x", padx=16, pady=4)

        # A: Duration
        dur_card = ctk.CTkFrame(metrics_row, corner_radius=10, fg_color=COZY_PALETTE["card"], border_color=COZY_PALETTE["border"], border_width=1)
        dur_card.pack(side="left", fill="both", expand=True, padx=(0, 4))
        ctk.CTkLabel(dur_card, text=self.t["modal_total_time"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"]).pack(pady=(6, 1))
        ctk.CTkLabel(dur_card, text=self.session_data.get("total_duration_formatted", "00:00"), font=ctk.CTkFont(size=18, weight="bold"), text_color=COZY_PALETTE["text_main"]).pack(pady=(0, 6))

        # B: Total Blinks
        blinks_card = ctk.CTkFrame(metrics_row, corner_radius=10, fg_color=COZY_PALETTE["card"], border_color=COZY_PALETTE["border"], border_width=1)
        blinks_card.pack(side="left", fill="both", expand=True, padx=4)
        ctk.CTkLabel(blinks_card, text=self.t["modal_total_blinks"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"]).pack(pady=(6, 1))
        ctk.CTkLabel(blinks_card, text=str(self.session_data.get("total_blinks", 0)), font=ctk.CTkFont(size=18, weight="bold"), text_color=COZY_PALETTE["text_main"]).pack(pady=(0, 6))

        # C: Average BPM
        rate_card = ctk.CTkFrame(metrics_row, corner_radius=10, fg_color=COZY_PALETTE["card"], border_color=COZY_PALETTE["border"], border_width=1)
        rate_card.pack(side="left", fill="both", expand=True, padx=(4, 0))
        ctk.CTkLabel(rate_card, text=self.t["modal_avg_rate"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"]).pack(pady=(6, 1))
        ctk.CTkLabel(rate_card, text=f"{self.session_data.get('average_bpm', 0.0)}", font=ctk.CTkFont(size=18, weight="bold"), text_color=COZY_PALETTE["text_main"]).pack(pady=(0, 6))

        # 3. Activities Breakdown Scrollable List
        act_card = ctk.CTkFrame(
            self,
            corner_radius=14,
            fg_color=COZY_PALETTE["card"],
            border_color=COZY_PALETTE["border"],
            border_width=2
        )
        act_card.pack(fill="both", expand=True, padx=16, pady=8)

        # Table header
        tbl_head = ctk.CTkFrame(act_card, fg_color="transparent")
        tbl_head.pack(fill="x", padx=14, pady=(10, 4))

        ctk.CTkLabel(tbl_head, text=self.t["modal_activity_col"], font=ctk.CTkFont(size=11, weight="bold"), text_color=COZY_PALETTE["text_muted"]).pack(side="left")

        stat_header_right = ctk.CTkFrame(tbl_head, fg_color="transparent")
        stat_header_right.pack(side="right")
        ctk.CTkLabel(stat_header_right, text=self.t["modal_duration_col"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"], width=75, anchor="e").pack(side="left", padx=4)
        ctk.CTkLabel(stat_header_right, text=self.t["modal_blinks_col"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"], width=65, anchor="e").pack(side="left", padx=4)
        ctk.CTkLabel(stat_header_right, text=self.t["modal_rate_col"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"], width=85, anchor="e").pack(side="left", padx=4)

        scroll_frame = ctk.CTkScrollableFrame(
            act_card,
            fg_color="transparent",
            scrollbar_button_color=COZY_PALETTE["border"],
            scrollbar_button_hover_color=COZY_PALETTE["accent_primary"]
        )
        scroll_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        activities = self.session_data.get("activities", [])
        if not activities:
            ctk.CTkLabel(
                scroll_frame,
                text="—",
                font=ctk.CTkFont(size=12),
                text_color=COZY_PALETTE["text_dim"]
            ).pack(pady=20)
        else:
            for act in activities:
                row = ctk.CTkFrame(scroll_frame, fg_color=COZY_PALETTE["card_alt"], border_color=COZY_PALETTE["border"], border_width=1, corner_radius=8, height=36)
                row.pack(fill="x", pady=3)

                label_text = act.get("label_ua" if self.lang == "UA" else "label_en") or act.get("label", act.get("activity", ""))
                icon = act.get("icon", "☕")

                left_box = ctk.CTkFrame(row, fg_color="transparent")
                left_box.pack(side="left", padx=10, pady=6)
                ctk.CTkLabel(left_box, text=f"{icon} {label_text}", font=ctk.CTkFont(size=11, weight="bold"), text_color=COZY_PALETTE["text_main"]).pack(side="left")

                right_box = ctk.CTkFrame(row, fg_color="transparent")
                right_box.pack(side="right", padx=10, pady=6)

                dur_str = act.get("duration_formatted", "00:00")
                blinks_str = str(act.get("blinks", 0))
                bpm_str = f"{act.get('bpm', 0.0):.1f}"

                ctk.CTkLabel(right_box, text=dur_str, font=ctk.CTkFont(size=11), text_color=COZY_PALETTE["text_muted"], width=75, anchor="e").pack(side="left", padx=4)
                ctk.CTkLabel(right_box, text=blinks_str, font=ctk.CTkFont(size=11, weight="bold"), text_color=COZY_PALETTE["accent_primary"], width=65, anchor="e").pack(side="left", padx=4)
                ctk.CTkLabel(right_box, text=bpm_str, font=ctk.CTkFont(size=11), text_color=COZY_PALETTE["text_main"], width=85, anchor="e").pack(side="left", padx=4)

        # 4. Bottom Button Bar
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=(0, 14))

        btn_open = ctk.CTkButton(
            btn_bar,
            text=self.t["modal_btn_open_folder"],
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COZY_PALETTE["card"],
            hover_color=COZY_PALETTE["card_alt"],
            border_color=COZY_PALETTE["border"],
            border_width=1,
            text_color=COZY_PALETTE["text_main"],
            height=34,
            corner_radius=12,
            command=self._open_folder
        )
        btn_open.pack(side="left")

        btn_close = ctk.CTkButton(
            btn_bar,
            text=self.t["modal_btn_close"],
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COZY_PALETTE["accent_primary"],
            hover_color=COZY_PALETTE["accent_hover"],
            border_color=COZY_PALETTE["border_light"],
            border_width=1,
            text_color="#ffffff",
            width=110,
            height=34,
            corner_radius=12,
            command=self.destroy
        )
        btn_close.pack(side="right")

    def _open_folder(self):
        sessions_dir = os.path.dirname(os.path.abspath(self.txt_path))
        open_folder_cross_platform(sessions_dir)


def get_friendly_app_label(activity_str: str, process_name: str, lang: str = "UA") -> Tuple[str, str]:
    """Returns (icon, human-friendly label) for an app or activity."""
    proc = process_name.lower().strip() if process_name else ""
    is_ua = (lang == "UA")

    PROC_NAMES = {
        "chrome.exe": ("🌐", "Google Chrome"),
        "msedge.exe": ("🌐", "Microsoft Edge"),
        "firefox.exe": ("🌐", "Mozilla Firefox"),
        "brave.exe": ("🌐", "Brave Browser"),
        "opera.exe": ("🌐", "Opera Browser"),
        "code.exe": ("💻", "Visual Studio Code"),
        "pycharm64.exe": ("💻", "PyCharm"),
        "idea64.exe": ("💻", "IntelliJ IDEA"),
        "devenv.exe": ("💻", "Visual Studio"),
        "sublime_text.exe": ("💻", "Sublime Text"),
        "windowsterminal.exe": ("💻", "Windows Terminal"),
        "powershell.exe": ("💻", "PowerShell"),
        "winword.exe": ("💻", "Microsoft Word"),
        "excel.exe": ("💻", "Microsoft Excel"),
        "notion.exe": ("💻", "Notion"),
        "telegram.exe": ("💬", "Telegram"),
        "discord.exe": ("💬", "Discord"),
        "slack.exe": ("💬", "Slack"),
        "vlc.exe": ("🎬", "VLC Player"),
        "cs2.exe": ("🎮", "Counter-Strike 2"),
        "dota2.exe": ("🎮", "Dota 2"),
        "steam.exe": ("🎮", "Steam"),
        "valorant.exe": ("🎮", "Valorant"),
    }

    if proc in PROC_NAMES:
        return PROC_NAMES[proc]

    try:
        act_enum = ActivityType(activity_str)
        meta = ACTIVITY_META.get(lang, ACTIVITY_META["UA"]).get(act_enum, {})
        label = meta.get("label", activity_str)
        icon = meta.get("icon", "☕")
        if proc:
            label = f"{label} ({proc})"
        return icon, label
    except Exception:
        name = proc if proc else (activity_str or ("Інше" if is_ua else "Other"))
        return "☕", name


class HistoryAnalyticsModal(ctk.CTkToplevel):
    """Cozy dialog displaying 7-day eye load app ranking and daily/weekly history."""
    def __init__(self, parent, lang: str = "UA"):
        super().__init__(parent)
        self.parent = parent
        self.lang = lang
        self.t = TRANSLATIONS[lang]

        self.title(self.t["modal_history_title"])
        self.geometry("630x580")
        self.minsize(560, 480)
        self.configure(fg_color=COZY_PALETTE["bg"])

        # Center dialog over parent window
        try:
            self.update_idletasks()
            px = parent.winfo_x()
            py = parent.winfo_y()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            x = px + max(0, (pw - 630) // 2)
            y = py + max(0, (ph - 580) // 2)
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))
        self.focus_force()

        # Set modal icon
        ico_path = resource_path(os.path.join("assets", "icon.ico"))
        if sys.platform == "win32" and os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

        # Fetch data
        self.ranking_data = db.get_eye_strain_ranking(days=7)
        self.weekly_data = db.get_weekly_history(limit_days=7)
        self.active_tab = "ranking"

        self._build_ui()

    def _build_ui(self):
        # 1. Header Card
        card_top = ctk.CTkFrame(
            self,
            corner_radius=14,
            fg_color=COZY_PALETTE["card"],
            border_color=COZY_PALETTE["border"],
            border_width=2
        )
        card_top.pack(fill="x", padx=16, pady=(14, 6))

        lbl_head = ctk.CTkLabel(
            card_top,
            text=self.t["modal_history_title"],
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COZY_PALETTE["text_main"]
        )
        lbl_head.pack(anchor="w", padx=14, pady=(10, 2))

        lbl_sub = ctk.CTkLabel(
            card_top,
            text=self.t["modal_history_subtitle"],
            font=ctk.CTkFont(size=11),
            text_color=COZY_PALETTE["sage_green"]
        )
        lbl_sub.pack(anchor="w", padx=14, pady=(0, 10))

        # 2. 7-Day Summary Cards Row (3 cards)
        metrics_row = ctk.CTkFrame(self, fg_color="transparent")
        metrics_row.pack(fill="x", padx=16, pady=4)

        # Card A: Screen time
        time_card = ctk.CTkFrame(metrics_row, corner_radius=10, fg_color=COZY_PALETTE["card"], border_color=COZY_PALETTE["border"], border_width=1)
        time_card.pack(side="left", fill="both", expand=True, padx=(0, 4))
        ctk.CTkLabel(time_card, text=self.t["stat_week_time"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"]).pack(pady=(6, 1))
        ctk.CTkLabel(time_card, text=self.weekly_data.get("formatted_total_time", "0 хв"), font=ctk.CTkFont(size=18, weight="bold"), text_color=COZY_PALETTE["text_main"]).pack(pady=(0, 6))

        # Card B: Avg BPM
        rate_card = ctk.CTkFrame(metrics_row, corner_radius=10, fg_color=COZY_PALETTE["card"], border_color=COZY_PALETTE["border"], border_width=1)
        rate_card.pack(side="left", fill="both", expand=True, padx=4)
        ctk.CTkLabel(rate_card, text=self.t["stat_week_rate"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"]).pack(pady=(6, 1))
        avg_bpm_val = self.weekly_data.get("week_avg_bpm", 0.0)
        bpm_color = COZY_PALETTE["sage_green"] if avg_bpm_val >= 14 else (COZY_PALETTE["warm_latte"] if avg_bpm_val >= 10 else COZY_PALETTE["soft_coral"])
        ctk.CTkLabel(rate_card, text=f"{avg_bpm_val} {self.t['bpm_unit_short']}", font=ctk.CTkFont(size=18, weight="bold"), text_color=bpm_color).pack(pady=(0, 6))

        # Card C: Completed Breaks
        breaks_card = ctk.CTkFrame(metrics_row, corner_radius=10, fg_color=COZY_PALETTE["card"], border_color=COZY_PALETTE["border"], border_width=1)
        breaks_card.pack(side="left", fill="both", expand=True, padx=(4, 0))
        ctk.CTkLabel(breaks_card, text=self.t["stat_week_breaks"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"]).pack(pady=(6, 1))
        ctk.CTkLabel(breaks_card, text=f"{self.weekly_data.get('total_breaks', 0)} ☕", font=ctk.CTkFont(size=18, weight="bold"), text_color=COZY_PALETTE["text_main"]).pack(pady=(0, 6))

        # 3. Tab Navigation Buttons (Ranking vs Weekly History)
        tab_bar = ctk.CTkFrame(self, fg_color="transparent")
        tab_bar.pack(fill="x", padx=16, pady=(8, 4))

        self.btn_tab_ranking = ctk.CTkButton(
            tab_bar,
            text=self.t["tab_ranking"],
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COZY_PALETTE["accent_primary"],
            hover_color=COZY_PALETTE["accent_hover"],
            text_color="#ffffff",
            height=30,
            corner_radius=8,
            command=lambda: self._switch_tab("ranking")
        )
        self.btn_tab_ranking.pack(side="left", padx=(0, 6))

        self.btn_tab_history = ctk.CTkButton(
            tab_bar,
            text=self.t["tab_history"],
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COZY_PALETTE["card_alt"],
            hover_color=COZY_PALETTE["border"],
            border_color=COZY_PALETTE["border"],
            border_width=1,
            text_color=COZY_PALETTE["text_muted"],
            height=30,
            corner_radius=8,
            command=lambda: self._switch_tab("history")
        )
        self.btn_tab_history.pack(side="left")

        # 4. Content Card (Container)
        self.content_card = ctk.CTkFrame(
            self,
            corner_radius=14,
            fg_color=COZY_PALETTE["card"],
            border_color=COZY_PALETTE["border"],
            border_width=2
        )
        self.content_card.pack(fill="both", expand=True, padx=16, pady=4)

        self._render_active_tab_content()

        # 5. Footer Action Buttons
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(8, 14))

        btn_folder = ctk.CTkButton(
            footer,
            text=self.t["btn_open_sessions_folder"],
            font=ctk.CTkFont(size=11),
            fg_color=COZY_PALETTE["card_alt"],
            hover_color=COZY_PALETTE["border"],
            border_color=COZY_PALETTE["border"],
            border_width=1,
            text_color=COZY_PALETTE["text_muted"],
            height=32,
            corner_radius=10,
            command=self._open_sessions_folder
        )
        btn_folder.pack(side="left")

        btn_close = ctk.CTkButton(
            footer,
            text=self.t["modal_btn_close"],
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COZY_PALETTE["accent_primary"],
            hover_color=COZY_PALETTE["accent_hover"],
            border_color=COZY_PALETTE["border_light"],
            border_width=1,
            text_color="#ffffff",
            width=110,
            height=32,
            corner_radius=10,
            command=self.destroy
        )
        btn_close.pack(side="right")

    def _switch_tab(self, tab_name: str):
        if self.active_tab == tab_name:
            return
        self.active_tab = tab_name

        if tab_name == "ranking":
            self.btn_tab_ranking.configure(
                fg_color=COZY_PALETTE["accent_primary"],
                hover_color=COZY_PALETTE["accent_hover"],
                border_width=0,
                text_color="#ffffff"
            )
            self.btn_tab_history.configure(
                fg_color=COZY_PALETTE["card_alt"],
                hover_color=COZY_PALETTE["border"],
                border_color=COZY_PALETTE["border"],
                border_width=1,
                text_color=COZY_PALETTE["text_muted"]
            )
        else:
            self.btn_tab_history.configure(
                fg_color=COZY_PALETTE["accent_primary"],
                hover_color=COZY_PALETTE["accent_hover"],
                border_width=0,
                text_color="#ffffff"
            )
            self.btn_tab_ranking.configure(
                fg_color=COZY_PALETTE["card_alt"],
                hover_color=COZY_PALETTE["border"],
                border_color=COZY_PALETTE["border"],
                border_width=1,
                text_color=COZY_PALETTE["text_muted"]
            )

        self._render_active_tab_content()

    def _render_active_tab_content(self):
        # Clear previous children of content_card
        for child in self.content_card.winfo_children():
            child.destroy()

        if self.active_tab == "ranking":
            self._render_ranking_tab()
        else:
            self._render_history_tab()

    def _render_ranking_tab(self):
        # Table header
        tbl_head = ctk.CTkFrame(self.content_card, fg_color="transparent")
        tbl_head.pack(fill="x", padx=14, pady=(10, 4))

        ctk.CTkLabel(
            tbl_head,
            text=self.t["ranking_app_col"],
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COZY_PALETTE["text_muted"]
        ).pack(side="left")

        right_head = ctk.CTkFrame(tbl_head, fg_color="transparent")
        right_head.pack(side="right")
        ctk.CTkLabel(right_head, text=self.t["ranking_time_col"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"], width=65, anchor="e").pack(side="left", padx=4)
        ctk.CTkLabel(right_head, text=self.t["ranking_rate_col"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"], width=85, anchor="e").pack(side="left", padx=4)
        ctk.CTkLabel(right_head, text=self.t["ranking_status_col"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"], width=135, anchor="center").pack(side="left", padx=4)

        scroll = ctk.CTkScrollableFrame(
            self.content_card,
            fg_color="transparent",
            scrollbar_button_color=COZY_PALETTE["border"],
            scrollbar_button_hover_color=COZY_PALETTE["accent_primary"]
        )
        scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        if not self.ranking_data:
            ctk.CTkLabel(
                scroll,
                text=self.t["no_ranking_data"],
                font=ctk.CTkFont(size=12),
                text_color=COZY_PALETTE["text_dim"]
            ).pack(pady=40)
            return

        for item in self.ranking_data:
            row = ctk.CTkFrame(scroll, fg_color=COZY_PALETTE["card_alt"], border_color=COZY_PALETTE["border"], border_width=1, corner_radius=8, height=38)
            row.pack(fill="x", pady=3)

            act_str = item.get("activity", "OTHER")
            proc_str = item.get("process_name", "")
            icon, name = get_friendly_app_label(act_str, proc_str, lang=self.lang)

            # Left: Icon & App Name
            left_box = ctk.CTkFrame(row, fg_color="transparent")
            left_box.pack(side="left", padx=10, pady=4)

            ctk.CTkLabel(left_box, text=icon, font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(left_box, text=name, font=ctk.CTkFont(size=11, weight="bold"), text_color=COZY_PALETTE["text_main"]).pack(side="left")

            # Right: Time, BPM, Badge
            right_box = ctk.CTkFrame(row, fg_color="transparent")
            right_box.pack(side="right", padx=10, pady=4)

            mins = item.get("minutes_count", 0)
            time_str = f"{mins // 60}г {mins % 60:02d}хв" if mins >= 60 else f"{mins} хв"
            bpm_val = float(item.get("avg_bpm", 0.0))

            badge_text = item.get("badge_ua" if self.lang == "UA" else "badge_en", "")
            badge_color = item.get("color", COZY_PALETTE["sage_green"])

            ctk.CTkLabel(right_box, text=time_str, font=ctk.CTkFont(size=11), text_color=COZY_PALETTE["text_muted"], width=65, anchor="e").pack(side="left", padx=4)
            ctk.CTkLabel(right_box, text=f"{bpm_val:.1f} {self.t['bpm_unit_short']}", font=ctk.CTkFont(size=11, weight="bold"), text_color=COZY_PALETTE["text_main"], width=85, anchor="e").pack(side="left", padx=4)

            # Status Badge with gentle background
            badge_frame = ctk.CTkFrame(right_box, fg_color=COZY_PALETTE["card"], border_color=badge_color, border_width=1, corner_radius=6, width=135, height=24)
            badge_frame.pack_propagate(False)
            badge_frame.pack(side="left", padx=(6, 0))

            ctk.CTkLabel(badge_frame, text=badge_text, font=ctk.CTkFont(size=10, weight="bold"), text_color=badge_color).pack(expand=True)

    def _render_history_tab(self):
        # Table header
        tbl_head = ctk.CTkFrame(self.content_card, fg_color="transparent")
        tbl_head.pack(fill="x", padx=14, pady=(10, 4))

        ctk.CTkLabel(
            tbl_head,
            text=self.t["history_date_col"],
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COZY_PALETTE["text_muted"]
        ).pack(side="left")

        right_head = ctk.CTkFrame(tbl_head, fg_color="transparent")
        right_head.pack(side="right")
        ctk.CTkLabel(right_head, text=self.t["history_time_col"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"], width=85, anchor="e").pack(side="left", padx=4)
        ctk.CTkLabel(right_head, text=self.t["history_blinks_col"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"], width=70, anchor="e").pack(side="left", padx=4)
        ctk.CTkLabel(right_head, text=self.t["history_rate_col"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"], width=80, anchor="e").pack(side="left", padx=4)
        ctk.CTkLabel(right_head, text=self.t["history_breaks_col"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"], width=75, anchor="center").pack(side="left", padx=4)

        scroll = ctk.CTkScrollableFrame(
            self.content_card,
            fg_color="transparent",
            scrollbar_button_color=COZY_PALETTE["border"],
            scrollbar_button_hover_color=COZY_PALETTE["accent_primary"]
        )
        scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        daily_list = self.weekly_data.get("daily", [])
        if not daily_list:
            ctk.CTkLabel(
                scroll,
                text=self.t["no_history_data"],
                font=ctk.CTkFont(size=12),
                text_color=COZY_PALETTE["text_dim"]
            ).pack(pady=40)
            return

        today_str = datetime.now().strftime("%Y-%m-%d")

        for item in daily_list:
            row = ctk.CTkFrame(scroll, fg_color=COZY_PALETTE["card_alt"], border_color=COZY_PALETTE["border"], border_width=1, corner_radius=8, height=38)
            row.pack(fill="x", pady=3)

            date_str = item.get("date", "")
            if date_str == today_str:
                display_date = f"✨ {self.t['today']} ({date_str})"
            else:
                display_date = f"📅 {date_str}"

            # Left: Date
            left_box = ctk.CTkFrame(row, fg_color="transparent")
            left_box.pack(side="left", padx=10, pady=4)
            ctk.CTkLabel(left_box, text=display_date, font=ctk.CTkFont(size=11, weight="bold"), text_color=COZY_PALETTE["text_main"]).pack(side="left")

            # Right: Screen Time, Blinks, BPM, Breaks
            right_box = ctk.CTkFrame(row, fg_color="transparent")
            right_box.pack(side="right", padx=10, pady=4)

            time_str = item.get("formatted_time", "0 хв")
            blinks_val = str(item.get("blinks", 0))
            bpm_val = float(item.get("avg_bpm", 0.0))
            breaks_val = f"{item.get('breaks_count', 0)} ☕"

            bpm_color = COZY_PALETTE["sage_green"] if bpm_val >= 14 else (COZY_PALETTE["warm_latte"] if bpm_val >= 10 else COZY_PALETTE["soft_coral"])

            ctk.CTkLabel(right_box, text=time_str, font=ctk.CTkFont(size=11), text_color=COZY_PALETTE["text_muted"], width=85, anchor="e").pack(side="left", padx=4)
            ctk.CTkLabel(right_box, text=blinks_val, font=ctk.CTkFont(size=11), text_color=COZY_PALETTE["text_muted"], width=70, anchor="e").pack(side="left", padx=4)
            ctk.CTkLabel(right_box, text=f"{bpm_val:.1f}", font=ctk.CTkFont(size=11, weight="bold"), text_color=bpm_color, width=80, anchor="e").pack(side="left", padx=4)
            ctk.CTkLabel(right_box, text=breaks_val, font=ctk.CTkFont(size=11, weight="bold"), text_color=COZY_PALETTE["text_main"], width=75, anchor="center").pack(side="left", padx=4)

    def _open_sessions_folder(self):
        sessions_dir = os.path.abspath("sessions")
        open_folder_cross_platform(sessions_dir)


class EyeTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Setup explicit AppUserModelID on Windows so taskbar displays custom icon
        if sys.platform == "win32":
            try:
                import ctypes
                myappid = 'eyetracker.ai.v1'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception:
                pass

        # Set window icon (supports Windows, macOS, Linux)
        ico_path = resource_path(os.path.join("assets", "icon.ico"))
        png_path = resource_path(os.path.join("assets", "icon.png"))
        if sys.platform == "win32" and os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass
        elif os.path.exists(png_path):
            try:
                img = tk.PhotoImage(file=png_path)
                self.iconphoto(True, img)
                self._app_icon_img = img
            except Exception:
                pass

        # Current language (EN by default for global audience)
        self.current_lang = "EN"
        self.t = TRANSLATIONS[self.current_lang]

        # Window configuration (Smoothly resizable cozy widget)
        self.title(self.t["title"])
        self.geometry("620x510")
        self.minsize(520, 480)
        self.resizable(True, True)

        # Custom appearance
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=COZY_PALETTE["bg"])

        # Subsystems
        db.init_db()
        self.eye_tracker = EyeTracker(camera_index=0)
        self.activity_tracker = ActivityTracker()

        # State variables
        self.is_tracking = False
        self.session_id = None
        self.tracking_thread = None

        # Session activity tracking
        self.session_start_timestamp = 0.0
        self.session_activity_durations = {act.value: 0.0 for act in ActivityType}
        self.session_activity_blinks = {act.value: 0 for act in ActivityType}

        # Camera & eye break reminder settings
        self.available_cameras = get_available_cameras(self.current_lang)
        self.selected_camera_index = 0
        self.reminders_enabled = ctk.BooleanVar(value=True)
        self.break_interval_sec = 1800.0  # default 30 min
        self.last_break_time = time.time()
        self.blinks_at_last_break = 0
        self.last_toast_time = 0.0

        # Stats aggregation
        self.minute_blinks = 0
        self.last_minute_save_time = time.time()
        self.last_known_total_blinks = 0
        self.completed_breaks_count = 0

        # Smart Auto-Pause settings & state
        self.auto_pause_enabled = True
        self.is_auto_paused = False
        self.face_absent_start_time = 0.0
        self.total_paused_duration = 0.0
        self.pause_start_timestamp = 0.0
        self.last_face_seen_time = time.time()
        self.resumed_banner_time = 0.0

        # Performance & Smooth Resize Caches
        self._last_resize_time = 0.0
        self._current_size = (620, 510)
        self._cached_bpm = None
        self._cached_health_text = None
        self._cached_health_color = None
        self._cached_cam_status = None
        self._cached_cam_color = None
        self._cached_act_icon = None
        self._cached_act_name = None
        self._cached_act_color = None
        self._cached_win_title = None
        self._cached_total_blinks = None
        self._cached_since_blink_str = None
        self._cached_since_blink_color = None
        self._cached_session_time = None

        # Build UI layout
        self._build_cozy_ui()

        # Track resizing to ensure buttery smooth performance
        self.bind("<Configure>", self._on_window_configure)

        # Intercept window close [X]
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Enable modern Windows dark titlebar and native DWM hardware acceleration
        self.after(50, self._apply_modern_windows_styling)

        # UI Update Loop (80ms ~ 12.5 FPS)
        self.after(80, self._ui_update_loop)

    def _apply_modern_windows_styling(self):
        """Enables native DWM hardware-accelerated rendering, WS_CLIPCHILDREN, and modern dark titlebar on Windows."""
        if sys.platform != "win32" or win32gui is None:
            return
        try:
            import ctypes
            hwnd = self.winfo_id()
            toplevel = ctypes.windll.user32.GetAncestor(hwnd, 2) or hwnd  # GA_ROOT = 2

            # Enable WS_CLIPCHILDREN on both root and client to eliminate redraw flicker
            for h in (toplevel, hwnd):
                cur_style = win32gui.GetWindowLong(h, win32con.GWL_STYLE)
                win32gui.SetWindowLong(h, win32con.GWL_STYLE, cur_style | win32con.WS_CLIPCHILDREN)

                cur_ex = win32gui.GetWindowLong(h, win32con.GWL_EXSTYLE)
                if cur_ex & win32con.WS_EX_COMPOSITED:
                    win32gui.SetWindowLong(h, win32con.GWL_EXSTYLE, cur_ex & ~win32con.WS_EX_COMPOSITED)

                try:
                    win32gui.SetWindowPos(
                        h, 0, 0, 0, 0, 0,
                        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
                    )
                except Exception:
                    pass

            # Native Windows 10/11 Dark Titlebar (DWMWA_USE_IMMERSIVE_DARK_MODE = 20 or 19)
            value = ctypes.c_int(1)
            for attr in (20, 19):
                res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    toplevel,
                    attr,
                    ctypes.byref(value),
                    ctypes.sizeof(value)
                )
                if res == 0:
                    break

            # Windows 11 Rounded Corners (DWMWA_WINDOW_CORNER_PREFERENCE = 33, DWMWCP_ROUND = 2)
            corner_pref = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                toplevel,
                33,
                ctypes.byref(corner_pref),
                ctypes.sizeof(corner_pref)
            )
        except Exception:
            pass

    def _on_window_configure(self, event):
        """Monitors window resizing to pause background relayouts during active mouse drag."""
        if event.widget is self:
            new_size = (event.width, event.height)
            if new_size != self._current_size:
                self._current_size = new_size
                self._last_resize_time = time.time()

    def _build_cozy_ui(self):
        # 1. Header Bar
        self.header_bar = ctk.CTkFrame(
            self,
            corner_radius=14,
            fg_color=COZY_PALETTE["card"],
            border_color=COZY_PALETTE["border"],
            border_width=2,
            overwrite_preferred_drawing_method="polygon_shapes"
        )
        self.header_bar.pack(fill="x", padx=16, pady=(8, 3))

        # Brand / Logo (Native fast layout container)
        brand_box = tk.Frame(self.header_bar, bg=COZY_PALETTE["card"])
        brand_box.pack(side="left", padx=(10, 4), pady=4)

        self.lbl_logo = ctk.CTkLabel(
            brand_box,
            text=self.t["app_name"],
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COZY_PALETTE["text_main"]
        )
        self.lbl_logo.pack(anchor="w")

        self.lbl_tagline = ctk.CTkLabel(
            brand_box,
            text=self.t["tagline"],
            font=ctk.CTkFont(size=10),
            text_color=COZY_PALETTE["text_muted"]
        )
        self.lbl_tagline.pack(anchor="w")

        # Controls container packed on right (Native fast layout container)
        hdr_right = tk.Frame(self.header_bar, bg=COZY_PALETTE["card"])
        hdr_right.pack(side="right", padx=(4, 10), pady=4)

        # Main Start / Stop Pill Button
        self.btn_start = ctk.CTkButton(
            hdr_right,
            text=self.t["btn_start"],
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COZY_PALETTE["accent_primary"],
            hover_color=COZY_PALETTE["accent_hover"],
            border_color=COZY_PALETTE["border_light"],
            border_width=1,
            text_color="#ffffff",
            height=28,
            width=102,
            corner_radius=8,
            command=self.toggle_tracking
        )
        self.btn_start.pack(side="right", padx=(3, 0))

        # Sessions & Analytics Modal Button (compact icon button)
        self.btn_sessions = ctk.CTkButton(
            hdr_right,
            text=self.t["btn_sessions"],
            font=ctk.CTkFont(size=12),
            fg_color=COZY_PALETTE["card_alt"],
            hover_color=COZY_PALETTE["border"],
            border_color=COZY_PALETTE["border"],
            border_width=1,
            text_color=COZY_PALETTE["text_main"],
            width=30,
            height=28,
            corner_radius=7,
            command=self.open_history_analytics
        )
        self.btn_sessions.pack(side="right", padx=2)

        # Language Switcher OptionMenu (no text selection / cursor)
        self.combo_lang = ctk.CTkOptionMenu(
            hdr_right,
            values=["🇬🇧 EN", "🇺🇦 UA"],
            width=70,
            height=28,
            corner_radius=7,
            dynamic_resizing=False,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COZY_PALETTE["card_alt"],
            button_color=COZY_PALETTE["accent_primary"],
            button_hover_color=COZY_PALETTE["accent_hover"],
            dropdown_fg_color=COZY_PALETTE["card"],
            dropdown_hover_color=COZY_PALETTE["card_alt"],
            text_color=COZY_PALETTE["text_main"],
            command=self._on_language_changed
        )
        self.combo_lang.set("🇬🇧 EN" if self.current_lang == "EN" else "🇺🇦 UA")
        self.combo_lang.pack(side="right", padx=2)

        # Reminder test button (compact icon button - guaranteed never compressed)
        self.btn_test_reminder = ctk.CTkButton(
            hdr_right,
            text=self.t["btn_test"],
            font=ctk.CTkFont(size=12),
            fg_color=COZY_PALETTE["card_alt"],
            hover_color=COZY_PALETTE["border"],
            border_color=COZY_PALETTE["border"],
            border_width=1,
            text_color=COZY_PALETTE["text_muted"],
            width=30,
            height=28,
            corner_radius=7,
            command=self.test_reminder
        )
        self.btn_test_reminder.pack(side="right", padx=2)

        # 2. Alert Banner (appears only when user hasn't blinked in > threshold)
        self.alert_banner = ctk.CTkFrame(
            self,
            corner_radius=14,
            fg_color=COZY_PALETTE["alert_bg"],
            border_color=COZY_PALETTE["alert_border"],
            border_width=1,
            overwrite_preferred_drawing_method="polygon_shapes"
        )
        # Hidden by default

        self.lbl_alert_text = ctk.CTkLabel(
            self.alert_banner,
            text=self.t["alert_text"],
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#fcdad7"
        )
        self.lbl_alert_text.pack(side="left", padx=14, pady=8)

        self.btn_dismiss = ctk.CTkButton(
            self.alert_banner,
            text=self.t["btn_blinked"],
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#5e2b24",
            hover_color="#73352c",
            text_color="#fcdad7",
            width=84,
            height=26,
            corner_radius=13,
            command=self._dismiss_alert
        )
        self.btn_dismiss.pack(side="right", padx=12, pady=6)

        # 3. Settings & Camera Selection Card (Two clean responsive rows)
        self.settings_card = ctk.CTkFrame(
            self,
            corner_radius=14,
            fg_color=COZY_PALETTE["card"],
            border_color=COZY_PALETTE["border"],
            border_width=2,
            overwrite_preferred_drawing_method="polygon_shapes"
        )
        self.settings_card.pack(fill="x", padx=16, pady=3)

        # Row 1: Camera (Native fast layout row)
        row_cam = tk.Frame(self.settings_card, bg=COZY_PALETTE["card"])
        row_cam.pack(fill="x", padx=12, pady=(5, 2))

        self.lbl_cam_title = ctk.CTkLabel(
            row_cam,
            text=self.t["camera_label"],
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COZY_PALETTE["text_muted"]
        )
        self.lbl_cam_title.pack(side="left", padx=(0, 6))

        self.combo_camera = ctk.CTkOptionMenu(
            row_cam,
            values=self.available_cameras if self.available_cameras else [self.t["default_camera"]],
            width=210,
            height=26,
            corner_radius=8,
            dynamic_resizing=False,
            font=ctk.CTkFont(size=11),
            fg_color=COZY_PALETTE["card_alt"],
            button_color=COZY_PALETTE["accent_primary"],
            button_hover_color=COZY_PALETTE["accent_hover"],
            dropdown_fg_color=COZY_PALETTE["card"],
            dropdown_hover_color=COZY_PALETTE["card_alt"],
            text_color=COZY_PALETTE["text_main"],
            command=self._on_camera_selected
        )
        if self.available_cameras:
            self.combo_camera.set(self.available_cameras[0])
        self.combo_camera.pack(side="left", padx=(0, 6))

        # Refresh cameras button
        btn_refresh_cam = ctk.CTkButton(
            row_cam,
            text="🔄",
            width=26,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color=COZY_PALETTE["card_alt"],
            hover_color=COZY_PALETTE["border"],
            border_color=COZY_PALETTE["border"],
            border_width=1,
            text_color=COZY_PALETTE["text_muted"],
            command=self._refresh_cameras
        )
        btn_refresh_cam.pack(side="left")

        # Row 2: Break interval & Reminders toggle (Native fast layout row)
        row_break = tk.Frame(self.settings_card, bg=COZY_PALETTE["card"])
        row_break.pack(fill="x", padx=12, pady=(2, 5))

        self.lbl_break_title = ctk.CTkLabel(
            row_break,
            text=self.t["break_label"],
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COZY_PALETTE["text_muted"]
        )
        self.lbl_break_title.pack(side="left", padx=(0, 6))

        self.combo_break = ctk.CTkOptionMenu(
            row_break,
            values=self.t["break_options"],
            width=165,
            height=26,
            corner_radius=8,
            dynamic_resizing=False,
            font=ctk.CTkFont(size=11),
            fg_color=COZY_PALETTE["card_alt"],
            button_color=COZY_PALETTE["accent_primary"],
            button_hover_color=COZY_PALETTE["accent_hover"],
            dropdown_fg_color=COZY_PALETTE["card"],
            dropdown_hover_color=COZY_PALETTE["card_alt"],
            text_color=COZY_PALETTE["text_main"],
            command=self._on_break_interval_change
        )
        self.combo_break.set(self.t["break_options"][1])  # 30 min default
        self.combo_break.pack(side="left", padx=(0, 10))

        self.chk_reminders = ctk.CTkCheckBox(
            row_break,
            text=self.t["reminders"],
            variable=self.reminders_enabled,
            font=ctk.CTkFont(size=11),
            text_color=COZY_PALETTE["text_muted"],
            fg_color=COZY_PALETTE["accent_primary"],
            hover_color=COZY_PALETTE["accent_hover"],
            border_color=COZY_PALETTE["border"]
        )
        self.chk_reminders.pack(side="right", padx=(0, 2))

        # 7. Cozy Footer Note (pinned to bottom of window)
        footer_frame = tk.Frame(self, bg=COZY_PALETTE["bg"])
        footer_frame.pack(side="bottom", fill="x", padx=16, pady=(2, 8))

        self.lbl_footer_note = ctk.CTkLabel(
            footer_frame,
            text=self.t["footer_note"],
            font=ctk.CTkFont(size=9),
            text_color=COZY_PALETTE["text_dim"]
        )
        self.lbl_footer_note.pack(anchor="center")

        # 4. Main Hero Card: Blink Rate & Health Status (expands vertically)
        self.card_bpm = ctk.CTkFrame(
            self,
            corner_radius=14,
            fg_color=COZY_PALETTE["card"],
            border_color=COZY_PALETTE["border"],
            border_width=2,
            overwrite_preferred_drawing_method="polygon_shapes"
        )
        self.card_bpm.pack(side="top", fill="both", expand=True, padx=16, pady=3)

        bpm_head = tk.Frame(self.card_bpm, bg=COZY_PALETTE["card"])
        bpm_head.pack(side="top", fill="x", padx=12, pady=(5, 1))

        self.lbl_bpm_header = ctk.CTkLabel(
            bpm_head,
            text=self.t["bpm_title"],
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COZY_PALETTE["text_dim"]
        )
        self.lbl_bpm_header.pack(side="left")

        self.lbl_camera_status = ctk.CTkLabel(
            bpm_head,
            text=self.t["cam_waiting"],
            font=ctk.CTkFont(size=11),
            text_color=COZY_PALETTE["text_dim"]
        )
        self.lbl_camera_status.pack(side="right")

        # Cozy Inset Health Status Frame (docked to bottom of card_bpm)
        health_box = ctk.CTkFrame(
            self.card_bpm,
            corner_radius=8,
            fg_color=COZY_PALETTE["card_alt"],
            border_color=COZY_PALETTE["border"],
            border_width=1,
            overwrite_preferred_drawing_method="polygon_shapes"
        )
        health_box.pack(side="bottom", fill="x", padx=12, pady=(2, 6))

        self.lbl_health_status = ctk.CTkLabel(
            health_box,
            text=self.t["health_ready"],
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COZY_PALETTE["sage_green"]
        )
        self.lbl_health_status.pack(anchor="w", padx=8, pady=3)

        bpm_row = tk.Frame(self.card_bpm, bg=COZY_PALETTE["card"])
        bpm_row.pack(side="top", fill="both", expand=True, padx=12, pady=0)

        self.lbl_bpm_value = ctk.CTkLabel(
            bpm_row,
            text="0",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=COZY_PALETTE["text_main"]
        )
        self.lbl_bpm_value.pack(side="left")

        self.lbl_bpm_unit = ctk.CTkLabel(
            bpm_row,
            text=self.t["bpm_unit"],
            font=ctk.CTkFont(size=11),
            text_color=COZY_PALETTE["text_muted"]
        )
        self.lbl_bpm_unit.pack(side="left", padx=6, pady=(10, 0))

        # 5. Activity Card
        self.card_activity = ctk.CTkFrame(
            self,
            corner_radius=14,
            fg_color=COZY_PALETTE["card"],
            border_color=COZY_PALETTE["border"],
            border_width=2,
            overwrite_preferred_drawing_method="polygon_shapes"
        )
        self.card_activity.pack(side="top", fill="x", padx=16, pady=3)

        act_top = tk.Frame(self.card_activity, bg=COZY_PALETTE["card"])
        act_top.pack(fill="x", padx=12, pady=(5, 1))

        self.lbl_act_header = ctk.CTkLabel(
            act_top,
            text=self.t["activity_title"],
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COZY_PALETTE["text_dim"]
        )
        self.lbl_act_header.pack(side="left")

        self.combo_mode = ctk.CTkOptionMenu(
            act_top,
            values=self.t["activity_modes"],
            width=110,
            height=24,
            corner_radius=6,
            dynamic_resizing=False,
            font=ctk.CTkFont(size=11),
            fg_color=COZY_PALETTE["card_alt"],
            button_color=COZY_PALETTE["accent_primary"],
            button_hover_color=COZY_PALETTE["accent_hover"],
            dropdown_fg_color=COZY_PALETTE["card"],
            dropdown_hover_color=COZY_PALETTE["card_alt"],
            text_color=COZY_PALETTE["text_main"],
            command=self._on_activity_mode_change
        )
        self.combo_mode.set(self.t["activity_modes"][0])  # Auto
        self.combo_mode.pack(side="right")

        act_content = tk.Frame(self.card_activity, bg=COZY_PALETTE["card"])
        act_content.pack(fill="x", padx=12, pady=(1, 5))

        # Cozy Inset Icon Slot Box
        self.icon_slot = ctk.CTkFrame(
            act_content,
            width=30,
            height=30,
            corner_radius=8,
            fg_color=COZY_PALETTE["card_alt"],
            border_color=COZY_PALETTE["border"],
            border_width=1,
            overwrite_preferred_drawing_method="polygon_shapes"
        )
        self.icon_slot.pack_propagate(False)
        self.icon_slot.pack(side="left", padx=(0, 8))

        self.lbl_activity_icon = ctk.CTkLabel(
            self.icon_slot,
            text="☕",
            font=ctk.CTkFont(size=15)
        )
        self.lbl_activity_icon.pack(expand=True)

        act_titles = tk.Frame(act_content, bg=COZY_PALETTE["card"])
        act_titles.pack(side="left", fill="x", expand=True)

        self.lbl_activity_name = ctk.CTkLabel(
            act_titles,
            text=self.t["activity_waiting"],
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COZY_PALETTE["text_main"],
            anchor="w"
        )
        self.lbl_activity_name.pack(fill="x")

        self.lbl_window_title = ctk.CTkLabel(
            act_titles,
            text=self.t["desktop"],
            font=ctk.CTkFont(size=10),
            text_color=COZY_PALETTE["text_dim"],
            anchor="w"
        )
        self.lbl_window_title.pack(fill="x")

        # 6. Micro Metrics Grid (3 minimal cards, expand vertically)
        metrics_row = tk.Frame(self, bg=COZY_PALETTE["bg"])
        metrics_row.pack(side="top", fill="both", expand=True, padx=16, pady=3)

        # Card A: Total Blinks
        card_a = ctk.CTkFrame(
            metrics_row,
            corner_radius=12,
            fg_color=COZY_PALETTE["card"],
            border_color=COZY_PALETTE["border"],
            border_width=2,
            overwrite_preferred_drawing_method="polygon_shapes"
        )
        card_a.pack(side="left", fill="both", expand=True, padx=3)
        self.lbl_m_total_title = ctk.CTkLabel(card_a, text=self.t["metric_total"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"])
        self.lbl_m_total_title.pack(side="top", pady=(6, 2))
        self.lbl_total_blinks = ctk.CTkLabel(card_a, text="0", font=ctk.CTkFont(size=17, weight="bold"), text_color=COZY_PALETTE["text_main"])
        self.lbl_total_blinks.pack(side="top", fill="both", expand=True, pady=(0, 6))

        # Card B: Pause since last blink
        card_b = ctk.CTkFrame(
            metrics_row,
            corner_radius=12,
            fg_color=COZY_PALETTE["card"],
            border_color=COZY_PALETTE["border"],
            border_width=2,
            overwrite_preferred_drawing_method="polygon_shapes"
        )
        card_b.pack(side="left", fill="both", expand=True, padx=3)
        self.lbl_m_pause_title = ctk.CTkLabel(card_b, text=self.t["metric_pause"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"])
        self.lbl_m_pause_title.pack(side="top", pady=(6, 2))
        self.lbl_since_blink = ctk.CTkLabel(card_b, text="0.0 с", font=ctk.CTkFont(size=17, weight="bold"), text_color=COZY_PALETTE["text_main"])
        self.lbl_since_blink.pack(side="top", fill="both", expand=True, pady=(0, 6))

        # Card C: Session Time
        card_c = ctk.CTkFrame(
            metrics_row,
            corner_radius=12,
            fg_color=COZY_PALETTE["card"],
            border_color=COZY_PALETTE["border"],
            border_width=2,
            overwrite_preferred_drawing_method="polygon_shapes"
        )
        card_c.pack(side="left", fill="both", expand=True, padx=3)
        self.lbl_m_session_title = ctk.CTkLabel(card_c, text=self.t["metric_session"], font=ctk.CTkFont(size=10, weight="bold"), text_color=COZY_PALETTE["text_dim"])
        self.lbl_m_session_title.pack(side="top", pady=(6, 2))
        self.lbl_session_time = ctk.CTkLabel(card_c, text="00:00", font=ctk.CTkFont(size=17, weight="bold"), text_color=COZY_PALETTE["text_main"])
        self.lbl_session_time.pack(side="top", fill="both", expand=True, pady=(0, 6))

    def _on_language_changed(self, choice):
        """Switches application language between Ukrainian and English."""
        if "EN" in choice:
            self.current_lang = "EN"
        else:
            self.current_lang = "UA"
        self.t = TRANSLATIONS[self.current_lang]
        self._apply_language()

    def _apply_language(self):
        """Applies current language to all UI widgets."""
        t = self.t
        self.title(t["title"])
        self.lbl_logo.configure(text=t["app_name"])
        self.lbl_tagline.configure(text=t["tagline"])
        self.btn_start.configure(text=t["btn_stop"] if self.is_tracking else t["btn_start"])
        self.btn_sessions.configure(text=t["btn_sessions"])
        self.btn_test_reminder.configure(text=t["btn_test"])
        self.chk_reminders.configure(text=t["reminders"])
        self.lbl_alert_text.configure(text=t["alert_text"])
        self.btn_dismiss.configure(text=t["btn_blinked"])
        self.lbl_cam_title.configure(text=t["camera_label"])
        self.lbl_break_title.configure(text=t["break_label"])
        self.combo_break.configure(values=t["break_options"])

        # Preserve current break interval index
        if self.break_interval_sec == 900.0:
            self.combo_break.set(t["break_options"][0])
        elif self.break_interval_sec == 1800.0:
            self.combo_break.set(t["break_options"][1])
        elif self.break_interval_sec == 2700.0:
            self.combo_break.set(t["break_options"][2])
        else:
            self.combo_break.set(t["break_options"][3])

        self.lbl_bpm_header.configure(text=t["bpm_title"])
        self.lbl_bpm_unit.configure(text=t["bpm_unit"])
        if not self.is_tracking:
            self.lbl_health_status.configure(text=t["health_ready"])
            self.lbl_camera_status.configure(text=t["cam_waiting"])

        self.lbl_act_header.configure(text=t["activity_title"])
        self.combo_mode.configure(values=t["activity_modes"])
        self.combo_mode.set(t["activity_modes"][0])

        self.lbl_m_total_title.configure(text=t["metric_total"])
        self.lbl_m_pause_title.configure(text=t["metric_pause"])
        self.lbl_m_session_title.configure(text=t["metric_session"])
        self.lbl_footer_note.configure(text=t["footer_note"])

        # Invalidate caches to trigger immediate re-translation
        self._cached_health_text = None
        self._cached_cam_status = None
        self._cached_act_name = None
        self._cached_win_title = None

    def _refresh_cameras(self):
        self.available_cameras = get_available_cameras(self.current_lang)
        cams = self.available_cameras if self.available_cameras else [self.t["default_camera"]]
        self.combo_camera.configure(values=cams)
        if self.available_cameras:
            self.combo_camera.set(self.available_cameras[0])
            self._on_camera_selected(self.available_cameras[0])
        else:
            self.combo_camera.set(self.t["default_camera"])

    def _on_camera_selected(self, choice):
        try:
            index = int(choice.split(":")[0].strip())
            self.selected_camera_index = index
            self.eye_tracker.set_camera_index(index)
            status_text = self.t["cam_selected"].format(idx=index)
            self._update_label(self.lbl_camera_status, status_text, COZY_PALETTE["text_muted"])
        except Exception as e:
            print(f"[Camera Select Error] {e}")

    def _on_break_interval_change(self, choice):
        if "15" in choice:
            self.break_interval_sec = 900.0
        elif "30" in choice:
            self.break_interval_sec = 1800.0
        elif "45" in choice:
            self.break_interval_sec = 2700.0
        else:
            self.break_interval_sec = 3600.0

    def _on_activity_mode_change(self, choice):
        mapping = {
            # UA
            "🤖 Авто": None,
            "💻 Робота": "WORK",
            "🎮 Ігри": "GAMING",
            "🎬 Відео": "VIDEO",
            "🌐 Серфінг": "BROWSING",
            "💬 Чат": "SOCIAL",
            # EN
            "🤖 Auto": None,
            "💻 Work": "WORK",
            "🎮 Gaming": "GAMING",
            "🎬 Video": "VIDEO",
            "🌐 Browsing": "BROWSING",
            "💬 Chat": "SOCIAL"
        }
        target = mapping.get(choice)
        self.activity_tracker.set_manual_override(target)

    def send_toast_reminder(self, title: str, message: str):
        if not self.reminders_enabled.get():
            return

        def _send():
            # 1. Windows: Native Win11/10 toast
            if sys.platform == "win32" and toast is not None:
                try:
                    toast(title, message, duration='short', audio={'silent': 'true'})
                    return
                except Exception:
                    pass

            # 2. macOS: Native AppleScript notification
            if sys.platform == "darwin":
                try:
                    import subprocess
                    script = f'display notification "{message}" with title "{title}"'
                    subprocess.run(["osascript", "-e", script], check=False)
                    return
                except Exception:
                    pass

            # 3. Linux: notify-send
            if sys.platform.startswith("linux"):
                try:
                    import subprocess
                    subprocess.run(["notify-send", title, message], check=False)
                    return
                except Exception:
                    pass

            # 4. Universal Fallback: Plyer
            try:
                from plyer import notification
                notification.notify(title=title, message=message, app_name="EyeTracker", timeout=5)
            except Exception:
                pass

        threading.Thread(target=_send, daemon=True).start()

    def test_reminder(self):
        mins = int(self.break_interval_sec // 60)
        blinks = self.last_known_total_blinks if self.is_tracking else 385
        bpm = round(blinks / max(0.1, mins), 1) if self.is_tracking else 12.8
        t = self.t
        msg = t["toast_test_msg"].format(mins=mins, blinks=blinks, bpm=bpm)
        self.send_toast_reminder(t["toast_test_title"], msg)
        self._trigger_in_app_break(mins, blinks, bpm)

    def _trigger_in_app_break(self, mins: int, blinks: int, bpm: float):
        self.completed_breaks_count += 1
        msg = self.t["in_app_break"].format(mins=mins, blinks=blinks, bpm=bpm)
        self._update_label(self.lbl_alert_text, msg)
        if not self.alert_banner.winfo_ismapped():
            self.alert_banner.pack(fill="x", padx=16, pady=(0, 4), before=self.settings_card)
        if win32gui is not None:
            try:
                hwnd = self.winfo_id()
                win32gui.FlashWindow(hwnd, True)
            except Exception:
                pass

    def open_history_analytics(self):
        """Opens the cozy 7-day eye load app ranking & history modal."""
        try:
            HistoryAnalyticsModal(parent=self, lang=self.current_lang)
        except Exception as e:
            print(f"[Open History Analytics Error] {e}")

    def open_sessions_folder(self):
        """Opens the sessions folder in default file manager."""
        open_folder_cross_platform("sessions")

    def toggle_tracking(self):
        if not self.is_tracking:
            self._start_tracking()
        else:
            self._stop_tracking()

    def _start_tracking(self):
        self._update_label(self.lbl_camera_status, self.t["cam_connecting"], COZY_PALETTE["warm_latte"])
        self.update_idletasks()

        started = self.eye_tracker.start()
        if not started:
            self._update_label(self.lbl_camera_status, self.t["cam_not_found"], COZY_PALETTE["soft_coral"])
            return

        # Complete fresh reset for new session
        self.eye_tracker.reset()
        self.is_tracking = True
        self.session_id = db.start_session()
        self.session_start_timestamp = time.time()
        self.session_activity_durations = {act.value: 0.0 for act in ActivityType}
        self.session_activity_blinks = {act.value: 0 for act in ActivityType}
        self.last_minute_save_time = time.time()
        self.last_break_time = time.time()
        self.blinks_at_last_break = 0
        self.last_toast_time = 0.0
        self.minute_blinks = 0
        self.last_known_total_blinks = 0
        self.completed_breaks_count = 0

        # Reset auto-pause state for new session
        self.is_auto_paused = False
        self.face_absent_start_time = 0.0
        self.total_paused_duration = 0.0
        self.pause_start_timestamp = 0.0
        self.last_face_seen_time = time.time()
        self.resumed_banner_time = 0.0

        # Reset cached values & UI indicators immediately
        self._cached_bpm = None
        self._cached_total_blinks = None
        self._cached_session_time = None
        self._cached_since_blink_str = None
        self._update_label(self.lbl_bpm_value, "0")
        self._update_label(self.lbl_total_blinks, "0")
        self._update_label(self.lbl_session_time, "00:00")
        unit_sec = "с" if self.current_lang == "UA" else "s"
        self._update_label(self.lbl_since_blink, f"0.0 {unit_sec}", COZY_PALETTE["text_main"])

        self.btn_start.configure(
            text=self.t["btn_stop"],
            fg_color=COZY_PALETTE["accent_stop"],
            hover_color=COZY_PALETTE["accent_stop_hover"]
        )
        self._update_label(self.lbl_camera_status, self.t["cam_active"], COZY_PALETTE["sage_green"])

        self.tracking_thread = threading.Thread(target=self._camera_worker, daemon=True)
        self.tracking_thread.start()

    def _stop_tracking(self):
        if not self.is_tracking:
            return

        self.is_tracking = False
        if self.tracking_thread and self.tracking_thread.is_alive():
            self.tracking_thread.join(timeout=0.8)

        # Finalize any ongoing auto-pause
        if self.is_auto_paused:
            self.total_paused_duration += max(0.0, time.time() - self.pause_start_timestamp)
            self.is_auto_paused = False

        end_ts = time.time()
        start_ts = self.session_start_timestamp or end_ts
        total_duration = max(1, int(end_ts - start_ts - self.total_paused_duration))
        mins = total_duration // 60
        secs = total_duration % 60
        total_blinks = self.last_known_total_blinks
        avg_bpm = round(total_blinks / (total_duration / 60.0), 1) if total_duration > 0 else 0.0

        # Compile activity breakdown
        activities_summary = []
        primary_activity = "OTHER"
        max_dur = -1.0

        for act in ActivityType:
            dur = self.session_activity_durations.get(act.value, 0.0)
            blinks = self.session_activity_blinks.get(act.value, 0)
            if dur > max_dur:
                max_dur = dur
                primary_activity = act.value

            if dur >= 0.5 or blinks > 0:
                act_mins = max(0.016, dur / 60.0)
                act_bpm = round(blinks / act_mins, 1)
                meta_ua = ACTIVITY_META["UA"].get(act, {})
                meta_en = ACTIVITY_META["EN"].get(act, {})
                activities_summary.append({
                    "activity": act.value,
                    "label_ua": meta_ua.get("label", act.value),
                    "label_en": meta_en.get("label", act.value),
                    "icon": meta_ua.get("icon", "☕"),
                    "color": meta_ua.get("color", "#b08968"),
                    "duration_sec": int(dur),
                    "duration_formatted": f"{int(dur // 60):02d}:{int(dur % 60):02d}",
                    "blinks": blinks,
                    "bpm": act_bpm
                })

        # Fallback if session was very brief
        if not activities_summary:
            meta_ua = ACTIVITY_META["UA"].get(self.activity_tracker.current_activity, {})
            meta_en = ACTIVITY_META["EN"].get(self.activity_tracker.current_activity, {})
            activities_summary.append({
                "activity": self.activity_tracker.current_activity.value,
                "label_ua": meta_ua.get("label", "Інше"),
                "label_en": meta_en.get("label", "Other"),
                "icon": meta_ua.get("icon", "☕"),
                "color": meta_ua.get("color", "#b08968"),
                "duration_sec": total_duration,
                "duration_formatted": f"{mins:02d}:{secs:02d}",
                "blinks": total_blinks,
                "bpm": avg_bpm
            })

        activities_summary.sort(key=lambda x: x["duration_sec"], reverse=True)

        # Record to SQLite DB
        if self.session_id:
            try:
                db.end_session(
                    self.session_id,
                    total_blinks,
                    avg_bpm,
                    primary_activity,
                    duration_sec=total_duration,
                    breaks_count=self.completed_breaks_count
                )
            except Exception as e:
                print(f"[DB end_session error] {e}")

        if self.eye_tracker:
            self.eye_tracker.stop()

        self.btn_start.configure(
            text=self.t["btn_start"],
            fg_color=COZY_PALETTE["accent_primary"],
            hover_color=COZY_PALETTE["accent_hover"]
        )
        self._update_label(self.lbl_camera_status, self.t["cam_stopped"], COZY_PALETTE["text_dim"])
        self._dismiss_alert()

        # Save session to JSON and human-readable TXT in sessions/
        sessions_dir = os.path.abspath("sessions")
        os.makedirs(sessions_dir, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        json_path = os.path.join(sessions_dir, f"session_{timestamp_str}.json")
        txt_path = os.path.join(sessions_dir, f"session_{timestamp_str}.txt")

        start_dt_str = datetime.fromtimestamp(start_ts).strftime("%H:%M:%S") if start_ts else ""
        end_dt_str = datetime.fromtimestamp(end_ts).strftime("%H:%M:%S")
        date_str = datetime.fromtimestamp(end_ts).strftime("%Y-%m-%d")

        session_payload = {
            "session_id": self.session_id,
            "date": date_str,
            "start_time": start_dt_str,
            "end_time": end_dt_str,
            "total_duration_sec": total_duration,
            "total_duration_formatted": f"{mins:02d}:{secs:02d}",
            "total_blinks": total_blinks,
            "average_bpm": avg_bpm,
            "breaks_count": self.completed_breaks_count,
            "activities": activities_summary
        }

        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(session_payload, f, ensure_ascii=False, indent=2)

            txt_content = generate_session_txt(session_payload, lang=self.current_lang)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(txt_content)
        except Exception as e:
            print(f"[Save Session Error] {e}")

        # Show Cozy Session Summary Modal Dialog
        try:
            SessionSummaryModal(
                parent=self,
                session_data=session_payload,
                json_path=json_path,
                txt_path=txt_path,
                lang=self.current_lang
            )
        except Exception as e:
            print(f"[Modal Error] {e}")

    def _dismiss_alert(self):
        self.alert_banner.pack_forget()

    def _camera_worker(self):
        """Worker thread processing frames for blink detection and per-activity stats."""
        AUTO_PAUSE_THRESHOLD_SEC = 20.0
        last_act_poll = 0
        last_frame_ts = time.time()
        try:
            while self.is_tracking:
                now = time.time()
                dt = max(0.0, now - last_frame_ts)
                last_frame_ts = now

                telemetry = self.eye_tracker.process_frame(
                    generate_preview=False,
                    show_landmarks=False
                )

                face_detected = telemetry.get("face_detected", False)

                # Auto-Pause logic: detect when user steps away from PC
                if self.auto_pause_enabled:
                    if face_detected:
                        self.face_absent_start_time = 0.0
                        if self.is_auto_paused:
                            # Auto-resume from pause
                            pause_dur = max(0.0, now - self.pause_start_timestamp)
                            self.total_paused_duration += pause_dur
                            self.is_auto_paused = False
                            self.resumed_banner_time = now
                            # Shift eye break timer forward so pause duration isn't counted as screen time
                            self.last_break_time += pause_dur
                            if self.eye_tracker:
                                self.eye_tracker.last_blink_time = now
                    else:
                        if self.face_absent_start_time == 0.0:
                            self.face_absent_start_time = now
                        elif (now - self.face_absent_start_time >= AUTO_PAUSE_THRESHOLD_SEC) and not self.is_auto_paused:
                            # Enter auto-pause
                            self.is_auto_paused = True
                            self.pause_start_timestamp = now

                # If auto-paused, skip accumulating active session stats
                if self.is_auto_paused:
                    self.last_minute_save_time = now
                    self.last_break_time += dt
                    time.sleep(0.05)
                    continue

                if now - last_act_poll >= 1.5:
                    self.activity_tracker.update(lang=self.current_lang)
                    last_act_poll = now

                current_act = self.activity_tracker.current_activity.value
                self.session_activity_durations[current_act] = self.session_activity_durations.get(current_act, 0.0) + dt

                cur_total = telemetry["total_blinks"]
                diff = max(0, cur_total - self.last_known_total_blinks)
                self.last_known_total_blinks = cur_total
                self.minute_blinks += diff
                if diff > 0:
                    self.session_activity_blinks[current_act] = self.session_activity_blinks.get(current_act, 0) + diff

                if now - self.last_minute_save_time >= 60.0:
                    if self.session_id:
                        db.record_minute_stat(
                            self.session_id,
                            self.minute_blinks,
                            float(telemetry["bpm"]),
                            current_act,
                            float(telemetry["current_ear"]),
                            process_name=self.activity_tracker.current_process_name or ""
                        )
                    self.minute_blinks = 0
                    self.last_minute_save_time = now

                # Eye break reminder check (customizable: 15, 30, 45, 60 min)
                if now - self.last_break_time >= self.break_interval_sec:
                    cur_total = telemetry["total_blinks"]
                    interval_blinks = max(0, cur_total - self.blinks_at_last_break)
                    interval_mins = max(1, int(self.break_interval_sec // 60))
                    interval_bpm = round(interval_blinks / float(interval_mins), 1)

                    t = self.t
                    self.send_toast_reminder(
                        t["toast_break_title"],
                        t["toast_break_msg"].format(mins=interval_mins, blinks=interval_blinks, bpm=interval_bpm)
                    )
                    self.last_break_time = now
                    self.blinks_at_last_break = cur_total
                    self.after(0, lambda m=interval_mins, b=interval_blinks, bpm=interval_bpm: self._trigger_in_app_break(m, b, bpm))

                time.sleep(0.005)
        except Exception as e:
            print(f"[Worker Error] {e}")
        finally:
            if not self.is_tracking and self.eye_tracker:
                self.eye_tracker.stop()

    def _update_label(self, label_widget, text=None, text_color=None):
        """Helper that only reconfigures if the value actually changed, avoiding layout thrashing."""
        if text is not None and label_widget.cget("text") != text:
            label_widget.configure(text=text)
        if text_color is not None and label_widget.cget("text_color") != text_color:
            label_widget.configure(text_color=text_color)

    def _ui_update_loop(self):
        # If user is actively resizing window with mouse (within last 150ms), skip update to keep 60 FPS smooth
        if time.time() - self._last_resize_time < 0.15:
            self.after(50, self._ui_update_loop)
            return

        if self.is_tracking and self.eye_tracker:
            telemetry = self.eye_tracker.get_telemetry()
            act_info = self.activity_tracker.get_cached_info(lang=self.current_lang)

            bpm = telemetry["bpm"]
            if bpm != self._cached_bpm:
                self._update_label(self.lbl_bpm_value, str(bpm))
                self._cached_bpm = bpm

            sec_since = telemetry["seconds_since_blink"]
            t = self.t

            # Health text logic with auto-pause handling
            if self.is_auto_paused:
                h_text = t["auto_paused"]
                h_color = COZY_PALETTE["warm_latte"]
                c_text = t["cam_paused"]
                c_color = COZY_PALETTE["warm_latte"]
            elif (time.time() - self.resumed_banner_time) < 4.0:
                h_text = t["auto_resumed"]
                h_color = COZY_PALETTE["sage_green"]
                c_text = t["cam_in_frame"]
                c_color = COZY_PALETTE["sage_green"]
            elif not telemetry["face_detected"]:
                h_text = t["health_no_face"]
                h_color = COZY_PALETTE["text_dim"]
                c_text = t["cam_looking"]
                c_color = COZY_PALETTE["warm_latte"]
            elif bpm < 8:
                h_text = t["health_fatigue"]
                h_color = COZY_PALETTE["warm_latte"]
                c_text = t["cam_in_frame"]
                c_color = COZY_PALETTE["sage_green"]
            elif bpm < 14:
                h_text = t["health_moderate"]
                h_color = COZY_PALETTE["text_muted"]
                c_text = t["cam_in_frame"]
                c_color = COZY_PALETTE["sage_green"]
            else:
                h_text = t["health_healthy"]
                h_color = COZY_PALETTE["sage_green"]
                c_text = t["cam_in_frame"]
                c_color = COZY_PALETTE["sage_green"]

            self._update_label(self.lbl_health_status, h_text, h_color)
            self._update_label(self.lbl_camera_status, c_text, c_color)

            # Activity Info with caching
            self._update_label(self.lbl_activity_icon, act_info["icon"])
            self._update_label(self.lbl_activity_name, act_info["label"], act_info["color"])

            raw_title = act_info["title"]
            if raw_title in ["Desktop / No Active Window", "Desktop", "Рабочий стол"]:
                title = t["desktop"]
            else:
                title = raw_title or t["desktop"]

            if len(title) > 36:
                title = title[:34] + "..."
            self._update_label(self.lbl_window_title, title)

            # Micro metrics
            self._update_label(self.lbl_total_blinks, str(telemetry["total_blinks"]))

            if self.is_auto_paused:
                self._update_label(self.lbl_since_blink, "—", COZY_PALETTE["text_dim"])
            else:
                unit_sec = "с" if self.current_lang == "UA" else "s"
                since_str = f"{sec_since:.1f} {unit_sec}"
                since_color = COZY_PALETTE["warm_latte"] if sec_since >= 10.0 else COZY_PALETTE["text_main"]
                self._update_label(self.lbl_since_blink, since_str, since_color)

            # Active session time excluding auto-paused intervals
            if self.is_auto_paused:
                current_paused = self.total_paused_duration + max(0.0, time.time() - self.pause_start_timestamp)
            else:
                current_paused = self.total_paused_duration

            dur_sec = max(0, int(time.time() - self.session_start_timestamp - current_paused))
            mins = dur_sec // 60
            secs = dur_sec % 60
            session_str = f"{mins:02d}:{secs:02d}"
            self._update_label(self.lbl_session_time, session_str)

        self.after(80, self._ui_update_loop)

    def on_closing(self):
        try:
            self.is_tracking = False
            if self.tracking_thread and self.tracking_thread.is_alive():
                self.tracking_thread.join(timeout=0.5)
        except Exception:
            pass
        try:
            if self.eye_tracker:
                self.eye_tracker.stop()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass
        os._exit(0)


# Backward compatibility alias
EyeTrackerCozyApp = EyeTrackerApp


def main():
    app = EyeTrackerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
