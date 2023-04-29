import gc, os
import time
import board, busio

try:
    from AtlasSensors import *
finally:
    print("Error importing EZO sensor module\n")

# Show available memory
print("Memory Info - gc.mem_free()")
print("---------------------------")
print("{} Bytes\n".format(gc.mem_free()))

flash = os.statvfs("/")
flash_size = flash[0] * flash[2]
flash_free = flash[0] * flash[3]
# Show flash size
print("Flash - os.statvfs('/')")
print("---------------------------")
print("Size: {} Bytes\nFree: {} Bytes\n".format(flash_size, flash_free))

# i2c = busio.I2C(scl=board.IO5, sda=board.IO6, frequency=400000)

# Grab i2c bus

ORP_ADDRESS = 98

try:
    # identify_devices()
    orp_sensor = generic_ezo(ORP_ADDRESS)
    res = orp_sensor.read()
    print(res)

finally:
    i2c.unlock()
