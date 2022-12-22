from neokey_debounced import NeoKey1x4Debounced


class PickerCluster():
    
    def __init__(self, i2c_bus):
        self._neokey = NeoKey1x4Debounced(i2c_bus, addr=0x30)


    def debounce_update(self):
        self._neokey.debounce_update()

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