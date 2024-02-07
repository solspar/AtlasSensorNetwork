import time
import board
import busio
import digitalio
import storage

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

PULSE_PERIOD = 4  # How long the control signal is True for
CO2_SETPOINT = 500  # in PPM
CO2_DEADBAND = 50  # Difference from setpoint to turn off or on
C02_ALARM = 2000  # 'Dangerous' ppms
# Ex. Setpoint 700 DB 50, Systems turns on @ 650 and off @ 750
co2_controller = DeadbandController(CO2_SETPOINT, CO2_DEADBAND, C02_ALARM)
co2_port = digitalio.DigitalInOut(board.D3)  # Sets Digital Port 3 for CO2 control
co2_alarm = digitalio.DigitalInOut(board.D4)  # Sets Digital Port 4 for CO2 alarm
co2_port.direction = digitalio.Direction.OUTPUT  # Makes it an output port
co2_alarm.direction = digitalio.Direction.OUTPUT  # Makes it an output port
