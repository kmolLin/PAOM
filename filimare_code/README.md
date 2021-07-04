## The filmare code

## Requirements:

- arduino 1.8.15
- arduino mega 2560
- reprap ramps1.4 or higher

![](/filimare_code/images/ramps1_6.jpg)

## Modified part of the configuration file

- Gcode: M998 (Control the servo run Zoom in or out)
- XYZ endstop: use pull up version (clicked will stop)
- XYZ platform size: 100 * 100 * 100
- cancel heatbed and Nozzle
- adjust the E axis to rotate axis
- Not use autoplate function in marlin
- adjust stepper and adjust motion speed

## Reference

1. [Arduino](https://www.arduino.cc/)
2. [reprap ramps1.4 wiki](https://reprap.org/wiki/RepRap)
3. [Marlin Firmware source code](https://reprap.org/wiki/RepRap)
4. [Stepper Motor driver DM420](https://www.exp-tech.de/media/pdf/ACT/DM420.pdf)
