import gc
import os
import time
import board
import busio
import wifi
import socketpool
import ssl
import rtc
import adafruit_ntp
import adafruit_requests as requests
from params import headers, params
from sys_info import sys_info
from real_Atlas import *
from setpoint_and_addresses import *

# Constants for controlling program flow
POLLING_PERIOD = 15  # Data polling interval in seconds

# Prepare URL for data upload
url = "http://159.203.186.79:8086/api/v2/write?org=%s&bucket=%s&precision=%s" % (params["org"], params["bucket"], params["precision"])

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

# Import WiFi secrets
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

def connect_to_wifi():
    global https, socket
    print("Connecting to %s" % secrets["ssid"])
    wifi.radio.hostname = sys_info["hostname"]
    print("Hostname:", wifi.radio.hostname)

    if not wifi.radio.ipv4_address:
        try:
            wifi.radio.connect(secrets["ssid"], secrets["password"])
            print("Connected to %s!" % secrets["ssid"])
            socket = socketpool.SocketPool(wifi.radio)
            https = requests.Session(socket, ssl.create_default_context())
            try:
                ntp = adafruit_ntp.NTP(socket, server="time-e-g.nist.gov", tz_offset=0)
                rtc.RTC().datetime = ntp.datetime
            except TimeoutError:
                print("Error: Could not connect to ntp")
        except Exception as e:
            print("Error connecting to wifi:", e)

    return wifi.radio.ipv4_address is not None

def send_data(data):
    try:
        response = https.post(url, headers=headers, data=data)
        # You might want to check 'response' content here to ensure data was successfully posted
        print("Data successfuly sent!")
        time.sleep(5)
    except (RuntimeError, AssertionError) as error:
        print("Data sending failed:", error)

def main_loop():
    while True:
        while not i2c.try_lock():  # attempting to lock i2c to have exclusive control
            pass
        # Initialize sensors
        orp_sensor = generic_ezo(ORP_ADDRESS)
        ph_sensor = generic_ezo(PH_ADDRESS)
        do_sensor = generic_ezo(DO_ADDRESS)
        ec_sensor = generic_ezo(EC_ADDRESS)

        ec_flag = False
        orp_flag = False
        ph_flag = False
        do_flag = False

        # Data collection
        try:
            res_orp = orp_sensor.read()
            print("ORP reading:", res_orp, "mV")
        except Exception as e:
            print("\n Error occurred: ", str(e))
            res_orp = -1
            orp_flag = True

        try:
            res_ph = ph_sensor.read()
            print("pH:", res_ph)
        except Exception as e:
            print("\n Error occurred: ", str(e))
            res_ph = -1
            ph_flag = True

        try:
            res_do = do_sensor.read()
            print("Dissolved Oxygen: ", res_do, "mg/L")
        except Exception as e:
            print("\n Error occurred: ", str(e))
            res_do = -1
            do_flag = True

        try:
            res_ec = ec_sensor.read()
            print("EC: ", res_ec)
        except Exception as e:
            print("\n Error occurred: ", str(e))
            res_ec = -1
            ec_flag = True

        # You might want to store the timestamp of the data collection
        timestamp = time.mktime(time.localtime())
        data = "\n atlasSensors,sensor_id=%s orp=%f,ph=%f,do=%f,ec=%f %i" % (
            sys_info["controller_id"],
            res_orp,
            res_ph,
            res_do,
            res_ec,
            timestamp,
        )

        #Controlling Below:


        # Save data offline in case of connection issues
        try:
            offline_data = "\n %i, %f, %f, %f, %f" % (timestamp, res_orp, res_ph, res_do, res_ec)
            with open('/offline_collection.csv', 'a') as file:
                file.write(offline_data)
            print("Saved data offline successfully.")
        except Exception as e:
            print("\n Error occurred: ", str(e))

        # Attempt to connect and send data
        if connect_to_wifi():
            send_data(data)
        else:
            print("Unable to connect to the internet, data saved locally.")

        # Wait for the next data collection
        i2c.unlock()
        time.sleep(POLLING_PERIOD)

# Start the main loop
main_loop()
