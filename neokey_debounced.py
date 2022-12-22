from micropython import const
from adafruit_seesaw import neopixel, digitalio
from adafruit_seesaw.seesaw import Seesaw
from adafruit_debouncer import Debouncer

try:
    import typing  # pylint: disable=unused-import
    from busio import I2C
except ImportError:
    pass

_NEOKEY1X4_ADDR = const(0x30)

_NEOKEY1X4_NEOPIX_PIN = const(3)

_NEOKEY1X4_NUM_ROWS = const(1)
_NEOKEY1X4_NUM_COLS = const(4)
_NEOKEY1X4_NUM_KEYS = const(4)


class NeoKey1x4Debounced(Seesaw):
    """Driver for the Adafruit NeoKey 1x4."""

    def __init__(
        self, i2c_bus: I2C, interrupt: bool = False, addr: int = _NEOKEY1X4_ADDR
    ) -> None:
        super().__init__(i2c_bus, addr)
        self.interrupt_enabled = interrupt
        self.pixels = neopixel.NeoPixel(
            self,
            _NEOKEY1X4_NEOPIX_PIN,
            _NEOKEY1X4_NUM_KEYS,
            brightness=0.2,
            pixel_order=neopixel.GRB,
        )
        # set the pins to inputs, pullups
        self.debounced_switches = []
        for pin_number in range(4, 8):
            self.pin_mode(pin_number, self.INPUT_PULLUP)
            pin = digitalio.DigitalIO(self, pin_number)
            self.debounced_switches.append(Debouncer(pin, 0.1))
            
        
    def debounce_update(self):
        for key in self.debounced_switches:
            key.update()
            
    def __getitem__(self, index: int) -> bool:
        if not isinstance(index, int) or (index < 0) or (index > 3):
            raise RuntimeError("Index must be 0 thru 3")
        return not self.debounced_switches[index].value