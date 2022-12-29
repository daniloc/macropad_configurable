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
import board
from rotary import RotaryBoard
from picker import PickerCluster
from configuration import Configuration

from adafruit_display_shapes.rect import Rect
from adafruit_display_text import label
from adafruit_macropad import MacroPad
from adafruit_hid.keycode import Keycode
from adafruit_neokey.neokey1x4 import NeoKey1x4
from adafruit_seesaw import seesaw, neopixel, rotaryio, digitalio

import const

i2c_bus = board.I2C()
picker_cluster = PickerCluster(i2c_bus)

left_rotary = RotaryBoard(i2c_bus)
left_rotary.pixel.fill(0x220000)


# INITIALIZATION -----------------------

macropad = MacroPad()
macropad.display.auto_refresh = False
macropad.pixels.auto_write = False

# Neokey cluster

for key in range(4):
    picker_cluster.pixels[key] = 0x222222

# Set up displayio group with all the labels
display_group = displayio.Group()
for key_index in range(12):
    x = key_index % 3
    y = key_index // 3
    display_group.append(
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
display_group.append(Rect(0, 0, macropad.display.width, 12, fill=0xFFFFFF))
display_group.append(
    label.Label(
        terminalio.FONT,
        text="",
        color=0x000000,
        anchored_position=(macropad.display.width // 2, -2),
        anchor_point=(0.5, 0.0),
    )
)
macropad.display.show(display_group)

MACRO_FILE = "macro.json"
configuration = Configuration(MACRO_FILE, macropad, display_group, picker_cluster)

positions = [0, 0]
switch_states = [False, False]


# MAIN LOOP ----------------------------

while True:
        
    for encoder_index in range(2):
        if encoder_index == const.LEFT_ENCODER_INDEX:
            new_position = left_rotary.encoder
        else:
            new_position = macropad.encoder
            
        old_position = positions[encoder_index]

        if new_position > old_position:
            configuration.rotary_turn(encoder_index, const.DIRECTION_RIGHT)
        if new_position < old_position:
            configuration.rotary_turn(encoder_index, const.DIRECTION_LEFT)
            
        positions[encoder_index] = new_position
                
    # check Neopixel cluster
    
    picker_cluster.debounce_update()
    
    if len(picker_cluster.active_keys) > 0:
                
        picker_selection = [0,0,0,0]
    
        for neokey_index in picker_cluster.active_keys:
            picker_selection[neokey_index] = 1
            print(neokey_index)
        
        print("switching to ")
        print(picker_selection)
                
        configuration.activate_page(picker_selection)
                
        continue
        
    # Check encoders
    macropad.encoder_switch_debounced.update()
    left_rotary.encoder_switch_debounced.update()
    
    left_rotary_switch_state = left_rotary.encoder_switch_debounced.pressed
    right_rotary_switch_state = macropad.encoder_switch_debounced.pressed
    
    if left_rotary_switch_state != switch_states[const.LEFT_ENCODER_INDEX]:
        print("left rotary")
        key_number = 13
        switch_states[const.LEFT_ENCODER_INDEX] = left_rotary_switch_state
        configuration.macropad_keypress(key_number, left_rotary.encoder_switch_debounced.pressed)
    
    if right_rotary_switch_state != switch_states[const.RIGHT_ENCODER_INDEX]:
        print("right rotary")
        key_number = 12
        switch_states[const.RIGHT_ENCODER_INDEX] = right_rotary_switch_state
        configuration.macropad_keypress(key_number, macropad.encoder_switch_debounced.pressed)
    # Read key events from Macropad
    else:
        event = macropad.keys.events.get()
        if not event:
            continue  # No key events, or no corresponding macro, resume loop
        key_number = event.key_number
        pressed = event.pressed
        
        configuration.macropad_keypress(key_number, pressed)

    # If code reaches here, a key or the encoder button WAS pressed/released
    # and there IS a corresponding macro available for it...other situations
    # are avoided by 'continue' statements above which resume the loop.

    
    