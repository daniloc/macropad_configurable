"""
A macro/hotkey program for Adafruit MACROPAD. Macro setups are stored in the
/macros folder (configurable below), load up just the ones you're likely to
use. Plug into computer's USB port, use dial to select an application macro
set, press MACROPAD keys to send key sequences and other USB protocols.
"""

# pylint: disable=import-error, unused-import, too-few-public-methods

import os
import time
import displayio
import terminalio
import json
import board
from rotary import RotaryBoard
from picker import PickerCluster

from adafruit_display_shapes.rect import Rect
from adafruit_display_text import label
from adafruit_macropad import MacroPad
from adafruit_hid.keycode import Keycode
from adafruit_neokey.neokey1x4 import NeoKey1x4
from adafruit_seesaw import seesaw, neopixel, rotaryio, digitalio

i2c_bus = board.I2C()
picker_cluster = PickerCluster(i2c_bus)

left_rotary = RotaryBoard(i2c_bus)
left_rotary.pixel.fill(0x220000)


# CONFIGURABLES ------------------------

MACRO_FOLDER = "/macros"
MACRO_FILE = "macro.json"


# CLASSES AND FUNCTIONS ----------------


class App:
    """Class representing a host-side application, for which we have a set
    of macro sequences. Project code was originally more complex and
    this was helpful, but maybe it's excessive now?"""

    def __init__(self, appdata):
        self.name = appdata["name"]
        self.macros = appdata["macros"]

    def switch(self):
        """Activate application settings; update OLED labels and LED
        colors."""
        group[13].text = self.name  # Application name
        for i in range(12):
            if i < len(self.macros):  # Key in use, set label + LED color
                macropad.pixels[i] = self.macros[i][0]
                group[i].text = self.macros[i][1]
            else:  # Key not in use, no label or LED
                macropad.pixels[i] = 0
                group[i].text = ""
        macropad.keyboard.release_all()
        macropad.consumer_control.release()
        macropad.mouse.release_all()
        macropad.stop_tone()
        macropad.pixels.show()
        macropad.display.refresh()

# INITIALIZATION -----------------------

macropad = MacroPad()
macropad.display.auto_refresh = False
macropad.pixels.auto_write = False


# Neokey cluster

for key in range(4):
    picker_cluster.pixels[key] = 0x222222

# Set up displayio group with all the labels
group = displayio.Group()
for key_index in range(12):
    x = key_index % 3
    y = key_index // 3
    group.append(
        label.Label(
            terminalio.FONT,
            text="",
            color=0xFFFFFF,
            anchored_position=(
                (macropad.display.width - 1) * x / 2,
                macropad.display.height - 1 - (3 - y) * 12,
            ),
            anchor_point=(x / 2, 1.0),
        )
    )
