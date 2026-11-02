"""GUI module for Phone Keyboard to PC"""
import tkinter as tk
from tkinter import scrolledtext
import threading
import requests
from pynput.keyboard import Key

from utils import get_local_ip, qr_code_to_photoimage
from server import WebServer
from text_handler import TextHandler
from hotkey_manager import HotkeyManager


class PhoneKeyboardApp:
    """Main application class for Phone Keyboard to PC"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Phone Keyboard to PC")
        self.root.geometry("600x450")
        
        # Initialize components
        self.local_ip = get_local_ip()
        self.port = 5000
        self.text_handler = TextHandler()
        self.hotkey_manager = HotkeyManager()
        self.hotkey_manager.load_config()
        
        # Server setup
        self.web_server = WebServer(
            port=self.port,
            on_text_update=self.handle_text_update,
            on_ping=self.handle_ping
        )
        
        # State variables
        self.typing_mode_enabled = False
        self.receive_text_enabled = True
        self.receive_text_hotkey = Key.f9
        self.receive_text_listener = None
        self.last_receive_text_hotkey_time = 0
        
        # Phone connection status
        self.phone_connected = False
        self.phone_connection_timer = None
        self.phone_connection_timeout = 5.0
        
        # Text tracking
        self.current_text = ""
        self.last_received_text = ""
        self.update_queue_count = 0
        self.queued_text = ""
        
        # GUI elements (will be created in create_widgets)
        self.qr_label = None
        self.status_label = None
        self.toggle_button = None
        self.set_hotkey_button = None
        self.receive_status_button = None
        self.clear_button = None
        self.text_display = None
        self.queue_label = None
        self.phone_status_circle = None
        self.qr_url_label = None
        
        # Setup hotkey listener
        self.hotkey_manager.setup_listener(self.toggle_typing_mode)
        
        # Setup receive text hotkey listener
        self.setup_receive_text_listener()
        
        # Create GUI
        self.create_widgets()
        
        # Setup cleanup
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start polling
        self.poll_text_updates()
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Phone connection status
        phone_status_frame = tk.Frame(self.root)
        phone_status_frame.pack(pady=(10, 5), fill=tk.X)
        
        phone_center_frame = tk.Frame(phone_status_frame)
        phone_center_frame.pack(expand=True)
        
        tk.Label(
            phone_center_frame,
            text="Phone Connected: ",
            font=("Arial", 9)
        ).pack(side=tk.LEFT)
        
        self.phone_status_circle = tk.Label(
            phone_center_frame,
            text="●",
            font=("Arial", 16),
            fg="red"
        )
        self.phone_status_circle.pack(side=tk.LEFT)
        
        # Top row: Server status and QR code
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10, padx=20, fill=tk.X)
        
        right_frame = tk.Frame(top_frame)
        right_frame.pack(side=tk.RIGHT)
        
        self.status_label = tk.Label(
            right_frame,
            text="Server Status: Stopped",
            font=("Arial", 10, "bold"),
            fg="red"
        )
        self.status_label.pack(anchor=tk.E)
        
        qr_frame = tk.Frame(right_frame, width=120, height=140)
        qr_frame.pack(anchor=tk.E, pady=(5, 0))
        qr_frame.pack_propagate(False)
        
        self.qr_url_label = tk.Label(
            qr_frame,
            text=f"http://{self.local_ip}:{self.port}",
            font=("Arial", 9),
            fg="blue"
        )
        self.qr_url_label.pack(anchor=tk.E)
        
        self.qr_label = tk.Label(qr_frame, text="", font=("Arial", 9))
        self.qr_label.pack(anchor=tk.E)
        
        # Checkboxes
        checkbox_frame = tk.Frame(self.root)
        checkbox_frame.pack(pady=(0, 5), padx=20, fill=tk.X)
        
        enter_checkbox_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            checkbox_frame,
            text="Simulate Enter for newlines",
            variable=enter_checkbox_var,
            command=lambda: setattr(self.text_handler, 'simulate_enter', enter_checkbox_var.get()),
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        clipboard_checkbox_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            checkbox_frame,
            text="Copy to clipboard",
            variable=clipboard_checkbox_var,
            command=lambda: setattr(self.text_handler, 'copy_to_clipboard', clipboard_checkbox_var.get()),
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Hotkey buttons
        hotkey_frame = tk.Frame(self.root)
        hotkey_frame.pack(pady=(0, 5), padx=20, fill=tk.X)
        
        left_hotkey_frame = tk.Frame(hotkey_frame)
        left_hotkey_frame.pack(side=tk.LEFT)
        
        self.set_hotkey_button = tk.Button(
            left_hotkey_frame,
            text="Typing Mode: Not Set",
            command=self.start_listening_for_hotkey,
            font=("Arial", 9),
            width=20,
            height=1
        )
        self.set_hotkey_button.pack(side=tk.LEFT, padx=(0, 5), pady=(0, 2))
        
        self.receive_status_button = tk.Button(
            left_hotkey_frame,
            text="Receive: ON (F9)",
            command=self.toggle_receive_text,
            font=("Arial", 9),
            width=20,
            height=1
        )
        self.receive_status_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.clear_button = tk.Button(
            hotkey_frame,
            text="Clear all text",
            command=self.clear_text,
            font=("Arial", 9),
            width=15,
            height=1,
            bg="#e0e0e0",
            fg="black"
        )
        self.clear_button.pack(side=tk.LEFT)
        
        self.update_hotkey_display()
        
        # Text display area
        label_frame = tk.Frame(self.root)
        label_frame.pack(pady=(0, 5), padx=20, fill=tk.X)
        
        tk.Label(
            label_frame,
            text="Text from Website:",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT)
        
        self.queue_label = tk.Label(
            label_frame,
            text="Update queue: 0",
            font=("Arial", 10, "bold"),
            fg="green"
        )
        self.queue_label.pack(side=tk.RIGHT)
        
        self.text_display = scrolledtext.ScrolledText(
            self.root,
            height=8,
            width=50,
            wrap=tk.WORD,
            font=("Arial", 11)
        )
        self.text_display.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        self.text_display.bind("<FocusOut>", self.on_text_focus_out)
        
        self.create_context_menu()
        
        # Start Server button
        self.toggle_button = tk.Button(
            self.root,
            text="Start Local Server",
            command=self.toggle_server,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            width=13,
            height=1
        )
        self.toggle_button.place(x=20, y=10)
        
        self.setup_focus_handling()
        
        # Guide frame
        guide_frame = tk.Frame(self.root, bg="#f5f5f5", relief=tk.FLAT, bd=0)
        guide_frame.place(x=20, y=45)
        
        tk.Label(
            guide_frame,
            text="Quick Guide",
            font=("Arial", 11, "bold"),
            bg="#f5f5f5",
            fg="#000"
        ).pack(anchor=tk.W, pady=(2, 4))
        
        tk.Label(
            guide_frame,
            text="• Start server to sync text\n  from phone to clipboard",
            font=("Arial", 10),
            bg="#f5f5f5",
            fg="#000",
            justify=tk.LEFT,
            anchor=tk.W,
            wraplength=260
        ).pack(anchor=tk.W, pady=(0, 2))
        
        tk.Label(
            guide_frame,
            text="• Press the hotkey to toggle typing mode (types text from the browser window instead of manual input",
            font=("Arial", 10),
            bg="#f5f5f5",
            fg="#000",
            justify=tk.LEFT,
            anchor=tk.W,
            wraplength=260
        ).pack(anchor=tk.W, pady=(0, 2))
        
        guide_frame.update_idletasks()
        guide_frame.lift()
        self.toggle_button.lift()
        self.receive_status_button.lift()
        
        self.update_receive_text_status()
        self.update_phone_connection(False)
    
    def create_context_menu(self):
        """Create right-click context menu"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Cut", command=self.cut_text)
        self.context_menu.add_command(label="Copy", command=self.copy_text)
        self.context_menu.add_command(label="Paste", command=self.paste_text)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Select All", command=self.select_all)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Clear", command=self.clear_text)
        
        self.text_display.bind("<Button-3>", self.show_context_menu)
        self.text_display.bind("<Button-2>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """Show context menu"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def cut_text(self):
        try:
            self.text_display.event_generate("<<Cut>>")
        except:
            pass
    
    def copy_text(self):
        try:
            self.text_display.event_generate("<<Copy>>")
        except:
            pass
    
    def paste_text(self):
        try:
            self.text_display.event_generate("<<Paste>>")
        except:
            pass
    
    def select_all(self):
        self.text_display.tag_add(tk.SEL, "1.0", tk.END)
        self.text_display.mark_set(tk.INSERT, "1.0")
        self.text_display.see(tk.INSERT)
    
    def clear_text(self):
        """Clear all text"""
        self.text_display.delete("1.0", tk.END)
        self.last_received_text = ""
        self.update_queue_count = 0
        self.queued_text = ""
        self.text_handler.reset_typing_state()
        self.update_queue_label()
    
    def setup_focus_handling(self):
        """Setup click handlers to remove focus from text box"""
        def remove_text_focus(event):
            widget_under_cursor = event.widget
            if widget_under_cursor != self.text_display:
                self.root.focus_set()
        
        self.root.bind("<Button-1>", remove_text_focus)
        for widget in [self.status_label, self.qr_label, self.qr_url_label, 
                       self.toggle_button, self.set_hotkey_button, self.clear_button]:
            if hasattr(widget, 'bind'):
                widget.bind("<Button-1>", remove_text_focus)
    
    def update_qr_code(self, url):
        """Update QR code display"""
        try:
            photo = qr_code_to_photoimage(url)
            if photo:
                self.qr_label.config(image=photo, text="")
                self.qr_label.image = photo
        except Exception as e:
            print(f"QR code error: {e}")
            self.qr_label.config(text="QR code unavailable", image="")
    
    def toggle_server(self):
        """Toggle server on/off"""
        if self.web_server.is_running:
            self.stop_server()
        else:
            self.start_server()
    
    def start_server(self):
        """Start the web server"""
        self.web_server.start()
        url = f"http://{self.local_ip}:{self.port}"
        self.status_label.config(text="Server Status: Running", fg="green")
        self.toggle_button.config(text="Stop Server", bg="#f44336")
        self.qr_url_label.config(text=url, fg="blue")
        self.update_qr_code(url)
        self.update_phone_connection(False)
    
    def stop_server(self):
        """Stop the web server"""
        self.web_server.stop()
        url = f"http://{self.local_ip}:{self.port}"
        self.status_label.config(text="Server Status: Stopped", fg="red")
        self.toggle_button.config(text="Start Server", bg="#4CAF50")
        self.qr_url_label.config(text=url, fg="gray")
        self.qr_label.config(image="", text="")
        self.qr_label.image = None
        self.update_phone_connection(False)
    
    def handle_text_update(self, text):
        """Handle text update from server"""
        self.current_text = text
        self.root.after(0, self.process_text_update, text)
    
    def process_text_update(self, text):
        """Process text update in GUI thread"""
        if not self.receive_text_enabled:
            return
        
        if self.typing_mode_enabled:
            self.text_handler.add_to_buffer(text)
            
            if self.text_handler.should_process_buffer():
                self.process_buffered_updates()
            else:
                if self.text_handler.buffer_timer:
                    self.root.after_cancel(self.text_handler.buffer_timer)
                
                self.text_handler.buffer_timer = self.root.after(
                    int(self.text_handler.buffer_timeout * 1000),
                    self.process_buffered_updates
                )
            
            self.root.after(0, self.update_text_display, text)
        else:
            self.text_handler.copy_text(text)
            self.root.after(0, self.update_text_display, text)
    
    def process_buffered_updates(self):
        """Process buffered text updates"""
        latest_text = self.text_handler.process_buffer(
            lambda new_text: self.type_text_thread(new_text)
        )
        self.last_received_text = latest_text
    
    def type_text_thread(self, text):
        """Type text in a separate thread"""
        def type_it():
            self.text_handler.type_text(
                text,
                on_display_update=lambda t: self.root.after(0, self.insert_text_to_display, t)
            )
        
        threading.Thread(target=type_it, daemon=True).start()
    
    def insert_text_to_display(self, text):
        """Insert text into display"""
        try:
            current_display = self.text_display.get("1.0", tk.END)
            if current_display.endswith('\n'):
                current_display = current_display[:-1]
            if not current_display.endswith(text):
                self.text_display.insert(tk.END, text)
                self.text_display.see(tk.END)
        except Exception as e:
            print(f"Error inserting text: {e}")
    
    def update_text_display(self, text):
        """Update text display widget"""
        try:
            has_focus = self.text_display.focus_get() == self.text_display
            new_text_portion = self.text_handler.find_new_text(self.last_received_text, text)
            
            if new_text_portion:
                if not has_focus:
                    current_display = self.text_display.get("1.0", tk.END)
                    if current_display.endswith('\n'):
                        current_display = current_display[:-1]
                    self.text_display.insert(tk.END, new_text_portion)
                    self.last_received_text = text
                    self.text_display.see(tk.END)
                else:
                    self.queued_text += new_text_portion
                    self.update_queue_count += 1
                    self.update_queue_label()
                    self.last_received_text = text
        except Exception as e:
            print(f"Error updating text display: {e}")
    
    def on_text_focus_out(self, event):
        """Handle text box focus out"""
        if self.update_queue_count > 0 and self.queued_text:
            current_display = self.text_display.get("1.0", tk.END)
            if current_display.endswith('\n'):
                current_display = current_display[:-1]
            self.text_display.insert(tk.END, self.queued_text)
            self.text_display.see(tk.END)
            self.update_queue_count = 0
            self.queued_text = ""
            self.update_queue_label()
    
    def update_queue_label(self):
        """Update queue label"""
        self.queue_label.config(text=f"Update queue: {self.update_queue_count}")
        if self.update_queue_count > 0:
            self.queue_label.config(fg="red")
        else:
            self.queue_label.config(fg="green")
    
    def handle_ping(self):
        """Handle ping from phone"""
        self.root.after(0, self.update_phone_connection, True)
    
    def update_phone_connection(self, connected):
        """Update phone connection status"""
        self.phone_connected = connected
        
        if self.phone_connection_timer:
            self.root.after_cancel(self.phone_connection_timer)
            self.phone_connection_timer = None
        
        if connected:
            if hasattr(self, 'phone_status_circle'):
                self.phone_status_circle.config(fg="green")
            self.phone_connection_timer = self.root.after(
                int(self.phone_connection_timeout * 1000),
                lambda: self.update_phone_connection(False)
            )
        else:
            if hasattr(self, 'phone_status_circle'):
                self.phone_status_circle.config(fg="red")
    
    def setup_receive_text_listener(self):
        """Setup listener for receive text toggle (F9)"""
        from pynput import keyboard
        
        self.last_receive_text_hotkey_time = 0
        
        def on_press(key):
            try:
                if self.hotkey_manager.listening_for_hotkey:
                    return
                if self.hotkey_manager.keys_match(key, self.receive_text_hotkey):
                    import time
                    current_time = time.time()
                    if current_time - self.last_receive_text_hotkey_time > 0.5:
                        self.last_receive_text_hotkey_time = current_time
                        self.root.after(0, self.toggle_receive_text)
            except Exception:
                pass
        
        self.receive_text_listener = keyboard.Listener(on_press=on_press)
        self.receive_text_listener.daemon = True
        self.receive_text_listener.start()
    
    def toggle_receive_text(self):
        """Toggle receive text"""
        self.receive_text_enabled = not self.receive_text_enabled
        
        if self.receive_text_enabled:
            try:
                response = requests.get(f'http://localhost:{self.port}/get_text', timeout=1)
                if response.status_code == 200:
                    data = response.json()
                    current_website_text = data.get('text', '')
                    self.current_text = current_website_text
                    self.last_received_text = current_website_text
                    if self.typing_mode_enabled:
                        self.text_handler.reset_typing_state(current_website_text, self.root.after_cancel)
            except Exception:
                self.last_received_text = self.current_text
                if self.typing_mode_enabled:
                    self.text_handler.reset_typing_state(self.current_text, self.root.after_cancel)
        
        self.update_receive_text_status()
    
    def update_receive_text_status(self):
        """Update receive text status display"""
        status = "ON" if self.receive_text_enabled else "OFF"
        if hasattr(self, 'receive_status_button'):
            self.receive_status_button.config(text=f"Receive: {status} (F9)")
            if self.receive_text_enabled:
                self.receive_status_button.config(bg="#4CAF50", fg="white")
            else:
                self.receive_status_button.config(bg="#e0e0e0", fg="black")
    
    def update_hotkey_display(self):
        """Update hotkey display"""
        if self.hotkey_manager.hotkey_key:
            hotkey_str = self.hotkey_manager.get_key_display_name(self.hotkey_manager.hotkey_key)
        else:
            hotkey_str = "Not Set"
        
        status = "ON" if self.typing_mode_enabled else "OFF"
        if hasattr(self, 'set_hotkey_button'):
            self.set_hotkey_button.config(text=f"Typing Mode: {hotkey_str} ({status})")
            if self.typing_mode_enabled:
                self.set_hotkey_button.config(bg="#4CAF50", fg="white")
            else:
                self.set_hotkey_button.config(bg="#e0e0e0", fg="black")
    
    def toggle_typing_mode(self):
        """Toggle typing mode"""
        self.typing_mode_enabled = not self.typing_mode_enabled
        
        if not self.typing_mode_enabled:
            if self.text_handler.update_buffer:
                self.process_buffered_updates()
        else:
            self.text_handler.reset_typing_state(self.current_text, self.root.after_cancel)
        
        self.update_hotkey_display()
    
    def start_listening_for_hotkey(self):
        """Start listening for hotkey"""
        def on_capture():
            self.root.after(0, self.update_hotkey_display)
        
        self.hotkey_manager.start_capture(on_capture)
        if hasattr(self, 'set_hotkey_button'):
            self.set_hotkey_button.config(
                text="Listening... Press any key",
                state=tk.DISABLED,
                bg="#fff3cd",
                fg="black"
            )
            self.root.after(100, lambda: self.set_hotkey_button.config(state=tk.NORMAL))
    
    def poll_text_updates(self):
        """Poll for text updates"""
        if self.web_server.is_running and self.receive_text_enabled:
            try:
                response = requests.get(f'http://localhost:{self.port}/get_text', timeout=1)
                if response.status_code == 200:
                    data = response.json()
                    new_text = data.get('text', '')
                    self.update_text_display(new_text)
            except Exception:
                pass
        
        self.root.after(1000, self.poll_text_updates)
    
    def on_closing(self):
        """Handle window closing"""
        if self.hotkey_manager:
            self.hotkey_manager.stop()
        if self.receive_text_listener:
            try:
                self.receive_text_listener.stop()
            except:
                pass
        if self.web_server.is_running:
            self.web_server.stop()
        self.root.destroy()

