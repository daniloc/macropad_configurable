from adafruit_neokey.neokey1x4 import NeoKey1x4

class PickerCluster():
    
    def __init__(self, i2c_bus):
        self._neokey = NeoKey1x4(i2c_bus, addr=0x30)

    @property
    def active_keys(self) -> [int]:
        
        keys = []
                
        for key in range(4):
            if self._neokey[key]:
                keys.append(key)
        
        return keys
        
    @property
    def pixels(self) -> [Neopixel]:
        return self._neokey.pixels