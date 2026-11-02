"""Text processing and typing functionality for Phone Keyboard to PC"""
import time
import random
import subprocess
import pyperclip
from pynput.keyboard import Key, Controller as KeyboardController


def bring_chrome_to_front():
    """
    Executes AppleScript to find an active application named 'Google Chrome'
    and brings it directly to the front so typing lands inside the active tab.
    """
    applescript = '''tell application "System Events"
    set isRunning to (exists (processes where name is "Google Chrome"))
end tell
if isRunning then
    tell application "Google Chrome" to activate
    return "activated"
else
    return "not_running"
end if'''
    try:
        res = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True, check=False)
        if res.stdout.strip() == "activated":
            # 1-second safety pause right after bringing Chrome to front
            time.sleep(1.0)
            return True
    except Exception as e:
        print(f"Error bringing Chrome to front: {e}")
    return False


class TextHandler:
    """Handles text processing, clipboard operations, and typing simulation"""
    
    def __init__(self):
        self.keyboard_controller = KeyboardController()
        self.simulate_enter = False
        self.copy_to_clipboard = True
        
        # Update buffering for voice-to-text corrections
        self.update_buffer = []
        self.buffer_update_count = 0
        self.buffer_timer = None
        self.last_typed_text = ""
        self.last_buffered_text = ""
        self.buffer_timeout = 0.5
        self.buffer_size = 2
    
    def find_new_text(self, old_text, new_text):
        """Find the new portion of text that was added"""
        if not old_text:
            return new_text
        
        if new_text.startswith(old_text):
            return new_text[len(old_text):]
        
        # Find the longest common prefix
        common_length = 0
        min_len = min(len(old_text), len(new_text))
        for i in range(min_len):
            if old_text[i] == new_text[i]:
                common_length += 1
            else:
                break
        
        return new_text[common_length:]
    
    def copy_text(self, text):
        """Copy text to clipboard"""
        if self.copy_to_clipboard:
            try:
                pyperclip.copy(text)
            except Exception as e:
                print(f"Clipboard error: {e}")
    
    def type_text(self, text, on_display_update=None):
        """Simulate typing text character by character with human-like randomized speeds and micro-pauses"""
        if not text:
            return
        
        # Bring Google Chrome to the front and pause 1s for focus
        bring_chrome_to_front()
        
        if on_display_update:
            on_display_update(text)
        
        try:
            for char in text:
                if char == '\n':
                    if self.simulate_enter:
                        self.keyboard_controller.press(Key.enter)
                        self.keyboard_controller.release(Key.enter)
                elif char == '\t':
                    self.keyboard_controller.press(Key.tab)
                    self.keyboard_controller.release(Key.tab)
                else:
                    self.keyboard_controller.type(char)
                
                # Human-like randomized delay between keystrokes
                delay = random.uniform(0.03, 0.08)
                
                # Natural micro-pauses at punctuation, newlines, or word boundaries
                if char in ('.', '!', '?', '\n'):
                    delay += random.uniform(0.2, 0.45)
                elif char in (',', ';', ':'):
                    delay += random.uniform(0.1, 0.2)
                elif char == ' ':
                    delay += random.uniform(0.02, 0.06)
                
                time.sleep(delay)
        except Exception as e:
            print(f"Error typing text: {e}")
    
    def add_to_buffer(self, text):
        """Add text update to buffer for voice-to-text corrections"""
        if text != self.last_buffered_text:
            self.buffer_update_count += 1
            self.last_buffered_text = text
        
        if not self.update_buffer or self.update_buffer[-1] != text:
            self.update_buffer.append(text)
    
    def process_buffer(self, on_process):
        """Process buffered updates - use the latest complete text"""
        if not self.update_buffer:
            return
        
        latest_text = self.update_buffer[-1]
        
        # Clear buffer
        self.update_buffer = []
        self.buffer_update_count = 0
        self.last_buffered_text = ""
        self.buffer_timer = None
        
        # Find what's new
        new_text_portion = self.find_new_text(self.last_typed_text, latest_text)
        
        if new_text_portion and on_process:
            on_process(new_text_portion)
            self.last_typed_text = latest_text
        
        return latest_text
    
    def should_process_buffer(self):
        """Check if buffer should be processed immediately"""
        return self.buffer_update_count >= self.buffer_size
    
    def reset_typing_state(self, current_text="", cancel_timer=None):
        """Reset typing state"""
        self.last_typed_text = current_text
        self.update_buffer = []
        self.buffer_update_count = 0
        self.last_buffered_text = ""
        if self.buffer_timer and cancel_timer:
            cancel_timer(self.buffer_timer)
            self.buffer_timer = None

