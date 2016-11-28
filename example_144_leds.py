import pycom
import math
from utime import sleep_ms


from ws2812 import WS2812


ring = WS2812(ledNumber=144,brightness=100)

def data_generator(ledNumber):
    data = [(0, 0, 0) for i in range(ledNumber)]
    step = 0
    while True:
        red = int((1 + math.sin(step * 0.1324)) * 127)
        green = int((1 + math.sin(step * 0.1654)) * 127)
        blue = int((1 + math.sin(step * 0.1)) * 127)
        data[step % ledNumber] = (red, green, blue)
        yield data
        step += 1


pycom.rgbled(0x111111)
for data in data_generator(ring.ledNumber):
    ring.show(data)
    #sleep_ms( 1 )
