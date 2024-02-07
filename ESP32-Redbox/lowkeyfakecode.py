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

from AtlasSensors import *
from setpoint_and_address import *
from sys_info import sys_info
from offline_collection import main as offline_main

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

OFFLINE_MODE = True  # If offline mode is on, run offline.py
if OFFLINE_MODE:
    offline_main()
else:
    print("Connecting to %s" % secrets["ssid"])
    wifi.radio.hostname = sys_info["hostname"]
    print("Hostname:", wifi.radio.hostname)

    MAX_CONNECTION_ATTEMPTS = 10
    CONNECTION_INTERVAL = 10  # connection retry interval in seconds

    connection_attempts = 0

    while not wifi.radio.ipv4_address:
        try:
            connection_attempts += 1
            wifi.radio.connect(secrets["ssid"], secrets["password"])
        except Exception as e:
            print("Error connecting to wifi:", e)
            if connection_attempts == MAX_CONNECTION_ATTEMPTS:
                raise
            print("Trying again in %i seconds..." % CONNECTION_INTERVAL)
            time.sleep(CONNECTION_INTERVAL)

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


    url = "http://159.203.186.79:8086/api/v2/write?org=%s&bucket=%s&precision=%s" % (params["org"], params["bucket"], params["precision"])

    POLLING_PERIOD = 15  # Polling period in seconds

    while not i2c.try_lock():  # attempting to lock i2c to have exclusive control
        pass

    try:
        controller_id = sys_info["controller_id"]

        orp_sensor = generic_ezo(ORP_ADDRESS)
        ph_sensor = generic_ezo(PH_ADDRESS)
        do_sensor = generic_ezo(DO_ADDRESS)
        ec_sensor = generic_ezo(EC_ADDRESS)
        while True:
            startTime = time.time()
            res_orp = orp_sensor.read()
            print("ORP reading:", res_orp, "mV")

            res_ph = ph_sensor.read()
            print("pH:", res_ph)

            res_do = do_sensor.read()
            print("Dissolved Oxygen: ", res_do, "mg/L")

            res_ec = ec_sensor.read()
            print("EC: ", res_ec)

            data = "\n atlasSensors,sensor_id=%s orp=%f,ph=%f,do=%f,ec=%f %i" % (
                controller_id,
                res_orp,
                res_ph,
                res_do,
                res_ec,
                time.mktime(time.localtime()),
            )

            response = None
            while not response:
                try:
                    response = https.post(url, headers=headers, data=data)
                except RuntimeError as error:  # disconnect errors often show as RuntimeError
                    print("Error:", error)
                    if not wifi.radio.ipv4_address:
                        connection_attempts = 0
                        while not wifi.radio.ipv4_address:  # check if wifi is actually disconnected before attempting
                            # reconnect
                            try:
                                connection_attempts += 1
                                wifi.radio.connect(secrets["ssid"], secrets["password"])
                            except Exception as e:
                                print("Error connecting to wifi:", e)
                                if connection_attempts == MAX_CONNECTION_ATTEMPTS:
                                    raise
                                print("Trying again in %i seconds..." % CONNECTION_INTERVAL)
                                time.sleep(CONNECTION_INTERVAL)
                        print("Connected to %s!" % secrets["ssid"])
                except AssertionError as error:
                    print("Request failed:", error)
                    raise

            # time.sleep(15)
            now = time.time()
            waitTime = POLLING_PERIOD - (now - startTime)
            if waitTime > 0:  # waitTime will be negative if connection is lost
                time.sleep(waitTime)

    finally:
        i2c.unlock()
