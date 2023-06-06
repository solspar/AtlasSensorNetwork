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

import adafruit_scd30

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

print("Connecting to %s" % secrets["ssid"])
# wifi.radio.hostname = "epistemology" # green
wifi.radio.hostname = "agency" # orange
# wifi.radio.hostname = "coordination" # blue
# wifi.radio.hostname = "curiosity" # yellow
print("Hostname:", wifi.radio.hostname)
connection_attempts = 0

while not wifi.radio.ipv4_address:
    try:
        connection_attempts += 1
        wifi.radio.connect(secrets["ssid"], secrets["password"])
    except Exception as e:
        print("Error connecting to wifi:", e)
        if connection_attempts == 10:
            raise
        print("Trying again in 10 seconds...")
        time.sleep(10)

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

url = "http://159.203.186.79:8086/api/v2/write?org=uf_cea&bucket=chamber3_devel&precision=s"

POLLING_PERIOD = 15  # Polling period in seconds

try:
    i2c = busio.I2C(board.SCL, board.SDA, frequency=50000)
    scd = adafruit_scd30.SCD30(i2c)
    # controller_id = "310B9"  # green
    controller_id = "310BA"  # orange
    # controller_id = "310BB"  # blue
    # controller_id = "310BC"  # yellow
    while not scd.data_available:
        pass

    while True and int(scd.CO2) != 0:
        startTime = time.time()
        res_co2 = scd.CO2
        print("CO2 reading: ", res_co2, "PPM")

        res_temp = scd.temperature
        print("Temperature: ", res_temp, "degrees C")

        res_humidity = scd.relative_humidity
        print("Relative Humidity: ", res_humidity, "%")

        data = "\n sensirion,sensor_id=%s co2=%f,temp=%f,humidity=%f %i" % (
            controller_id,
            res_co2,
            res_temp,
            res_humidity,
            time.mktime(time.localtime()),
        )

        response = None
        while not response:
            try:
                response = https.post(url, headers=headers, data=data)
            except RuntimeError as error:
                print("Error:", error)
                if not wifi.radio.ipv4_address:
                    connection_attempts = 0
                    while wifi.radio.ipv4_address is None:
                        try:
                            connection_attempts += 1
                            wifi.radio.connect(secrets["ssid"], secrets["password"])
                        except Exception as e:
                            print("Error connecting to wifi:", e)
                            if connection_attempts == 10:
                                raise
                            print("Trying again in 10 seconds...")
                            time.sleep(10)
                    print("Connected to %s!" % secrets["ssid"])
            except AssertionError as error:
                print("Request failed")
                raise

        # time.sleep(15)
        now = time.time()
        waitTime = POLLING_PERIOD - (now - startTime)
        if waitTime > 0:
            time.sleep(waitTime)

finally:
    # i2c.unlock()
    print("i2c unlock")
