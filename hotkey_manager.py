"""Hotkey management for Phone Keyboard to PC"""
import json
import os
import time
from pynput import keyboard
from pynput.keyboard import Key, KeyCode


class HotkeyManager:
    """Manages hotkey configuration and listening"""
    
    def __init__(self, config_file="hotkey_config.json"):
        self.config_file = config_file
        self.hotkey_key = None
        self.hotkey_key_str = None
        self.listening_for_hotkey = False
        self.capture_listener = None
        self.hotkey_listener = None
        self.last_hotkey_time = 0
        self.on_hotkey_pressed = None  # Callback function
        
    def load_config(self):
        """Load hotkey configuration from file"""
        default_key = Key.f8
        default_key_str = 'f8'
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.hotkey_key_str = config.get('key', default_key_str)
                    self.hotkey_key = self.string_to_key(self.hotkey_key_str)
            else:
                self.hotkey_key_str = default_key_str
                self.hotkey_key = default_key
        except Exception as e:
            print(f"Error loading hotkey config: {e}")
            self.hotkey_key_str = default_key_str
            self.hotkey_key = default_key
    
    def save_config(self):
        """Save hotkey configuration to file"""
        try:
            if self.hotkey_key_str:
                key_to_save = self.hotkey_key_str
            else:
                key_to_save = self.key_to_string(self.hotkey_key)
            
            config = {'key': key_to_save}
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving hotkey config: {e}")
    
    def vk_to_numpad(self, vk):
        """Convert virtual key code to numpad key string"""
        numpad_vk_map = {
            96: 'num_0', 97: 'num_1', 98: 'num_2', 99: 'num_3', 100: 'num_4',
            101: 'num_5', 102: 'num_6', 103: 'num_7', 104: 'num_8', 105: 'num_9',
            106: 'num_multiply', 107: 'num_add', 108: 'num_enter',
            109: 'num_subtract', 110: 'num_decimal', 111: 'num_divide',
        }
        return numpad_vk_map.get(vk)
    
    def key_to_string(self, key):
        """Convert a key (char or Key object) to string representation"""
        if isinstance(key, str):
            return key
        
        if hasattr(key, 'vk'):
            numpad_key = self.vk_to_numpad(key.vk)
            if numpad_key:
                return numpad_key
        
        if hasattr(key, 'name'):
            return key.name.lower()
        
        if hasattr(key, 'char') and key.char:
            return key.char.lower()
        
        key_str = str(key).lower().replace("'", "").replace("key.", "")
        if hasattr(key, 'vk'):
            return f"vk_{key.vk}"
        
        return key_str
    
    def string_to_key(self, key_str):
        """Convert string representation back to key (char or Key object)"""
        if not key_str:
            return None
        
        key_str = key_str.lower()
        
        if key_str.startswith('vk_'):
            try:
                vk = int(key_str[3:])
                return KeyCode.from_vk(vk)
            except:
                pass
        
        if key_str.startswith('f') and len(key_str) > 1:
            try:
                num = int(key_str[1:])
                if 1 <= num <= 19:
                    return getattr(Key, f'f{num}', None)
            except:
                pass
        
        if key_str.startswith('num_'):
            num_key = key_str.replace('num_', '')
            if num_key.isdigit() or num_key in ['enter', 'lock', 'divide', 'multiply', 'subtract', 'add', 'decimal']:
                key_obj = getattr(Key, key_str, None)
                if key_obj:
                    return key_obj
                numpad_to_vk = {
                    'num_0': 96, 'num_1': 97, 'num_2': 98, 'num_3': 99, 'num_4': 100,
                    'num_5': 101, 'num_6': 102, 'num_7': 103, 'num_8': 104, 'num_9': 105,
                    'num_multiply': 106, 'num_add': 107, 'num_subtract': 109,
                    'num_decimal': 110, 'num_divide': 111
                }
                if key_str in numpad_to_vk:
                    return KeyCode.from_vk(numpad_to_vk[key_str])
        
        try:
            return getattr(Key, key_str, None)
        except:
            pass
        
        return key_str
    
    def get_key_display_name(self, key):
        """Get a human-readable name for a key"""
        if isinstance(key, str):
            if key.startswith('vk_'):
                try:
                    vk = int(key[3:])
                    numpad_key = self.vk_to_numpad(vk)
                    if numpad_key:
                        num_part = numpad_key[4:]
                        if num_part.isdigit():
                            return f"Num{num_part}"
                        else:
                            return f"Num{num_part.title()}"
                except:
                    pass
            if key.startswith('num_'):
                num_part = key[4:]
                if num_part.isdigit():
                    return f"Num{num_part}"
                else:
                    return f"Num{num_part.title()}"
            return key.upper()
        
        if hasattr(key, 'vk'):
            numpad_key = self.vk_to_numpad(key.vk)
            if numpad_key:
                num_part = numpad_key[4:]
                if num_part.isdigit():
                    return f"Num{num_part}"
                else:
                    return f"Num{num_part.title()}"
        
        if hasattr(key, 'name'):
            name = key.name
            if name.startswith('f') and name[1:].isdigit():
                return name.upper()
            elif name.startswith('num_'):
                num_part = name[4:]
                if num_part.isdigit():
                    return f"Num{num_part}"
                else:
                    return f"Num{num_part.title()}"
            else:
                return name.replace('_', ' ').title()
        elif hasattr(key, 'char') and key.char:
            return key.char.upper()
        else:
            key_str = str(key).replace("'", "").replace("Key.", "")
            return key_str.upper()
    
    def keys_match(self, pressed_key, stored_key):
        """Check if a pressed key matches the stored hotkey"""
        if not stored_key:
            return False
        
        if hasattr(pressed_key, 'vk') and hasattr(stored_key, 'vk'):
            return pressed_key.vk == stored_key.vk
        
        if isinstance(stored_key, str):
            if stored_key.startswith('vk_'):
                if hasattr(pressed_key, 'vk'):
                    try:
                        stored_vk = int(stored_key[3:])
                        return pressed_key.vk == stored_vk
                    except:
                        pass
            if stored_key.startswith('num_'):
                if hasattr(pressed_key, 'vk'):
                    numpad_key = self.vk_to_numpad(pressed_key.vk)
                    if numpad_key:
                        return numpad_key == stored_key
            if hasattr(pressed_key, 'char') and pressed_key.char:
                return pressed_key.char.lower() == stored_key.lower()
            return False
        
        if hasattr(stored_key, 'vk'):
            if hasattr(pressed_key, 'vk'):
                return pressed_key.vk == stored_key.vk
            return False
        
        if hasattr(stored_key, 'name'):
            if hasattr(pressed_key, 'name'):
                return pressed_key.name == stored_key.name
            return False
        
        if hasattr(stored_key, 'char') and stored_key.char:
            if hasattr(pressed_key, 'char') and pressed_key.char:
                return pressed_key.char.lower() == stored_key.char.lower()
            return False
        
        pressed_str = self.key_to_string(pressed_key)
        stored_str = self.key_to_string(stored_key)
        return pressed_str == stored_str
    
    def setup_listener(self, callback):
        """Setup global hotkey listener"""
        self.on_hotkey_pressed = callback
        
        if not self.hotkey_key:
            return
        
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except:
                pass
        
        self.last_hotkey_time = 0
        
        def on_press(key):
            try:
                if self.listening_for_hotkey:
                    return
                
                if self.keys_match(key, self.hotkey_key):
                    current_time = time.time()
                    if current_time - self.last_hotkey_time > 0.5:
                        self.last_hotkey_time = current_time
                        if self.on_hotkey_pressed:
                            self.on_hotkey_pressed()
            except Exception:
                pass
        
        self.hotkey_listener = keyboard.Listener(on_press=on_press)
        self.hotkey_listener.daemon = True
        self.hotkey_listener.start()
    
    def start_capture(self, on_capture):
        """Start listening for a single key press to set as hotkey"""
        if self.listening_for_hotkey:
            return
        
        if self.capture_listener:
            try:
                self.capture_listener.stop()
            except:
                pass
        
        self.listening_for_hotkey = True
        
        def on_press(key):
            try:
                if key in [Key.ctrl, Key.ctrl_l, Key.ctrl_r, 
                          Key.shift, Key.shift_l, Key.shift_r,
                          Key.alt, Key.alt_l, Key.alt_r,
                          Key.cmd, Key.cmd_l, Key.cmd_r]:
                    return
                
                self.hotkey_key = key
                self.hotkey_key_str = self.key_to_string(key)
                self.save_config()
                self.setup_listener(self.on_hotkey_pressed)
                
                self.listening_for_hotkey = False
                if self.capture_listener:
                    try:
                        self.capture_listener.stop()
                    except:
                        pass
                    self.capture_listener = None
                
                if on_capture:
                    on_capture()
            except Exception as e:
                print(f"Error capturing hotkey: {e}")
        
        self.capture_listener = keyboard.Listener(on_press=on_press)
        self.capture_listener.daemon = True
        self.capture_listener.start()
    
    def stop(self):
        """Stop all listeners"""
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except:
                pass
        if self.capture_listener:
            try:
                self.capture_listener.stop()
            except:
                pass

