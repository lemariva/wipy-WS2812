# -*- coding: utf-8 -*-
# Based on https://github.com/JanBednarik/micropython-ws2812
# Adapted for LoPy by @aureleq
# Adapted for WiPy by Johannes Gaa & Mauro Riva (lemariva.com)
# Adapted for Wemos by Mauro Riva (lemariva.com)

import gc
from uos import uname
from machine import SPI
from machine import Pin
from machine import disable_irq
from machine import enable_irq

class WS2812:
    """
    Driver for WS2812 RGB LEDs. May be used for controlling single LED or chain
    of LEDs.

    Example of use:

        chain = WS2812(ledNumber=4)
        data = [
            (255, 0, 0),    # red
            (0, 255, 0),    # green
            (0, 0, 255),    # blue
            (85, 85, 85),   # white
        ]
        chain.show(data)

    Version: 1.0
    """
    # Values to put inside SPi register for each color's bit
    buf_bytes = (0xE0E0, 0xFCE0, 0xE0FC, 0xFCFC)

    def __init__(self, ledNumber=1, brightness=100, dataPin='P22'):
        """
        Params:
        * ledNumber = count of LEDs
        * brightness = light brightness (integer : 0 to 100%)
        * dataPin = pin to connect data channel (LoPy only)
        """
        self.ledNumber = ledNumber
        self.brightness = brightness

        # Prepare SPI data buffer (8 bytes for each color)
        self.buf_length = self.ledNumber * 3 * 8
        self.buf = bytearray(self.buf_length)

        # SPI init
        # Bus 0, 8MHz => 125 ns by bit, 8 clock cycle when bit transfert+2 clock cycle between each transfert
        # => 125*10=1.25 us required by WS2812
        if uname().sysname == 'LoPy':   # LoPy
            self.spi = SPI(0, SPI.MASTER, baudrate=8000000, polarity=0, phase=1, pins=(None, dataPin, None))
            Pin(dataPin, mode=Pin.OUT, pull=Pin.PULL_DOWN)
        elif  uname().machine == 'WiPy with ESP32': # Wipy 2.0
            self.spi = SPI(0, SPI.MASTER, baudrate=8000000, polarity=0, phase=1, pins=None)
            Pin('P11', mode=Pin.OUT, pull=Pin.PULL_DOWN, alt=10)
        elif uname().machine == 'ESP32 module with ESP32': # Wemos ESP-WROOM-32
            mosi = Pin(23, mode = Pin.OUT, pull=Pin.PULL_DOWN)
            miso = Pin(19, mode = Pin.IN)
            sck =  Pin(18, mode = Pin.OUT, pull=Pin.PULL_DOWN)
            self.spi = SPI(1, baudrate=8000000, polarity=0, phase=1, sck = sck, mosi = mosi, miso = miso)

        # Turn LEDs off
        self.show([])

    def show(self, data):
        """
        Show RGB data on LEDs. Expected data = [(R, G, B), ...] where R, G and B
        are intensities of colors in range from 0 to 255. One RGB tuple for each
        LED. Count of tuples may be less than count of connected LEDs.
        """
        self.fill_buf(data)
        self.send_buf()

    def send_buf(self):
        """
        Send buffer over SPI.
        """
        if uname().machine != 'ESP32 module with ESP32':
            disable_irq()  # wemos has problems with this
        self.spi.write(self.buf)
        if uname().machine != 'ESP32 module with ESP32':
            enable_irq()   # wemos has problems with this
        gc.collect()

    def update_buf(self, data, start=0):
        """
        Fill a part of the buffer with RGB data.

        Order of colors in buffer is changed from RGB to GRB because WS2812 LED
        has GRB order of colors. Each color is represented by 4 bytes in buffer
        (1 byte for each 2 bits).

        Returns the index of the first unfilled LED

        Note: If you find this function ugly, it's because speed optimisations
        beated purity of code.
        """

        buf = self.buf
        buf_bytes = self.buf_bytes
        brightness = self.brightness

        index = start * 24
        for red, green, blue in data:
            red = int(red * brightness // 100)
            green = int(green * brightness // 100)
            blue = int(blue * brightness // 100)

            buf[index] = buf_bytes[green >> 6 & 0x03]
            buf[index+2] = buf_bytes[green >> 4 & 0x03]
            buf[index+4] = buf_bytes[green >> 2 & 0x03]
            buf[index+6] = buf_bytes[green & 0x03]

            buf[index+8] = buf_bytes[red >> 6 & 0x03]
            buf[index+10] = buf_bytes[red >> 4 & 0x03]
            buf[index+12] = buf_bytes[red >> 2 & 0x03]
            buf[index+14] = buf_bytes[red & 0x03]

            buf[index+16] = buf_bytes[blue >> 6 & 0x03]
            buf[index+18] = buf_bytes[blue >> 4 & 0x03]
            buf[index+20] = buf_bytes[blue >> 2 & 0x03]
            buf[index+22] = buf_bytes[blue & 0x03]

            index += 24

        return index // 24

    def fill_buf(self, data):
        """
        Fill buffer with RGB data.

        All LEDs after the data are turned off.
        """
        end = self.update_buf(data)

        # Turn off the rest of the LEDs
        buf = self.buf
        off = self.buf_bytes[0]
        for index in range(end * 24, self.buf_length):
            buf[index] = off
            index += 2

    def set_brightness(self, brightness):
        """
        Set brighness of all leds
        """
        self.brightness = brightness
