import time
import board
import busio
import digitalio
import storage


import adafruit_scd30

from sys_info import sys_info

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

def main():
    POLLING_PERIOD = 5  # Polling period in seconds
    PULSE_PERIOD = 4  # How long the control signal is True for
    CO2_SETPOINT = 500  # in PPM
    CO2_DEADBAND = 50  # Difference from setpoint to turn off or on
    C02_ALARM = 2000  # 'Dangerous' ppms
    # Ex. Setpoint 700 DB 50, Systems turns on @ 650 and off @ 750
    co2_controller = DeadbandController(CO2_SETPOINT, CO2_DEADBAND, C02_ALARM)
    co2_port = digitalio.DigitalInOut(board.D3)  # Sets Digital Port 3 for CO2 control
    co2_port.direction = digitalio.Direction.OUTPUT  # Makes it an output port
    co2_alarm = digitalio.DigitalInOut(board.D4)  # Sets Digital Port 4 for CO2 alarm
    co2_alarm.direction = digitalio.Direction.OUTPUT  # Makes it an output port

    try:
        i2c = busio.I2C(board.SCL, board.SDA, frequency=50000)
        scd = adafruit_scd30.SCD30(i2c)
        controller_id = sys_info["controller_id"]

        while not scd.data_available:
            pass

        while True and int(scd.CO2) != 0:
            startTime = time.time()
            try:
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

                # Think about converting to .csv but consider cloud
                data = "\n sensirion,sensor_id=%s co2=%f,temp=%f,humidity=%f %i" % (
                    controller_id,
                    res_co2,
                    res_temp,
                    res_humidity,
                    time.mktime(time.localtime()),
                )
                print(data)
                try:
                    offline_data = "\n %i, %f, %f, %f" % (
                    time.mktime(time.localtime()),
                    res_co2,
                    res_temp,
                    res_humidity
                )
                    with open('/offline_collection.csv', 'a') as file:
                        file.write(offline_data)
                except Exception as e:
                    print("\n Error occurred: ", str(e))
                now = time.time()
                waitTime = POLLING_PERIOD - (now - startTime)
                if waitTime > 0:  # waitTime will be negative if connection is lost
                    time.sleep(waitTime)
            except:
                print("Performing Soft Reset...")
                scd.reset()
                time.sleep(5)
    finally:
        i2c.unlock()


if __name__ == '__main__':
    main()
