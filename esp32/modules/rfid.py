from machine import Pin, SPI
from mfrc522 import MFRC522

spi = SPI(2, baudrate=2500000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(23), miso=Pin(19))
spi.init()

rdr = MFRC522(spi=spi, gpioRst=4, gpioCs=0)

def read_uid():
    (stat, tag_type) = rdr.request(rdr.REQIDL)
    if stat != rdr.OK:
        return None

    (stat, raw_uid) = rdr.anticoll()
    if stat != rdr.OK:
        return None

    uid = raw_uid[:-1]  # 去掉 CRC
    return " ".join(["{:02X}".format(x) for x in uid])