"""Flask server for Phone Keyboard to PC"""
import logging
import sys
import threading
from flask import Flask, render_template_string, request, jsonify
from werkzeug.serving import make_server


class WebServer:
    """Manages the Flask web server"""
    
    def __init__(self, port=5000, on_text_update=None, on_ping=None):
        self.port = port
        self.is_running = False
        self.server = None
        self.server_thread = None
        self.http_server = None
        self.on_text_update = on_text_update
        self.on_ping = on_ping
        self.current_text = ""
    
    def get_html_template(self):
        """Get the HTML template for the web interface"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Phone Keyboard to PC</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                h1 {
                    color: #333;
                    text-align: center;
                }
                textarea {
                    width: 100%;
                    min-height: 200px;
                    padding: 15px;
                    font-size: 16px;
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    box-sizing: border-box;
                    font-family: inherit;
                    resize: vertical;
                }
                textarea:focus {
                    outline: none;
                    border-color: #4CAF50;
                }
                .button-container {
                    margin-top: 15px;
                    display: flex;
                    gap: 10px;
                    justify-content: center;
                }
                .clear-button {
                    background-color: #e0e0e0;
                    color: black;
                    border: none;
                    padding: 12px 24px;
                    font-size: 16px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-family: inherit;
                    font-weight: normal;
                }
                .clear-button:hover {
                    background-color: #d0d0d0;
                }
                .clear-button:active {
                    background-color: #c0c0c0;
                }
                .info {
                    background-color: #e3f2fd;
                    padding: 10px;
                    border-radius: 5px;
                    margin-top: 20px;
                    font-size: 14px;
                    color: #1976d2;
                }
            </style>
        </head>
        <body>
            <h1>📝 Phone Keyboard to PC</h1>
            <textarea id="textInput" placeholder="Type your text here... It will be automatically sent to your computer's clipboard."></textarea>
            <div class="button-container">
                <button class="clear-button" onclick="clearText()">Clear all text</button>
            </div>
            <div class="info">
                ✓ Text is automatically synced to your computer's clipboard
            </div>
            
            <script>
                const textarea = document.getElementById('textInput');
                let lastSentText = '';
                
                function sendText() {
                    const currentText = textarea.value;
                    if (currentText !== lastSentText) {
                        fetch('/update_text', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({text: currentText})
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                lastSentText = currentText;
                            }
                        })
                        .catch(error => console.error('Error:', error));
                    }
                }
                
                let timeout;
                textarea.addEventListener('input', function() {
                    clearTimeout(timeout);
                    timeout = setTimeout(sendText, 300);
                });
                
                textarea.addEventListener('blur', sendText);
                
                window.addEventListener('load', function() {
                    if (textarea.value) {
                        sendText();
                    }
                });
                
                function pingServer() {
                    fetch('/ping', {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    })
                    .catch(error => {
                        console.error('Ping error:', error);
                    });
                }
                
                pingServer();
                setInterval(pingServer, 2000);
                
                function clearText() {
                    textarea.value = '';
                    lastSentText = '';
                    fetch('/clear_text', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({})
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            console.log('Text cleared');
                        }
                    })
                    .catch(error => console.error('Error:', error));
                }
            </script>
        </body>
        </html>
        """
    
    def setup_routes(self):
        """Setup Flask routes"""
        @self.server.route('/')
        def index():
            return render_template_string(self.get_html_template())
        
        @self.server.route('/update_text', methods=['POST'])
        def update_text():
            try:
                data = request.get_json()
                text = data.get('text', '')
                self.current_text = text
                
                if self.on_text_update:
                    self.on_text_update(text)
                
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.server.route('/get_text', methods=['GET'])
        def get_text():
            return jsonify({'text': self.current_text})
        
        @self.server.route('/ping', methods=['GET'])
        def ping():
            if self.on_ping:
                self.on_ping()
            return jsonify({'success': True, 'status': 'connected'})
        
        @self.server.route('/clear_text', methods=['POST'])
        def clear_text_route():
            try:
                self.current_text = ""
                if self.on_text_update:
                    self.on_text_update("")
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
    
    def start(self):
        """Start the Flask web server in a separate thread"""
        if self.is_running:
            return
        
        if self.server_thread and self.server_thread.is_alive():
            self.stop()
            import time
            time.sleep(0.5)
        
        self.is_running = True
        self.server = Flask(__name__)
        self.setup_routes()
        
        def run_server():
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
            log.disabled = True
            
            try:
                cli = sys.modules['flask.cli']
                cli.show_server_banner = lambda *args: None
            except:
                pass
            
            self.http_server = make_server('0.0.0.0', self.port, self.server, threaded=True)
            self.http_server.serve_forever()
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
    
    def stop(self):
        """Stop the Flask web server"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.http_server:
            try:
                self.http_server.shutdown()
            except:
                pass
            self.http_server = None
        
        if self.server_thread and self.server_thread.is_alive():
            import time
            time.sleep(0.2)
    
    def get_current_text(self):
        """Get the current text from the server"""
        return self.current_text

