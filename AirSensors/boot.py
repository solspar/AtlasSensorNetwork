import digitalio
import board
import storage

switch = digitalio.DigitalInOut(board.D5)
switch.direction = digitalio.Direction.INPUT
switch.pull = digitalio.Pull.UP

# If the D5 is connected to ground with a wire
# you can edit files over the USB drive again.
storage.remount("/", switch.value)
#test
