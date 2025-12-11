from machine import Pin, PWM
import time

buzzer = PWM(Pin(14))
buzzer.duty(0)

def tone(freq, duration):
    buzzer.freq(freq)
    buzzer.duty(512)
    time.sleep(duration)
    buzzer.duty(0)
    time.sleep(0.05)

def beep_success():
    tone(2000, 0.08)
    tone(2000, 0.08)

def beep_fail():
    tone(2000, 0.25)
    tone(2000, 0.25)
    tone(2000, 0.25)