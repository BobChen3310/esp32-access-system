from machine import Pin
from .lcd import display_msg
from .buzzer import beep_success, beep_fail
import time

LED_R = Pin(16, Pin.OUT); LED_R.value(0)
LED_G = Pin(13, Pin.OUT); LED_G.value(0)
solenoid = Pin(17, Pin.OUT); solenoid.value(0)

def show_standby():
    display_msg("System Ready", "Swipe Your Card")

def grant_access(student_id):
    display_msg("Access Granted", student_id)
    beep_success()
    LED_G.value(1)
    solenoid.value(1)
    time.sleep(3)
    LED_G.value(0)
    solenoid.value(0)
    time.sleep(0.02)
    show_standby()

def deny_access():
    display_msg("Access Denied", "")
    beep_fail()
    LED_R.value(1)
    time.sleep(2)
    LED_R.value(0)
    show_standby()