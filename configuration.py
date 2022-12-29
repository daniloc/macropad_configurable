import json
from adafruit_hid.keycode import Keycode

class Page:

    def __init__(self, pagecontent):
        self.name = pagecontent["name"]
        self.macros = pagecontent["macros"]
    
    def switch(self, display_group, macropad):
        """Activate application settings; update OLED labels and LED
        colors."""
        display_group[13].text = self.name  # Application name
        for i in range(12):
            if i < len(self.macros):  # Key in use, set label + LED color
                macropad.pixels[i] = self.macros[i][0]
                display_group[i].text = self.macros[i][1]
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
    
    def __init__(self, config_file):
        
        self.pages = {}
        
        with open(config_file) as f:
            page_data = json.load(f)
            
        for page in page_data:
        
            keys = page["keys"]
            
            imported_keys = []
            
            for key in keys:
                color_hex_string = "0x" + key["color"]
                color_hex = int(color_hex_string, 16)
                macro = key["macro"]
            
                text_string = macro.get("textContent")
                modifiers = macro.get("modifiers")
            
                imported_sequence = []
            
                if modifiers:
                    for modifier in modifiers:
                        hex_modifier = int(modifier, 16)
                        print(hex_modifier)
                        keycode = Keycode(hex_modifier)
                        imported_sequence.append(hex_modifier)
                        print(imported_sequence)
            
                if text_string:
                    imported_sequence.append(text_string)
            
                configured_key = (color_hex, key["label"], imported_sequence)
                imported_keys.append(configured_key)
            
            imported_page = {"name": page["name"], "macros": imported_keys}
            
            invocation = page["invocation"]
            
            self.pages[tuple(invocation)] = Page(imported_page)
            
    def activate_page(self, invocation, display_group, macropad):
        page = self.pages.get(tuple(invocation), None)
        
        if page != None:
            page.switch(display_group, macropad)
            return True
        else:
            return False