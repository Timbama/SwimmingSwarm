# Overview

The following image depicts the general structure of the electronics including LimeSDR radio support (not currently in use).
![Made in Orcad Capture][1]

Raspberry Pi Zero W overview and pinout.
![Raspberry Pi Pinout][2]

# Plate Layout

Full Stack | ESC Plate
:------|-------:
![][4] | ![][5]

Top of Control Plate | Bottom of Control Plate
:------|-------:
![][6] | ![][7]

Top of Battery Management Plate | BMS Obverse
:------|-------:
![][8] | ![][9]


![Made in Microsoft Paint][3]

# Connectors
## MT30 Connectors
* Male in hull to Female on ESCs
* Male on motors to Female on outer hull

## XT60 Connectors
* Male on PDB to Female on battery board (BMS)

## Bullet Connectors
* Power Distribution Board Output to ESC Power Input

## Dupont Connectors
* ESC Signal Wires to Pixhawk
* Power Distribution Board 5V Output to Raspberry Pi GPIO Pins


[1]: ../Images/Final%20Electrical%20Schematic.png?raw=true
[2]: https://www.etechnophiles.com/ezoimgfmt/i2.wp.com/www.etechnophiles.com/wp-content/uploads/2020/12/R-Pi-Zero-Pinout.jpg
[3]: ../Images/Masterpiece2.png?raw=true
[4]: ../Images/full_stack_powered.jpg
[5]: ../Images/ESC_layer_top.jpg
[6]: ../Images/control_layer_top.jpg
[7]: ../Images/control_layer_bottom.jpg
[8]: ../Images/BMS_bottom.jpg
[9]: ../Images/BMS_top.jpg