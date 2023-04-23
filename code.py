import gc, os
import time
import board, busio


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

"""
i2c = busio.I2C(
    scl=board.SCL, sda=board.SDA, frequency=400000
)  # Use board.SCL and board.SDA
"""
i2c = busio.I2C(
    scl=board.SCL, sda=board.SDA, frequency=400000
)  # Use board.SCL and board.SDA

while not i2c.try_lock():
    pass

i2c.scan()

try:
    while True:
        i2c.writeto(101, "i")
        result = bytearray(3)
        i2c.readfrom_into(101, result)
        print(result)
        i2c.writeto(101, "R")
        result = bytearray(3)
        i2c.readfrom_into(101, result)
        result_int = int.from_bytes(result, "big")
        print(result_int)
        time.sleep(1)

finally:
    i2c.unlock()
