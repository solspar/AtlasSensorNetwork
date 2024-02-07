import gc, os
import time
import board, busio
import wifi
import socketpool
import ssl
import rtc
import adafruit_ntp
import adafruit_requests as requests
import digitalio
# from setpoints_ports import *
from params import headers, params
from sys_info import sys_info
from offline_collection import main as offline_main

import adafruit_scd30

class DeadbandController:
    def __init__(self, setpoint, deadband, alarm):
        self.setpoint = setpoint
        self.deadband = deadband
        self.alarm = alarm

    def update(self, process_variable):
        error = process_variable - self.setpoint
        # Negative value means we're below the setpoint
        # Positive value means we're above the setpoint
        if abs(error) <= self.deadband:
            control_output = False  # Within the deadband, no control action
        else:
            if error > 0:
                # If error is positive then we remain off and wait to drop
                control_output = False
            else:
                # Error is negative and we're below setpoint so turn ON
                control_output = True

        return control_output

    def alarmCheck(self, process_variable):
        if process_variable >= self.alarm:
            alarm_output = True
        else:
            alarm_output = False

        return alarm_output

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
    PULSE_PERIOD = 15  # How long the control signal is True for
    CO2_SETPOINT = 500  # in PPM
    CO2_DEADBAND = 50  # Difference from setpoint to turn off or on
    C02_ALARM = 2000  # 'Dangerous' ppms
    # Ex. Setpoint 700 DB 50, Systems turns on @ 650 and off @ 750
    co2_controller = DeadbandController(CO2_SETPOINT, CO2_DEADBAND, C02_ALARM)
    co2_port = digitalio.DigitalInOut(board.D3)  # Sets Digital Port 3 for CO2 control
    co2_port.direction = digitalio.Direction.OUTPUT  # Makes it an output port
    co2_alarm = digitalio.DigitalInOut(board.D4)  # Sets Digital Port 4 for CO2 alarm
    co2_alarm.direction = digitalio.Direction.OUTPUT  # Makes it an output port

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

    try:
        i2c = busio.I2C(board.SCL, board.SDA, frequency=50000)
        scd = adafruit_scd30.SCD30(i2c)
        controller_id = sys_info["controller_id"]

        while not scd.data_available:
            pass

        while True and int(scd.CO2) != 0:
            startTime = time.time()
            res_co2 = scd.CO2
            print("CO2 reading: ", res_co2, "PPM")

            co2_port.value = co2_controller.update(res_co2)  # Updates control port
            if co2_port.value:
                time.sleep(PULSE_PERIOD)
                co2_port.value = False

            co2_alarm.value = co2_controller.alarmCheck(res_co2)  # Updates alarm port
            if co2_alarm.value:
                print("Alarm Active!")
            else:
                print("Alarm Inactive")

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
                except RuntimeError as error:  # disconnect errors often show as RuntimeError
                    print("Error:", error)
                    if not wifi.radio.ipv4_address:
                        connection_attempts = 0
                        while not wifi.radio.ipv4_address:  # check if wifi is actually disconnected before attempting reconnect
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
        # i2c.unlock()
        print("i2c unlock")
