#!/usr/bin/python

# Run this script like this...
# This will background the task 
# nohup python SMASolarMQTT.py 00:80:25:1D:AC:53 0000 1> spotvalues.csv 2> btscanerrors.log &

__author__ = 'Stuart Pittaway'

import time
from datetime import datetime
import argparse
import sys
import traceback
import paho.mqtt.client as mqtt
import bluetooth

from SMANET2PlusPacket import SMANET2PlusPacket
from SMABluetoothPacket import SMABluetoothPacket
import SMASolarMQTT_library


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    # print(msg.topic+" "+str(msg.payload))
    # do nothing
    pass


def main(bd_addr, InverterPassword):
    InverterCodeArray = bytearray([0x5c, 0xaf, 0xf0, 0x1d, 0x50, 0x00]);

    # Dummy arrays
    AddressFFFFFFFF = bytearray([0xff, 0xff, 0xff, 0xff, 0xff, 0xff]);
    Address00000000 = bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00]);
    InverterPasswordArray = SMASolarMQTT_library.encodeInverterPassword(InverterPassword)
    port = 1

    packet_send_counter = 0

    while True:
        try:
            # print "Connecting to SMA Inverter over Bluetooth"
            btSocket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            btSocket.connect((bd_addr, port))
            # Give BT 10 seconds to timeout so we dont hang and wait forever
            btSocket.settimeout(10)

            # http://pybluez.googlecode.com/svn/www/docs-0.7/public/bluetooth.BluetoothSocket-class.html
            mylocalBTAddress = SMASolarMQTT_library.BTAddressToByteArray(btSocket.getsockname()[0], ":")
            mylocalBTAddress.reverse()
            # LogMessageWithByteArray("mylocalBTAddress", mylocalBTAddress)

            SMASolarMQTT_library.initaliseSMAConnection(btSocket, mylocalBTAddress, AddressFFFFFFFF, InverterCodeArray,
                                                        packet_send_counter)

            # Logon to inverter
            pluspacket1 = SMASolarMQTT_library.SMANET2PlusPacket(0x0e, 0xa0, packet_send_counter, InverterCodeArray,
                                                                 0x00,
                                                                 0x01, 0x01)
            pluspacket1.pushRawByteArray(
                bytearray([0x80, 0x0C, 0x04, 0xFD, 0xFF, 0x07, 0x00, 0x00, 0x00, 0x84, 0x03, 0x00, 0x00]))
            pluspacket1.pushRawByteArray(
                SMASolarMQTT_library.floattobytearray(SMASolarMQTT_library.time.mktime(datetime.today().timetuple())))
            pluspacket1.pushRawByteArray(bytearray([0x00, 0x00, 0x00, 0x00]))
            pluspacket1.pushRawByteArray(InverterPasswordArray)

            send = SMASolarMQTT_library.SMABluetoothPacket(1, 1, 0x00, 0x01, 0x00, mylocalBTAddress, AddressFFFFFFFF)
            send.pushRawByteArray(pluspacket1.getBytesForSending())
            send.finish()
            send.sendPacket(btSocket)

            bluetoothbuffer = SMASolarMQTT_library.read_SMA_BT_Packet(btSocket, packet_send_counter, True,
                                                                      mylocalBTAddress)

            SMASolarMQTT_library.checkPacketReply(bluetoothbuffer, 0x0001)

            packet_send_counter = packet_send_counter + 1

            if bluetoothbuffer.leveltwo.errorCode() > 0:
                raise Exception("Error code returned from inverter - during logon - wrong password?")

            inverterserialnumber = bluetoothbuffer.leveltwo.getFourByteLong(16)
            invName = SMASolarMQTT_library.getInverterName(btSocket, packet_send_counter, mylocalBTAddress,
                                                           InverterCodeArray,
                                                           AddressFFFFFFFF)
            packet_send_counter += 1

            client = mqtt.Client()
            client.on_connect = on_connect
            client.on_message = on_message
            client.connect("localhost", 1883, 60)

            while True:

                # MQTT Blocking call that processes network traffic, dispatches callbacks and handles reconnecting.
                client.loop()

                # Make sure the packet counter wont exceed 8 bits
                if packet_send_counter > 200:
                    packet_send_counter = 0

                L2 = SMASolarMQTT_library.spotvalues_ac(btSocket, packet_send_counter, mylocalBTAddress,
                                                        InverterCodeArray,
                                                        AddressFFFFFFFF)
                packet_send_counter += 1

                payload = "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9}".format(L2[1][1], L2[2][1], L2[3][1], L2[4][1],
                                                                           L2[5][1],
                                                                           L2[6][1], L2[7][1], L2[8][1], L2[9][1],
                                                                           L2[10][1])
                client.publish("emonhub/rx/50/values", payload=payload, qos=0, retain=False)
                SMASolarMQTT_library.time.sleep(1)

                # print "dc watts"
                L2 = SMASolarMQTT_library.spotvalues_dcwatts(btSocket, packet_send_counter, mylocalBTAddress,
                                                             InverterCodeArray,
                                                             AddressFFFFFFFF)
                packet_send_counter += 1
                payload = "{0}".format(L2[1][1])
                client.publish("emonhub/rx/52/values", payload=payload, qos=0, retain=False)
                SMASolarMQTT_library.time.sleep(1)

                # print "dc"
                # These values only updated every 5 mins
                L2 = SMASolarMQTT_library.spotvalues_dc(btSocket, packet_send_counter, mylocalBTAddress,
                                                        InverterCodeArray,
                                                        AddressFFFFFFFF)
                packet_send_counter += 1
                payload = "{0},{1}".format(L2[1][1], L2[2][1])
                client.publish("emonhub/rx/51/values", payload=payload, qos=0, retain=False)
                SMASolarMQTT_library.time.sleep(1)

                # print "yield"
                L2 = SMASolarMQTT_library.spotvalues_yield(btSocket, packet_send_counter, mylocalBTAddress,
                                                           InverterCodeArray,
                                                           AddressFFFFFFFF)
                packet_send_counter += 1
                payload = "{0},{1},{2},{3}".format(L2[1][1], L2[2][1], L2[3][1], L2[4][1])
                client.publish("emonhub/rx/53/values", payload=payload, qos=0, retain=False)
                SMASolarMQTT_library.time.sleep(1)

                # Time in seconds between readings - about 60 seconds is more than enough!
                SMASolarMQTT_library.time.sleep(5)

        except bluetooth.btcommon.BluetoothError as inst:
            print >> sys.stderr, "Bluetooth Error"
            # print >>sys.stderr, type(inst)     # the exception instance
            # print >>sys.stderr, inst.args      # arguments stored in .args
            # print >>sys.stderr, inst           # __str__ allows args to printed directly
            traceback.print_exc(file=sys.stderr)

            btSocket.close()
            # Give bluetooth time to recover
            SMASolarMQTT_library.time.sleep(20)

        except Exception as inst:
            # print >>sys.stderr, type(inst)     # the exception instance
            # print >>sys.stderr, inst.args      # arguments stored in .args
            # print >>sys.stderr, inst           # __str__ allows args to printed directly
            traceback.print_exc(file=sys.stderr)

            btSocket.close()
            SMASolarMQTT_library.time.sleep(20)


parser = argparse.ArgumentParser(
    description='Report generation statistics from SMA photovoltaic inverter over a shared MQTT hub.',
    epilog='Copyright 2013-2015 Stuart Pittaway.')

parser.add_argument('addr', metavar='addr', type=str,
                    help='Bluetooth address of SMA inverter in 00:80:22:11:cc:55 format, run hcitool scan to find yours.')

parser.add_argument('passcode', metavar='passcode', type=str,
                    help='NUMERIC pass code for the inverter, default of 0000.')

args = parser.parse_args()

main(args.addr, args.passcode)

exit()