# Faah Autonomous (FAAH-AUTOMATA) ⚡

**Faah Autonomous** is an intelligent, low-latency cross-device auto-typer that lets you stream text seamlessly from your phone into your computer with realistic human typing speeds, cadence, and automatic application focus.

---

## 🌟 Key Features

- **📱 Zero-App Web Controller**: Connect from any smartphone browser via local Wi-Fi or hotspot.
- **⚡ Dynamic WPM Control**: Adjust typing speed on the fly (**25 to 150+ WPM**) with presets for Slow (40 WPM), Normal (65 WPM), Fast (95 WPM), and Turbo (130 WPM).
- **🧠 Human Cadence & Micro-Pauses**: Includes realistic jitter, natural sentence-end delays, comma pauses, and word-boundary micro-pauses.
- **🎯 macOS Auto-Focus (Google Chrome & Docs)**: Automatically finds and activates Google Chrome using native macOS AppleScript and pauses briefly to guarantee focus in Google Docs or any active tab.
- **📷 Instant QR Code Pairing**: Automatically opens a pairing QR code in macOS Preview on startup for 1-second camera connect.
- **📋 Automatic Clipboard Sync**: Seamlessly backs up submitted text into your Mac's clipboard for instant manual paste (`Cmd + V`) if needed.

---

## 🚀 Quick Start

### 1. Requirements
- macOS (Sonoma, Sequoia, or Monterey)
- Python 3.9+
- Wi-Fi or Personal Hotspot connection between Mac and phone

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/FaheelBhat/FAAH-AUTOMATA.git
cd FAAH-AUTOMATA

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Running Faah Autonomous
```bash
python app.py
```
- A QR code will open on your Mac screen.
- Scan it with your phone's camera (or navigate to the displayed URL, e.g. `http://<YOUR_IP>:5050`).
- Select your target WPM speed, enter your text on your phone, and tap **⚡ Type in Chrome**!

---

## ⚙️ macOS Permissions Note

To allow keystroke automation into other applications, ensure **Accessibility** and **Input Monitoring** permissions are enabled for your Terminal / IDE:
- Open **System Settings** > **Privacy & Security** > **Accessibility** and toggle your Terminal or IDE to **ON**.

---

## 📄 License
MIT License. Created by Faheel Bhat.
