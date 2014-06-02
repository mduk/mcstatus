#!/usr/bin/env python

import os
import serial
import socket
import sys
import time
import datetime
from argparse import ArgumentParser

from minecraft_query import MinecraftQuery

def main():
    parser = ArgumentParser( description="Monitor a Minecraft server for activity" )
    parser.add_argument( "host",
        help="hostname of server to monitor"
    )
    parser.add_argument( "-n", "--notify",
        help="trigger a Mac OS X notification (using terminal-notifier)",
        default=False,
        action='store_true'
    ) 
    parser.add_argument( "-l", "--led",
        help="toggle an LED for activity",
        default=False,
        action='store_true'
    )
    parser.add_argument( "-sd", "--serial-dev",
        help="Serial device to use for LED",
        default="/dev/tty.usbserial-A8007qt3"
    )
    parser.add_argument( "-sb", "--serial-baud",
        help="Serial baudrate to use for LED",
        default=115200
    )
    options = parser.parse_args()

    notifyState = None

    if options.led:
        arduino = serial.Serial( options.serial_dev, options.serial_baud, stopbits=serial.STOPBITS_TWO )

    while 1:
        try:
            query = MinecraftQuery(options.host, 25565, timeout=10, retries=3)
            response = query.get_rules()

            print_players( response )

            if options.notify:
                notifyState = notify( response, notifyState )

            if options.led:
                ledState = led( response, arduino )

        except socket.error as e:
            print "socket exception caught:", e.message

        time.sleep(10)

def led(response, arduino):
    if response['numplayers'] > 0:
        arduino.write("W01")
    else:
        arduino.write("W00")

def notify(response, numplayers):
    if response['numplayers'] == numplayers:
        return numplayers

    players = response['players']
    numplayers = response['numplayers']

    if numplayers == 1:
        msg = players[0] + " is online"
    elif numplayers == 0:
        msg = "Server is empty"
    else:
        msg = ", ".join(players[:-1]) + " and " + players[-1] + " are online"

    t = '-title Minecraft'
    i = '-appIcon /Applications/Minecraft.app/Contents/Resources/favicon.icns'
    m = '-message {!r}'.format(msg)
    e = '-execute /Applications/Minecraft.app/Contents/MacOS/JavaApplicationStub'
    os.system('terminal-notifier {}'.format(' '.join([t, i, m, e])))

    return numplayers

def print_players( response ):
    time = str( datetime.datetime.now() )
    msg = "Server is empty"
    if response['numplayers'] > 0:
        msg = str( response['numplayers'] ) + " players online: " + ', '.join( response['players'] )
    print time + ' ' + msg

if __name__=="__main__":
    main()

