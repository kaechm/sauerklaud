#!/usr/bin/env python
# -*- coding: utf-8 -*-

HOST = "localhost"
PORT = 4223


from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_dual_button import BrickletDualButton
from tinkerforge.bricklet_piezo_speaker import BrickletPiezoSpeaker
from tinkerforge.brick_imu_v2 import BrickIMUV2

import paho.mqtt.client as mqtt
from math import sqrt
import time
import private_settings as pset

# Callback function for state changed callback
def cb_state_changed(button_l, button_r, led_l, led_r):
    
    #if button_l == DualButton.BUTTON_STATE_PRESSED:
    #    print("Left button pressed")
    #else:
    #    print("Left button released")
    #
    #if button_r == DualButton.BUTTON_STATE_PRESSED:
    #    print("Right button pressed")
    #else:
    #    print("Right button released")

    print("button pressed")
    ps.beep(20, 500) # 200ms beep 1kHz
    #print("beeped")
    
    
    # Orientierung
    w, x, y, z = imu.get_quaternion()
    #print("w: {:.02f}, x: {:.02f}, y: {:.02f}, z: {:.02f}"
    #      .format(w/16383.0, x/16383.0, y/16383.0, z/16383.0))
    
    # Temperatur
    temp = imu.get_temperature()
	
    #print 'Temperatur: ',temp

    #print 'Lineare Beschleunigung: ', a, ', ', b, ', ', c 

    client.publish('dog/activity', payload='button')

if __name__ == "__main__":
    # Create IP connection
    ipcon = IPConnection()
    
    # CREATE DEVICE OBJECTS #########################################
    # Create BUTTON device object
    db = BrickletDualButton(pset.UIDdualbutton, ipcon)
    # Create PIEZO SPEAKER device object
    ps = BrickletPiezoSpeaker(pset.UIDpiezo, ipcon) # Create device object
    imu = BrickIMUV2(pset.UIDimu, ipcon) # Create device object

    # Connect to brickd
    ipcon.connect(HOST, PORT)
    # Don't use device before ipcon is connected


    # Connect to Cloud
    client = mqtt.Client()
    client.username_pw_set('miro','1234')
    client.connect('m21.cloudmqtt.com', 13840, 60)
    



    # Register state changed callback to function cb_state_changed
    db.register_callback(db.CALLBACK_STATE_CHANGED, cb_state_changed)

    ticks = time.time() # Anz. Sekunden
    
    beschleunigung = 0.2 # Lin.Beschleunigung (max. in letzter Zeiteinheit)

    # Main loop
    while True:

        # Lineare Beschleunigung
        a, b, c = imu.get_linear_acceleration()
        betrag = sqrt(pow(a, 2)+pow(b, 2)+pow(c, 2))
        if betrag > beschleunigung:
            beschleunigung = betrag

        if time.time() > ticks+1.0:
            # Reset
            #print 'Max Beschleunigung letzte Sekunde: ', beschleunigung, ' (', ticks, ')'

            if beschleunigung > 1000:
                # Event ausloesen
                ps.beep(50, 2000) # 200ms beep 1kHz
                client.publish('dog/hello', payload='activity')

            ticks = time.time()
            beschleunigung = 0.0


    ipcon.disconnect()