group.append(Rect(0, 0, macropad.display.width, 12, fill=0xFFFFFF))
group.append(
    label.Label(
        terminalio.FONT,
        text="",
        color=0x000000,
        anchored_position=(macropad.display.width // 2, -2),
        anchor_point=(0.5, 0.0),
    )
)
macropad.display.show(group)

with open("macro.json") as f:
    pages = json.load(f)

apps = []

for page in pages:

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

    app = {"name": page["name"], "macros": imported_keys}

    apps.append(App(app))


positions = [None, None]
switch_states = [False, False]

app_index = 0
apps[app_index].switch()
pages = {}

# MAIN LOOP ----------------------------

while True:
        
    for encoder_index in range(2):
        position = left_rotary.encoder if encoder_index == 0 else macropad.encoder
        if position != positions[encoder_index]:
            print(position)
            positions[encoder_index] = position
        
        

    # Handle encoder button. If state has changed, and if there's a
    # corresponding macro, set up variables to act on this just like
    # the keypad keys, as if it were a 13th key/macro.
    #macropad.encoder_switch_debounced.update()
    #encoder_switch = macropad.encoder_switch_debounced.pressed
    
    # check Neopixel cluster
    
    picker_cluster.debounce_update()
    
    if len(picker_cluster.active_keys) >= 1:
                
        picker_selection = [0,0,0,0]
    
        for neokey_index in picker_cluster.active_keys:
            picker_selection[neokey_index] = 1
            print(neokey_index)
        
        print("switching to ")
        print(picker_selection)
        
        if pages.get(picker_selection, None) != None:

            pages[picker_selection].switch()
                
        continue
        
    # Check encoders
    
    macropad.encoder_switch_debounced.update()
    left_rotary.encoder_switch_debounced.update()
    
    left_rotary_switch_state = left_rotary.encoder_switch_debounced.pressed
    right_rotary_switch_state = macropad.encoder_switch_debounced.pressed
    
    if left_rotary_switch_state != switch_states[0]:
        print("left rotary")
        key_number = 13
        switch_states[0] = left_rotary_switch_state
    
    if right_rotary_switch_state != switch_states[1]:
        print("right rotary")
        key_number = 12
        switch_states[1] = right_rotary_switch_state
    # Read key events from Macropad
    else:
        event = macropad.keys.events.get()
        if not event or event.key_number >= len(apps[app_index].macros):
            continue  # No key events, or no corresponding macro, resume loop
        key_number = event.key_number
        pressed = event.pressed

    # If code reaches here, a key or the encoder button WAS pressed/released
    # and there IS a corresponding macro available for it...other situations
    # are avoided by 'continue' statements above which resume the loop.
    
    if key_number >= len(apps[app_index].macros):
        continue

    sequence = apps[app_index].macros[key_number][2]
    if pressed:
        # 'sequence' is an arbitrary-length list, each item is one of:
        # Positive integer (e.g. Keycode.KEYPAD_MINUS): key pressed
        # Negative integer: (absolute value) key released
        # Float (e.g. 0.25): delay in seconds
        # String (e.g. "Foo"): corresponding keys pressed & released
        # List []: one or more Consumer Control codes (can also do float delay)
        # Dict {}: mouse buttons/motion (might extend in future)
        if key_number < 12:  # No pixel for encoder button
            macropad.pixels[key_number] = 0xFFFFFF
            macropad.pixels.show()
        for item in sequence:
            if isinstance(item, int):
                if item >= 0:
                    macropad.keyboard.press(item)
                else:
                    macropad.keyboard.release(-item)
            elif isinstance(item, float):
                time.sleep(item)
            elif isinstance(item, str):
                macropad.keyboard_layout.write(item)
            elif isinstance(item, list):
                for code in item:
                    if isinstance(code, int):
                        macropad.consumer_control.release()
                        macropad.consumer_control.press(code)
                    if isinstance(code, float):
                        time.sleep(code)
            elif isinstance(item, dict):
                if "buttons" in item:
                    if item["buttons"] >= 0:
                        macropad.mouse.press(item["buttons"])
                    else:
                        macropad.mouse.release(-item["buttons"])
                macropad.mouse.move(
                    item["x"] if "x" in item else 0,
                    item["y"] if "y" in item else 0,
                    item["wheel"] if "wheel" in item else 0,
                )
                if "tone" in item:
                    if item["tone"] > 0:
                        macropad.stop_tone()
                        macropad.start_tone(item["tone"])
                    else:
                        macropad.stop_tone()
                elif "play" in item:
                    macropad.play_file(item["play"])
    else:
        # Release any still-pressed keys, consumer codes, mouse buttons
        # Keys and mouse buttons are individually released this way (rather
        # than release_all()) because pad supports multi-key rollover, e.g.
        # could have a meta key or right-mouse held down by one macro and
        # press/release keys/buttons with others. Navigate popups, etc.
        for item in sequence:
            if isinstance(item, int):
                if item >= 0:
                    macropad.keyboard.release(item)
            elif isinstance(item, dict):
                if "buttons" in item:
                    if item["buttons"] >= 0:
                        macropad.mouse.release(item["buttons"])
                elif "tone" in item:
                    macropad.stop_tone()
        macropad.consumer_control.release()
        if key_number < 12:  # No pixel for encoder button
            macropad.pixels[key_number] = apps[app_index].macros[key_number][0]
            macropad.pixels.show()
