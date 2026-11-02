"""
Faah Autonomous (FAAH-AUTOMATA)
--------------------------------
Cross-platform phone-to-PC auto-typer with human-like cadence, WPM speed control,
and automatic browser focus (macOS & Windows).
"""

import os
import sys
import time
import random
import subprocess
import socket
import threading
from flask import Flask, request, jsonify, render_template_string
import qrcode
import pyautogui
import pyperclip

app = Flask(__name__)

# --- Cross-Platform Window Focus Helper ---
def focus_chrome():
    """Brings Google Chrome to the foreground on macOS or Windows."""
    print("[Focus] Locating and focusing Google Chrome...")
    try:
        if sys.platform == 'darwin':
            applescript = """
            tell application "Google Chrome"
                activate
            end tell
            """
            os.system(f"osascript -e '{applescript}'")
        elif sys.platform.startswith('win'):
            # Windows PowerShell activate Chrome
            ps_cmd = (
                "$wshell = New-Object -ComObject wscript.shell; "
                "$chrome = Get-Process -Name chrome -ErrorAction SilentlyContinue | Select-Object -First 1; "
                "if ($chrome) { $wshell.AppActivate($chrome.Id) }"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=False)
        time.sleep(1.0) # Small safety pause to let Chrome render on top
    except Exception as e:
        print(f"[Focus Notice] Error focusing Chrome: {e}")


def type_characters_humanlike(text, wpm=65):
    """
    Types text with human-like randomized typing speeds and micro-pauses based on target WPM.
    Standard typing assumption: 1 word = 5 characters (including spaces/punctuation).
    Target delay per char in seconds = 60 / (wpm * 5) = 12 / wpm.
    """
    try:
        wpm = max(15, min(250, int(wpm)))
    except (ValueError, TypeError):
        wpm = 65

    base_delay = 12.0 / wpm
    print(f"\n[Typing] Target Speed: {wpm} WPM (Base delay: {base_delay*1000:.1f}ms per char)")
    print(f"[Typing] Streaming {len(text)} characters: {repr(text[:50])}...")
    
    # 1. Bring Chrome directly to foreground
    focus_chrome()

    # 2. Sync to clipboard as instant backup
    try:
        pyperclip.copy(text)
    except Exception:
        pass

    # 3. Stream characters using PyAutoGUI with WPM-scaled randomized delay
    try:
        for char in text:
            if char == '\n':
                pyautogui.press('enter')
            elif char == '\t':
                pyautogui.press('tab')
            else:
                pyautogui.write(char)

            # Apply randomized jitter around the target base delay (±25%)
            jitter = random.uniform(0.75, 1.25)
            delay = base_delay * jitter

            # Natural micro-pauses proportional to typing speed
            if char in ('.', '!', '?', '\n'):
                delay += base_delay * random.uniform(3.0, 5.5)
            elif char in (',', ';', ':'):
                delay += base_delay * random.uniform(1.5, 3.0)
            elif char == ' ':
                delay += base_delay * random.uniform(0.5, 1.2)

            time.sleep(delay)
        print("[Typing] Finished streaming characters successfully!")
    except Exception as e:
        print(f"[Typing Error] PyAutoGUI error: {e}")


