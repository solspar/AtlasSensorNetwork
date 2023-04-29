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

i2c = busio.I2C(scl=board.IO5, sda=board.IO6, frequency=400000)

# Grab i2c bus
while not i2c.try_lock():
    pass

ORP_ADDRESS = 98


def show_name(address: int) -> None:
    """Show the name of the i2c device with the specified address"""
    i2c.writeto(address, "Name,?")
    result = bytearray(24)
    time.sleep(0.3)
    i2c.readfrom_into(address, result)
    print("name:", result.decode("utf-8"))


def identify_devices() -> None:
    """Display all devices in the system"""
    for address in i2c.scan():
        i2c.writeto(address, "i")
        result = bytearray(13)
        time.sleep(0.3)
        i2c.readfrom_into(address, result)
        # time.sleep(0.3)
        print("Device information:", result.decode("utf-8"))
        show_name(address)
        print("i2c address:", address)


class ph:
    def __init__(self, address: int, print_res: bool = False) -> None:
        self.address = address
        self.print_res = print_res

    def read_bytearray(self) -> bytearray:
        """Reads the PH, outputs as a byte array"""
        i2c.writeto(self.address, "R")
        time.sleep(0.9)
        result = bytearray(7)
        i2c.readfrom_into(ORP_ADDRESS, result)
        if self.print_res is True:
            print(result)
        return result

    def read(self) -> float:
        i2c.writeto(self.address, "R")
        time.sleep(0.9)
        result = bytearray(7)
        i2c.readfrom_into(ORP_ADDRESS, result)
        if self.print_res is True:
            print(result)
        result1 = result[1:5]
        result1_decode = result1.decode("utf-8")
        result_float = float(result1_decode)
        return result_float


class orp:
    def __init__(self, address: int, print_res: bool = False) -> None:
        self.address = address
        self.print_res = print_res

    def read_bytearray(self) -> bytearray:
        """Reads the ORP, outputs as a byte array"""
        i2c.writeto(self.address, "R")
        time.sleep(0.9)
        result = bytearray(7)
        i2c.readfrom_into(ORP_ADDRESS, result)
        if self.print_res is True:
            print(result)
        return result

    def read(self) -> float:
        """Reads the ORP, decodes to float"""
        i2c.writeto(self.address, "R")
        time.sleep(0.9)
        result = bytearray(7)
        i2c.readfrom_into(ORP_ADDRESS, result)
        if self.print_res is True:
            print(result)
        result1 = result[1:5]
        result1_decode = result1.decode("utf-8")
        result_float = float(result1_decode)
        return result_float


class generic_ezo:
    def __init__(self, address: int, print_res: bool = False) -> None:
        self.address = address
        self.print_res = print_res

    def read_bytearray(self) -> bytearray:
        """Reads the ORP, outputs as a byte array"""
        i2c.writeto(self.address, "R")
        time.sleep(0.9)
        result = bytearray(7)
        i2c.readfrom_into(ORP_ADDRESS, result)
        if self.print_res is True:
            print(result)
        return result

    def read(self) -> float:
        """Reads the ORP, decodes to float"""
        i2c.writeto(self.address, "R")
        time.sleep(0.9)
        result = bytearray(7)
        i2c.readfrom_into(ORP_ADDRESS, result)
        if self.print_res is True:
            print(result)
        result1 = result[1:5]
        result1_decode = result1.decode("utf-8")
        result_float = float(result1_decode)
        return result_float


ORP_ADDRESS = 98

try:
    # identify_devices()
    orp_sensor = orp(98)
    res = orp_sensor.read()
    print(res)

finally:
    i2c.unlock()
