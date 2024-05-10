import time
import board, busio

from AtlasSensors import *


def main():
    POLLING_PERIOD = 15  # Polling period in seconds

    DO_ADDRESS = 97
    ORP_ADDRESS = 98
    PH_ADDRESS = 99
    EC_ADDRESS = 100
    TEMP_ADDRESS = 102
    while not i2c.try_lock():  # attempting to lock i2c to have exclusive control
        pass

    try:
        # controller_id = "310B9"  # green
        # controller_id = "310BA"  # orange
        # controller_id = "310BB"  # blue
        controller_id = "310BC"  # yellow
        orp_sensor = generic_ezo(ORP_ADDRESS)
        ph_sensor = generic_ezo(PH_ADDRESS)
        do_sensor = generic_ezo(DO_ADDRESS)
        ec_sensor = generic_ezo(EC_ADDRESS)
        temp_sensor = generic_ezo(TEMP_ADDRESS)

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

           # data = "\n atlasSensors,sensor_id=%s orp=%f,ph=%f,do=%f,ec=%f %i" % (
               #controller_id,
               # res_orp,
               # res_ph,
               # res_do,
               # res_ec,
               # time.mktime(time.localtime()),
           # )

            #print(data)


            now = time.time()
            waitTime = POLLING_PERIOD - (now - startTime)
            if waitTime > 0:  # waitTime will be negative if connection is lost
                time.sleep(waitTime)
    finally:
        i2c.unlock()


if __name__ == "__main__":
    main()
