import storage
import board, digitalio

# If not pressed, the key will be at +V (due to the pull-up).
button = digitalio.DigitalInOut(board.KEY12)
button.pull = digitalio.Pull.UP

#if button.value:
   #storage.disable_usb_drive()