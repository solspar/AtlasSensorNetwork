from machine import I2C
import time

i2c = I2C(freq=400000)

i2c.scan()

while True:
    i2c.writeto(103, "R")
    time.sleep(100)
    i2c.readfrom(103, 31)
    time.sleep(100)