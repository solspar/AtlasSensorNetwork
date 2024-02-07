import board
import busio
import time

global i2c
i2c = busio.I2C(scl=board.SCL, sda=board.SDA, frequency=400000)

# while not i2c.try_lock():
#     pass
def change_address_name(current_address: int, new_address: int, name: str) -> None:
    """Change the current address of the device"""
    i2c.writeto(current_address, "Name,")
    time.sleep(0.3)
    i2c.writeto(current_address, "Name,%s" % name)
    time.sleep(0.3)
    i2c.writeto(current_address, "I2C,%i" % new_address)
    time.sleep(2)

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
        time.sleep(0.3)
        print("Device information:", result.decode("utf-8"))
        show_name(address)
        print("i2c address:", address)

def dispense(address: int, amount: int) -> None:
    i2c.writeto(address, "D,%f" % amount)

class generic_ezo:
    """Generic EZO class for reading from """

    def __init__(self, address: int, print_res: bool = False) -> None:
        self.address = address
        self.print_res = print_res

    def read_bytearray(self) -> bytearray:
        """Reads the ORP, outputs as a byte array"""
        i2c.writeto(self.address, "R")
        time.sleep(0.9)
        result = bytearray(7)
        i2c.readfrom_into(self.address, result)
        if self.print_res is True:
            print(result)
        return result

    def read(self) -> float:
        """Reads the ORP, decodes to float"""
        i2c.writeto(self.address, "R")
        time.sleep(0.9)
        result = bytearray(7)
        i2c.readfrom_into(self.address, result)
        if self.print_res is True:
            print(result)
        result1 = result[1:5]
        result1_decode = result1.decode("utf-8")
        result_float = float(result1_decode)
        return result_float

    def sleep(self) -> None:
        i2c.writeto(self.address, "Sleep")

    def status_bytearray(self) -> bytearray:
        i2c.writeto(self.address, "Status")
        time.sleep(0.3)
        result = bytearray(17)
        i2c.readfrom_into(self.address, result)
        if self.print_res is True:
            print(result)
        return result

