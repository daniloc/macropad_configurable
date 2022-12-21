from micropython import const
from adafruit_seesaw import seesaw, neopixel, rotaryio, digitalio
from adafruit_seesaw.seesaw import Seesaw
from adafruit_debouncer import Debouncer


try:
    import typing  # pylint: disable=unused-import
    from busio import I2C
except ImportError:
    pass

_ROTARYBOARD_ADDR = const(0x36)

class RotaryBoard(Seesaw):
    
    pixel: NeoPixel
    
    def __init__(self, i2c_bus: I2C, addr: int = _ROTARYBOARD_ADDR) -> None:
        super().__init__(i2c_bus, addr)    
        #seesaw = seesaw.Seesaw(i2c_bus, addr=0x36)
        seesaw_product = (self.get_version() >> 16) & 0xFFFF
        print("Found product {}".format(seesaw_product))
        if seesaw_product != 4991:
            print("Wrong firmware loaded?  Expected 4991")
            
        self.pin_mode(24, self.INPUT_PULLUP)
        # Define rotary encoder and encoder switch:
        self._encoder = rotaryio.IncrementalEncoder(self)
        self._encoder_switch = digitalio.DigitalIO(self, 24)
        self._debounced_switch = Debouncer(self._encoder_switch)
            
        self.pixel = neopixel.NeoPixel(self, 6, 1)
        self.pixel.brightness = 0.1
        self.pixel.fill(0x222222)
        
    @property
    def encoder(self) -> int:
        """
        The rotary encoder relative rotation position. Always begins at 0 when the code is run, so
        the value returned is relative to the initial location.
        The following example prints the relative position to the serial console.
        .. code-block:: python
            from adafruit_macropad import MacroPad
            macropad = MacroPad()
            while True:
                print(macropad.encoder)
        """
        return self._encoder.position * -1
        
    @property
    def encoder_switch(self) -> bool:
        """
        The rotary encoder switch. Returns ``True`` when pressed.
        The following example prints the status of the rotary encoder switch to the serial console.
        .. code-block:: python
            from adafruit_macropad import MacroPad
            macropad = MacroPad()
            while True:
                print(macropad.encoder_switch)
        """
        return not self._encoder_switch.value
        
    @property
    def encoder_switch_debounced(self) -> Debouncer:
        """
        The rotary encoder switch debounced. Allows for ``encoder_switch_debounced.pressed`` and
        ``encoder_switch_debounced.released``. Requires you to include
        ``encoder_switch_debounced.update()`` inside your loop.
        The following example prints to the serial console when the rotary encoder switch is
        pressed and released.
        .. code-block:: python
            from adafruit_macropad import MacroPad
            macropad = MacroPad()
            while True:
                macropad.encoder_switch_debounced.update()
                if macropad.encoder_switch_debounced.pressed:
                    print("Pressed!")
                if macropad.encoder_switch_debounced.released:
                    print("Released!")
        """
        self._debounced_switch.pressed = self._debounced_switch.fell
        self._debounced_switch.released = self._debounced_switch.rose
        return self._debounced_switch