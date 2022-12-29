import json
import const


from adafruit_hid.keycode import Keycode

class Encoder:
    def __init__(self, dictionary):
        self.left_turn = Macro(dictionary["leftTurn"])
        self.right_turn = Macro(dictionary["rightTurn"])
        self.press = Macro(dictionary["press"])

class Macro:
    def __init__(self, macro_dictionary):
        
        text_string = macro_dictionary.get("textContent")
        modifiers = macro_dictionary.get("modifiers")
        
        self.sequence = []
        
        if modifiers:
            for modifier in modifiers:
                hex_modifier = int(modifier, 16)
                print(hex_modifier)
                keycode = Keycode(hex_modifier)
                self.sequence.append(hex_modifier)
        
        if text_string:
            self.sequence.append(text_string)
            
class Key:
    def __init__(self, color_hex, label, macro):
        self.color_hex = color_hex
        self.label = label
        self.macro = macro
        

class Page:

    def __init__(self, name, keys, invocation, left_encoder, right_encoder):
        self.name = name
        self.keys = keys
        self.invocation = invocation
        self.left_encoder = left_encoder
        self.right_encoder = right_encoder
        
    def update_picker(self, picker):
        for key in range(4):
            if self.invocation[key] == 1:
                picker.pixels[key] = 0x555511
            else:
                picker.pixels[key] = 0x111111
    
    def switch(self, display_group, macropad, picker):
        """Activate application settings; update OLED labels and LED
        colors."""
        
        self.update_picker(picker)
        
        display_group[13].text = self.name  # Application name
        for i in range(12):
            if i < len(self.keys):  # Key in use, set label + LED color
                macropad.pixels[i] = self.keys[i].color_hex
                display_group[i].text = self.keys[i].label
            else:  # Key not in use, no label or LED
                macropad.pixels[i] = 0
                display_group[i].text = ""
        macropad.keyboard.release_all()
        macropad.consumer_control.release()
        macropad.mouse.release_all()
        macropad.stop_tone()
        macropad.pixels.show()
        macropad.display.refresh()
    
class Configuration:
    
    def __init__(self, config_file, macropad, display_group, picker):
        
        self.pages = {}
        self.macropad = macropad
        self.display_group = display_group
        self.current_page = None
        self.picker = picker
        
        with open(config_file) as f:
            page_data = json.load(f)
           
            
        for page in page_data:
        
            keys = page["keys"]
            
            imported_keys = []
            
            for key in keys:
                color_hex_string = "0x" + key["color"]
                color_hex = int(color_hex_string, 16)
                macro = Macro(key["macro"])
            
                configured_key = Key(color_hex, key["label"], macro)
                imported_keys.append(configured_key)
                
            left_encoder = Encoder(page["rotaryEncoders"][const.LEFT_ENCODER_INDEX])
            right_encoder = Encoder(page["rotaryEncoders"][const.RIGHT_ENCODER_INDEX])
            
            imported_page = Page(page["name"], imported_keys, tuple(page["invocation"]), left_encoder, right_encoder)
            
            self.pages[imported_page.invocation] = imported_page
            
            if self.current_page == None:
                self.activate_page(imported_page.invocation)
                
            
    def activate_page(self, invocation):
        page = self.pages.get(tuple(invocation), None)
        
        if page != None:
            page.switch(self.display_group, self.macropad, self.picker)
            self.current_page = page
            
    def macropad_keypress(self, key_index, is_pressed):
        if key_index >= len(self.current_page.keys):
            return
        
        sequence = self.current_page.keys[key_index].macro.sequence
        
        if is_pressed:
            # 'sequence' is an arbitrary-length list, each item is one of:
            # Positive integer (e.g. Keycode.KEYPAD_MINUS): key pressed
            # Negative integer: (absolute value) key released
            # Float (e.g. 0.25): delay in seconds
            # String (e.g. "Foo"): corresponding keys pressed & released
            # List []: one or more Consumer Control codes (can also do float delay)
            # Dict {}: mouse buttons/motion (might extend in future)
            if key_index < 12:  # No pixel for encoder button
                self.macropad.pixels[key_index] = 0xFFFFFF
                self.macropad.pixels.show()
            for item in sequence:
                if isinstance(item, int):
                    if item >= 0:
                        self.macropad.keyboard.press(item)
                    else:
                        self.macropad.keyboard.release(-item)
                elif isinstance(item, float):
                    time.sleep(item)
                elif isinstance(item, str):
                    self.macropad.keyboard_layout.write(item)
                elif isinstance(item, list):
                    for code in item:
                        if isinstance(code, int):
                            self.macropad.consumer_control.release()
                            self.macropad.consumer_control.press(code)
                        if isinstance(code, float):
                            time.sleep(code)
                elif isinstance(item, dict):
                    if "buttons" in item:
                        if item["buttons"] >= 0:
                            self.macropad.mouse.press(item["buttons"])
                        else:
                            self.macropad.mouse.release(-item["buttons"])
                    macropad.mouse.move(
                        item["x"] if "x" in item else 0,
                        item["y"] if "y" in item else 0,
                        item["wheel"] if "wheel" in item else 0,
                    )
                    if "tone" in item:
                        if item["tone"] > 0:
                            self.macropad.stop_tone()
                            self.macropad.start_tone(item["tone"])
                        else:
                            self.macropad.stop_tone()
                    elif "play" in item:
                        self.macropad.play_file(item["play"])
        else:
            # Release any still-pressed keys, consumer codes, mouse buttons
            # Keys and mouse buttons are individually released this way (rather
            # than release_all()) because pad supports multi-key rollover, e.g.
            # could have a meta key or right-mouse held down by one macro and
            # press/release keys/buttons with others. Navigate popups, etc.
            for item in sequence:
                if isinstance(item, int):
                    if item >= 0:
                        self.macropad.keyboard.release(item)
                elif isinstance(item, dict):
                    if "buttons" in item:
                        if item["buttons"] >= 0:
                            self.macropad.mouse.release(item["buttons"])
                    elif "tone" in item:
                        self.macropad.stop_tone()
            self.macropad.consumer_control.release()
            if key_index < 12:  # No pixel for encoder button
                self.macropad.pixels[key_index] = self.current_page.keys[key_index].color_hex
                self.macropad.pixels.show()
            
    def handleEncoderChange(self, encoder_position, direction):
        if encoder_position == const.LEFT_ENCODER_INDEX:
            current_page.left_encoder
        else:
            current_page.right_encoder
