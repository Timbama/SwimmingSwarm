# Flashing ESCs
## Install BLHeliSuite 16.7.14
Download the software located [here][1].

## Set Up Arduino
Flashing the ESCs requires some method of connecting the ESC to the computer. The easiest method we have found is to use
an Arduino Uno or Nano to convert the usb connection to the 1-wire signal that goes to the ESC. BLHeliSuite automatically
supports this as shown in [this guide][2]. Simply go to the `Make Interfaces` tab, select the board you have,
and click the `Make Arduino 1-Wire Interface` button.

*TODO: add info on multi-esc flashing*


## Connecting to the ESC
1. Connect the ground and signal wires of the ESC. The ground wire from the ESC needs to be conected to the ground pin on the Arduino.
Which pin to connect the signal wire to depends on what firmware was flashed to the Arduino
   * Multi-ESC Flashing: connect signal wires to digital signal pins 8-12. If only flashing one ESC any of those 4 pins will work
   * Single ESC Flashing: connect signal wire to digial pin 0.
2. Power the ESC from any source.
3. Go back to the Atmel ESC Setup tab
4. Select the correct COM port from the drop down in the bottom left
5. Press the `Connect` button
6. Press the `Read Setup` button

## Flash New ESC With the BLHeli Firmware
1. Connect to the ESC
2. *TODO: The rest of this section*

## Flash New Values to the ESC
1. Connect to the ESC
2. The recommended settings for the ESCs used in the robot are shown in this image:
![ESC Values][3]
3. Press the `Write Setup` button

[1]: https://github.com/4712/BLHeliSuite/releases/tag/16714901
[2]: https://oscarliang.com/esc-1-wire-bootloader-signal-cable-blheli-simonk/
[3]: ../Images/ESCFirmware.PNG
