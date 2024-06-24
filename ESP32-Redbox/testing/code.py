import gc
import os
import time
import board
import busio
import wifi
import ssl
import rtc
import adafruit_connection_manager as acm
import adafruit_ntp
import adafruit_requests as requests
from params import headers, params
from sys_info import sys_info
from real_Atlas import *
from setpoint_and_addresses import *

# Constants for controlling program flow
POLLING_PERIOD = 10  # Data polling interval in seconds

# Prepare URL for data upload
url = "http://159.203.186.79:8086/api/v2/write?org=%s&bucket=%s&precision=%s" % (params["org"], params["bucket"], params["precision"])

# Show available memory
def show_memory_info():
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

show_memory_info()

# Import WiFi secrets
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

def connect_to_wifi():
    global https, pool
    print("Connecting to %s" % secrets["ssid"])
    
    radio = wifi.radio
    while not radio.connected:
        try:
            radio.connect(secrets["ssid"], secrets["password"])
            print("Connected to %s!" % secrets["ssid"])
        except Exception as e:
            print("Could not connect to Wi-fi: ", e)
            time.sleep(5)  # Retry after delay

    pool = acm.get_radio_socketpool(radio)
    ssl_context = acm.get_radio_ssl_context(radio)

    try:
        https
    except:
        https = requests.Session(pool, ssl_context)

    return radio.ipv4_address is not None

def ntp_sync():
    global last_sync_time
    try:
        ntp = adafruit_ntp.NTP(pool, server="ns1.name.ufl.edu", tz_offset=0)
        rtc.RTC().datetime = ntp.datetime
        last_sync_time = time.time()
        print("NTP time synchronized")
    except Exception as e:
        print("Error: Could not connect to NTP.", str(e))
        time.sleep(2)

def send_data(data):
    try:
        response = https.post(url, headers=headers, data=data)
        print("Data successfully sent!")
    except (RuntimeError, AssertionError) as error:
        print("Data sending failed:", error)

def initialize_sensor(sensor_class, address):
    try:
        sensor = sensor_class(address)
        print(f"Initialized sensor at address {address}")
        return sensor
    except Exception as e:
        print(f"Sensor initialization failed at address {address}: {e}")
        return None

def read_sensor(sensor, sensor_name):
    try:
        value = sensor.read()
        print(f"{sensor_name} reading:", value)
        return value
    except Exception as e:
        print(f"Error reading {sensor_name}: {e}")
        return -1

last_sync_time = 0

def main_loop():
    while True:
        gc.collect()  # Collect garbage at the start of each loop
        try:
            if not connect_to_wifi():
                print("Could not connect to Wi-Fi. Trying again next loop.")
                time.sleep(POLLING_PERIOD)
                continue

            if time.time() - last_sync_time >= 3600:
                ntp_sync()

            i2c.try_lock()

            orp_sensor = initialize_sensor(generic_ezo, ORP_ADDRESS)
            ph_sensor = initialize_sensor(generic_ezo, PH_ADDRESS)
            do_sensor = initialize_sensor(generic_ezo, DO_ADDRESS)
            ec_sensor = initialize_sensor(generic_ezo, EC_ADDRESS)
            temp_sensor = initialize_sensor(generic_ezo, TEMP_ADDRESS)

            data = {
                "orp": read_sensor(orp_sensor, "ORP") if orp_sensor else -1,
                "ph": read_sensor(ph_sensor, "pH") if ph_sensor else -1,
                "do": read_sensor(do_sensor, "Dissolved Oxygen") if do_sensor else -1,
                "ec": read_sensor(ec_sensor, "EC") if ec_sensor else -1,
                "temp": read_sensor(temp_sensor, "Solution temperature") if temp_sensor else -1,
            }

            timestamp = time.mktime(time.localtime())
            data_str = "\n atlasSensors,sensor_id=%s orp=%f,ph=%f,do=%f,ec=%f,temp=%f %i" % (
                sys_info["controller_id"],
                data['orp'],
                data['ph'],
                data['do'],
                data['ec'],
                data['temp'],
                timestamp,
            )
            print(data_str)

            offline_data = "\n %i, %f, %f, %f, %f, %f" % (timestamp, data['orp'], data['ph'], data['do'], data['ec'], data['temp'])
            try:
                with open('/offline_collection.csv', 'a') as file:
                    file.write(offline_data)
                print("Saved data offline successfully.")
            except Exception as e:
                print("\n Error occurred while saving offline: ", str(e))

            if connect_to_wifi():
                send_data(data_str)
            else:
                print("Unable to connect to the internet, data saved locally.")

        except Exception as e:
            print("An error occurred in the main loop:", e)
        finally:
            if i2c.locked():
                i2c.unlock()
            time.sleep(POLLING_PERIOD)

# Start the main loop
main_loop()
