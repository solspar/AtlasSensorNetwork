import gc, os
import time
import board, busio
import wifi
import socketpool
import ssl
import rtc
import adafruit_ntp
import adafruit_requests as requests
from params import headers, params

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

try:
    print("Connecting to %s" % secrets["ssid"])
    wifi.radio.connect(secrets["ssid"], secrets["password"])
except:
    print("Error connecting to wifi")
    raise

print("Connected to %s!" % secrets["ssid"])

socket = socketpool.SocketPool(wifi.radio)
https = requests.Session(socket, ssl.create_default_context())
try:
    ntp = adafruit_ntp.NTP(socket, server="time-e-g.nist.gov", tz_offset=0)
    rtc.RTC().datetime = ntp.datetime
except TimeoutError:
    print("Error: Could not connect to ntp")
    raise


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

i2c = busio.I2C(
    scl=board.SCL, sda=board.SDA, frequency=400000
)  # Use board.SCL and board.SDA

while not i2c.try_lock():
    pass

i2c.scan()

# Write to and read from EZO-PMP devices
try:
    x = 0
    while(x < 15):
        i2c.writeto(101, "D,1")
        i2c.writeto(102, "D,2")
        result1 = bytearray(10)
        result2 = bytearray(10)
        time.sleep(0.3)
        i2c.readfrom_into(101, result1)
        i2c.readfrom_into(102, result2)
        time.sleep(0.3)
        print(result1)
        print(result2)
        i2c.writeto(101, "D,?")
        i2c.writeto(102, "D,?")
        time.sleep(0.3)
        i2c.readfrom_into(101, result1)
        i2c.readfrom_into(102, result2)
        time.sleep(0.3)
        print(result1)
        print(result2)

        output1 = result1[4:8]
        output2 = result2[4:8]
        result_decode1 = output1.decode("utf-8") # decode output to make it a float
        result_decode2 = output2.decode("utf-8")
        result_f1 = float(result_decode1)
        result_f2 = float(result_decode2)
        print(result_f1)
        print(result_f2)
        data1 = '\n pumps,sensor_id=EZOPMP3101 dispensed=%f %i' % (result_f1, time.mktime(time.localtime()))
        data2 = '\n pumps,sensor_id=EZOPMP3102 dispensed=%f %i' % (result_f2, time.mktime(time.localtime())) 
        print(data1)
        print(data2)

        url = "http://159.203.186.79:8086/api/v2/write?org=uf_cea&bucket=chamber3_devel&precision=s"

        response = None
        while not response:
            try:
                response = https.post(url, headers=headers, data=data1)
                response2 = https.post(url, headers=headers, data=data2)
            except AssertionError as error:
                print('Request failed')

        x += 1
        time.sleep(30)
        

finally:
    i2c.unlock()
