import gc, os
import time
import board, busio

try:
    from AtlasSensors import *
except:
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

DO_ADDRESS = 97
ORP_ADDRESS = 98
PH_ADDRESS = 99
EC_ADDRESS = 100


try:
    identify_devices()
    orp_sensor = generic_ezo(ORP_ADDRESS)
    res = orp_sensor.read()
    print("ORP reading:", res, "mV")
    ph_sensor = generic_ezo(PH_ADDRESS)
    res = ph_sensor.read()
    print("pH:", res)
    do_sensor = generic_ezo(DO_ADDRESS)
    res = do_sensor.read()
    print("Dissolved Oxygen: ", res, "mg/L")
    ec_sensor = generic_ezo(EC_ADDRESS)
    res = ec_sensor.read()
    print("EC: ", res)

finally:
    i2c.unlock()
