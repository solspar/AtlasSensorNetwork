import gc, os
import time
import board, busio
import wifi
import socketpool
import ssl
import rtc
import adafruit_ntp
import adafruit_requests as requests
from setpoints_ports import *
from params import headers, params
from sys_info import sys_info
import adafruit_scd30

# Import WiFi secrets
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Constants for controlling program flow
POLLING_PERIOD = 15  # Data polling interval in seconds

# Set up hardware components
i2c = busio.I2C(board.SCL, board.SDA, frequency=50000)
scd = adafruit_scd30.SCD30(i2c)

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
        while not scd.data_available:
            time.sleep(0.1)  # delay for a short period before checking again

        # Data collection
        res_co2 = scd.CO2
        res_temp = scd.temperature
        res_humidity = scd.relative_humidity

        print("CO2 reading: ", res_co2, "PPM")
        print("Temperature: ", res_temp, "degrees C")
        print("Relative Humidity: ", res_humidity, "%")
        co2_port.value = co2_controller.update(res_co2)  # Updates control port
        if co2_port.value:
            time.sleep(PULSE_PERIOD)
            co2_port.value = False

        co2_alarm.value = co2_controller.alarmCheck(res_co2)  # Updates alarm port

        if co2_alarm.value:
            print("Alarm Active!")
        else:
            print("Alarm Inactive")

        # You might want to store the timestamp of the data collection
        timestamp = time.mktime(time.localtime())
        data = "\n sensirion,sensor_id=%s co2=%f,temp=%f,humidity=%f %i" % (
            sys_info["controller_id"],
            res_co2,
            res_temp,
            res_humidity,
            timestamp,
        )

        # Save data offline in case of connection issues
        try:
            offline_data = "\n %i, %f, %f, %f" % (timestamp, res_co2, res_temp, res_humidity)
            with open('/offline_collection.csv', 'a') as file:
                file.write(offline_data)
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