def get_local_ip():
    """Returns local network IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# --- Web Interface ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Faah Autonomous - Auto Typer</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 16px;
            background: #121212;
            color: #eee;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
        }
        h2 {
            margin-top: 0;
            margin-bottom: 8px;
            color: #4CAF50;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .desc {
            color: #9e9e9e;
            font-size: 14px;
            margin-bottom: 16px;
        }
        textarea {
            width: 100%;
            height: 180px;
            padding: 14px;
            background: #1e1e1e;
            color: #fff;
            border: 1px solid #333;
            border-radius: 10px;
            font-size: 16px;
            box-sizing: border-box;
            resize: vertical;
        }
        textarea:focus {
            outline: none;
            border-color: #4CAF50;
        }
        .speed-control {
            background: #1e1e1e;
            border: 1px solid #2a2a2a;
            border-radius: 10px;
            padding: 14px 16px;
            margin-top: 15px;
        }
        .speed-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            font-size: 15px;
            font-weight: 600;
        }
        .wpm-badge {
            background: #2e7d32;
            color: #fff;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: bold;
        }
        input[type=range] {
            width: 100%;
            height: 6px;
            background: #333;
            border-radius: 4px;
            outline: none;
            -webkit-appearance: none;
        }
        input[type=range]::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background: #4CAF50;
            cursor: pointer;
        }
        .speed-presets {
            display: flex;
            gap: 8px;
            margin-top: 10px;
        }
        .preset-btn {
            flex: 1;
            padding: 6px 0;
            background: #2a2a2a;
            color: #ccc;
            font-size: 12px;
            border: 1px solid #3a3a3a;
            border-radius: 6px;
            cursor: pointer;
            text-align: center;
        }
        .preset-btn:active, .preset-btn.active {
            background: #388e3c;
            color: white;
            border-color: #4CAF50;
        }
        .btn-group {
            display: flex;
            gap: 10px;
            margin-top: 16px;
        }
        button.action-btn {
            flex: 1;
            padding: 14px;
            font-size: 16px;
            font-weight: bold;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        .btn-type {
            background: #4CAF50;
            color: white;
        }
        .btn-clear {
            background: #333;
            color: #ccc;
        }
        button:active {
            opacity: 0.8;
        }
        .status {
            margin-top: 15px;
            font-size: 14px;
            color: #aaa;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>⚡ Faah Autonomous</h2>
        <div class="desc">Types into active Google Chrome window with realistic human cadence.</div>
        
        <textarea id="textInput" placeholder="Paste or type text here..."></textarea>

        <div class="speed-control">
            <div class="speed-header">
                <span>⚡ Typing Speed</span>
                <span class="wpm-badge" id="wpmDisplay">65 WPM</span>
            </div>
            <input type="range" id="wpmSlider" min="25" max="150" value="65" oninput="updateWpm(this.value)">
            <div class="speed-presets">
                <div class="preset-btn" onclick="setPreset(40)">40 (Slow)</div>
                <div class="preset-btn" onclick="setPreset(65)">65 (Normal)</div>
                <div class="preset-btn" onclick="setPreset(95)">95 (Fast)</div>
                <div class="preset-btn" onclick="setPreset(130)">130 (Turbo)</div>
            </div>
        </div>

        <div class="btn-group">
            <button class="action-btn btn-type" onclick="sendText()">⚡ Type in Chrome</button>
            <button class="action-btn btn-clear" onclick="clearText()">Clear</button>
        </div>
        <div class="status" id="status">Ready</div>
    </div>

    <script>
        let currentWpm = 65;

        function updateWpm(val) {
            currentWpm = parseInt(val);
            document.getElementById('wpmDisplay').innerText = currentWpm + ' WPM';
        }

        function setPreset(val) {
            document.getElementById('wpmSlider').value = val;
            updateWpm(val);
        }

        async function sendText() {
            const text = document.getElementById('textInput').value;
            if (!text) return;
            const status = document.getElementById('status');
            status.innerText = "Focusing Chrome & typing @ " + currentWpm + " WPM...";
            try {
                const res = await fetch('/type', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: text, wpm: currentWpm})
                });
                const data = await res.json();
                status.innerText = data.status || "Typing finished!";
            } catch (err) {
                status.innerText = "Error: " + err;
            }
        }

        function clearText() {
            document.getElementById('textInput').value = '';
            document.getElementById('status').innerText = 'Ready';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/type', methods=['POST'])
def handle_type():
    data = request.get_json() or {}
    text = data.get('text', '')
    wpm = data.get('wpm', 65)
    if not text:
        return jsonify({'status': 'empty text'}), 400

    threading.Thread(target=type_characters_humanlike, args=(text, wpm), daemon=True).start()
    return jsonify({'status': f'Typing started in Google Chrome at {wpm} WPM!'})


def show_qr_code(url):
    """Generates a clean QR code image and opens it in the default viewer."""
    try:
        qr = qrcode.QRCode(box_size=10, border=3)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        qr_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "connect_qr.png")
        img.save(qr_path)
        
        if sys.platform == 'darwin':
            subprocess.run(["open", qr_path], check=False)
        elif sys.platform.startswith('win'):
            os.startfile(qr_path)
    except Exception as e:
        print(f"Notice opening QR image: {e}")


if __name__ == '__main__':
    port = 5050
    local_ip = get_local_ip()
    url = f"http://{local_ip}:{port}"

    print("=" * 60)
    print("🚀 Faah Autonomous Running!")
    print(f"🔗 Connect your phone to: {url}")
    print("=" * 60)

    # Show QR code image
    show_qr_code(url)

    # Start Flask server
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
