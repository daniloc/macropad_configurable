import json
from adafruit_hid.keycode import Keycode

class Page:

    def __init__(self, pagecontent):
        self.name = pagecontent["name"]
        self.macros = pagecontent["macros"]
        self.invocation = pagecontent["invocation"]
        
    def update_picker(self, picker):
        for key in range(4):
            if self.invocation[key] == 1:
                picker.pixels[key] = 0x333333
            else:
                picker.pixels[key] = 0x000000
    
    def switch(self, display_group, macropad, picker):
        """Activate application settings; update OLED labels and LED
        colors."""
        
        self.update_picker(picker)
        
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
    
    def __init__(self, config_file, macropad, display_group, picker):
        
        self.pages = {}
        self.macropad = macropad
        self.display_group = display_group
        self.active_page = None
        self.picker = picker
        
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
            
            page_dictionary = {"name": page["name"], "macros": imported_keys, "invocation": tuple(page["invocation"])}
            
            imported_page = Page(page_dictionary)
            
            self.pages[imported_page.invocation] = imported_page
            
            if self.active_page == None:
                self.active_page = imported_page
                
        self.activate_page(self.active_page.invocation)
            
    def activate_page(self, invocation):
        page = self.pages.get(tuple(invocation), None)
        
        if page != None:
            page.switch(self.display_group, self.macropad, self.picker)
