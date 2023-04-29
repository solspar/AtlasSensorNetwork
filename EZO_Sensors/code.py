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

try:
    from AtlasSensors import *
except:
    print("Error importing EZO sensor module\n")

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

ntp = adafruit_ntp.NTP(socket, tz_offset=0)
rtc.RTC().datetime = ntp.datetime

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
    # identify_devices()
    x = 0
    while x < 15:
        orp_sensor = generic_ezo(ORP_ADDRESS)
        res_orp = orp_sensor.read()
        print("ORP reading:", res_orp, "mV")

        ph_sensor = generic_ezo(PH_ADDRESS)
        res_ph = ph_sensor.read()
        print("pH:", res_ph)

        do_sensor = generic_ezo(DO_ADDRESS)
        res_do = do_sensor.read()
        print("Dissolved Oxygen: ", res_do, "mg/L")

        ec_sensor = generic_ezo(EC_ADDRESS)
        res_ec = ec_sensor.read()
        print("EC: ", res_ec)

        data = '\n atlasSensors,sensor_id=310B9 orp=%f,ph=%f,do=%f,ec=%f %i' % (res_orp, res_ph,
                                                                                res_do, res_ec,
                                                                                time.mktime(time.localtime()))

        url = "http://159.203.186.79:8086/api/v2/write?org=uf_cea&bucket=chamber3_devel&precision=s"

        response = None
        while not response:
            try:
                response = https.post(url, headers=headers, data=data)

            except AssertionError as error:
                print('Request failed')

        x += 1
        time.sleep(15)

finally:
    i2c.unlock()
