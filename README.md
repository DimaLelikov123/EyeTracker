<div align="center">

<img src="assets/icon.png" width="128" height="128" alt="EyeTracker Cozy Logo" style="border-radius: 28px; box-shadow: 0 8px 24px rgba(0,0,0,0.4);" />

# ✦ EyeTracker Cozy ✦
### Gentle, AI-Powered Blink Tracker & Eye Strain Prevention

[![License: MIT](https://img.shields.io/badge/License-MIT-amber.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)]()
[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-green.svg)]()
[![Privacy: 100% Offline](https://img.shields.io/badge/Privacy-100%25%20Offline-brightgreen.svg)]()

*Protect your eyesight while coding, gaming, studying, or browsing. Built with a soothing, distraction-free aesthetic inspired by cozy farm-sim games.*

</div>

---

## ☕ Why EyeTracker Cozy?

When we focus deeply on screens, our blink rate drops from the healthy baseline of **15–20 blinks/min** down to **4–7 blinks/min**. This causes digital eye strain, dryness, headache, and fatigue.

**EyeTracker Cozy** runs silently in the background:
- Tracks your eye blinks in real-time through your webcam using lightweight computer vision.
- Warns you when your eyes are drying out.
- Ranks your active applications by eye strain (e.g., Code Editor vs Browser vs Gaming).
- Gently reminds you to take 20–30 second breaks to look into the distance.

---

## ✨ Features

- 🌿 **Real-Time Blink & EAR Tracking**: High-accuracy Eye Aspect Ratio (EAR) and Iris tracking powered by Google MediaPipe Face Mesh running smoothly at 60 FPS on CPU (zero GPU needed).
- ☕ **Smart Auto-Pause**: Automatically pauses tracking and freezes timers when you step away from your desk. Resumes seamlessly when you return.
- 🏆 **Eye Strain App Ranking**: Automatically calculates your blink rate and screen time per program (VS Code, Chrome, Games, etc.) with color-coded health badges:
  - `🌿 Excellent` ($\ge 15$ blinks/min)
  - `💻 Moderate Focus` ($10–14$ blinks/min)
  - `⚠️ Eyes Drying Out` ($< 10$ blinks/min)
- 📅 **7-Day History & Weekly Summary**: View screen time, total blinks, average rate, and completed breaks across previous days.
- 🕯️ **Customizable Eye Stretch Reminders**: Set gentle breaks every **15, 30 (recommended), 45, or 60 minutes** with silent toast notifications and in-app reminders.
- 🎨 **Fields of Mistria Cozy Palette**: Warm espresso, matcha sage, and terracotta interface with smooth window resizing and instant language switching (**English 🇬🇧** & **Ukrainian 🇺🇦**).
- 🔒 **100% Privacy by Design**: All processing happens strictly on your local CPU in RAM. No video recording, no screenshots, and zero internet connections.

---

## 🚀 Quick Start

### 🪟 Windows (Pre-built Standalone App)
No Python installation required!
1. Go to the [**Releases**](../../releases) tab.
2. Download the latest `EyeTracker-Cozy-v1.0-Windows.zip`.
3. Extract the archive and double-click **`EyeTracker.exe`** (featuring the custom eye icon).
4. *(Optional)* Right-click `EyeTracker.exe` and select **Send to → Desktop (create shortcut)**.

> **Note on Windows SmartScreen**: Because this open-source build is new and not signed with an expensive enterprise certificate, Windows may show a standard *"Windows protected your PC"* prompt. Click **More info** → **Run anyway**. You can verify the full source code yourself right here in this repository!

---

### 🍏 macOS & 🐧 Linux (Run from Source)

Ensure you have **Python 3.9+** and a webcam:

```bash
# 1. Clone this repository
git clone https://github.com/your-username/EyeTracker-Cozy.git
cd EyeTracker-Cozy

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the app
python run.py
```

*Linux Note: To enable active window detection on Linux X11, optionally install `xdotool` (`sudo apt install xdotool`).*

---

## 🛡️ Privacy Guarantee

We take your digital privacy and security seriously:
- **No Video Recording**: The webcam stream is processed frame-by-frame purely in volatile memory (RAM) and immediately discarded.
- **100% Offline (Air-Gapped)**: The app does not make any outbound network connections or telemetry calls.
- **Local Data Only**: All session metrics are stored locally on your device in `eyetracker.db` and the `sessions/` directory.

---

## ⚖️ Medical & Software Disclaimer

> **PLEASE NOTE**:
> EyeTracker Cozy is an independent productivity and wellness awareness tool designed to remind users to rest their eyes during prolonged screen use.
> It is **NOT** a medical diagnostic tool, medical device, or clinical treatment software. It is not intended to diagnose, treat, cure, or prevent any eye disease or medical condition. Always consult a qualified healthcare or eye care professional (optometrist or ophthalmologist) for any visual symptoms or health concerns.
>
> The software is provided "AS IS", without warranty of any kind, express or implied. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability arising from the use of this software.

---

## 🛠️ Building the Standalone Executable

If you want to build the `.exe` yourself:

```powershell
# In PowerShell (Windows):
.\.venv\Scripts\python.exe build_exe.py
```

This compiles the project with all MediaPipe models, CustomTkinter assets, and icon resources into `dist/EyeTracker/` and automatically creates `dist/EyeTracker-Cozy-v1.0-Windows.zip`.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
Feel free to use, modify, and distribute it.
