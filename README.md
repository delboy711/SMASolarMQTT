```
   _____ __  __           _____       _            __  __  ____ _______ _______ 
  / ____|  \/  |   /\    / ____|     | |          |  \/  |/ __ |__   __|__   __|
 | (___ | \  / |  /  \  | (___   ___ | | __ _ _ __| \  / | |  | | | |     | |   
  \___ \| |\/| | / /\ \  \___ \ / _ \| |/ _` | '__| |\/| | |  | | | |     | |   
  ____) | |  | |/ ____ \ ____) | (_) | | (_| | |  | |  | | |__| | | |     | |   
 |_____/|_|  |_/_/    \_|_____/ \___/|_|\__,_|_|  |_|  |_|\___\_\ |_|     |_|   
```
 

# SMASolarMQTT
==================================================================

Forked from [stuartpittaway/SMASolarMQTT](https://github.com/stuartpittaway/SMASolarMQTT) by Derek Jennings
Hacked about to :-
* Operate with SMA Sunny Boy 3600TL Inverter
* Remove debug messages cluttering log files
* Add systemd unit

===================================================================

Report generation statistics from SMA photovoltaic inverter over a shared MQTT hub.  

Designed for use with emonCMS and emonPi see http://openenergymonitor.org/emon/

Copyright 2013-2015 Stuart Pittaway

GNU GENERAL PUBLIC LICENSE -  Version 2, June 1991



# Installation

Install on Raspberry PI image (low write) emonCMS from https://github.com/emoncms/emoncms/blob/master/readme.md
Python files should be put in the folder /home/pi/SMASolarMQTT
Edit SMASolarMQTT.service and replace the Bluetooth address in line 7 with your own.
Systemd unit SMASolarMQTT.service should be placed in folder /etc/systemd/system  enable auto start at boot with the command

`sudo systemctl enable SMASolarMQTT` and start it with

`sudo systemctl start SMASolarMQTT`

Fire up a command prompt and install the bluetooth stack

`sudo aptitude install bluez python-bluetooth`

Plug in a CLASS 1 BLUETOOTH USB adapter to the PI.

Run command

`lsusb`

should be shown similar to this...

`Bus 001 Device 004: ID 0a12:0001 Cambridge Silicon Radio, Ltd Bluetooth Dongle (HCI mode)`

Start the bluetooth service
```
sudo service bluetooth start
sudo service bluetooth status
```

Run command `hcitool scan`

Should find your SMA inverter...
```
Scanning ...
        00:80:25:1D:AC:53       SMA001d SN: 2120051742 SN2120051742
```		
	
# Configuring emonCMS to detect nodes

emonCMS should automatically detect and show the solar values inside the "Nodes" page, however they will be missing descriptions.

Click on EmonHub and cut and paste the below into the configuration editor, then click SAVE.

<pre>
[[50]]
    nodename = SMASolarMQTT_AC
    firmware =not_applicable
    hardware = not_applicable
    [[[rx]]]
       names = ACOutputPhase1,ACOutputPhase2,ACOutputPhase3,ACLineVoltagePhase1,ACLineVoltagePhase2,ACLineVoltagePhase3,ACLineCurrentPhase1,ACLineCurrentPhase2,ACLineCurrentPhase3,ACGridFrequency
       datacode = h
       scales = 1,1,1,1,1,1,1,1,1,1
       units =W,W,W,V,V,V,A,A,A,Hz

[[51]]
    nodename = SMASolarMQTT_DCWatts
    firmware = not_applicable
    hardware = not_applicable
    [[[rx]]]
       names = SolarDCWatts
       datacode = h
       scales = 1
       units =W

[[52]]
    nodename = SMASolarMQTT_Yield
    firmware = not_applicable
    hardware = not_applicable
    [[[rx]]]
       names = TotalYield, DayYield, OperatingTime, FeedInTime
       datacode = h
       scales = 1,1,1,1
       units =kWh,kWh,hours,hours

[[53]]
    nodename = SMASolarMQTT_DC
    firmware = not_applicable
    hardware = not_applicable
    [[[rx]]]
       names = DCVoltage, DCCurrent
       datacode = h
       scales = 1,1
       units =V,A
</pre>
