from machine import SoftI2C, Pin
from lcd1602 import LCD

i2c = SoftI2C(scl=Pin(27), sda=Pin(32), freq=100000)
lcd = LCD(i2c)

def display_msg(line1="", line2=""):
    lcd.clear()
    
    if len(line1) > 16:
        line1 = line1[:16]
        
    if len(line2) > 16:
        line2 = line2[:16]
        
    lcd.puts(line1, 0, 0)
    lcd.puts(line2, 1, 0)