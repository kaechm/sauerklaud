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
import json
import errno
from socket import gethostbyname,gaierror,error



# Callback function for state changed callback
def cb_state_changed(button_l, button_r, led_l, led_r):
    print("button pressed")
    ps.beep(20, 500) # 200ms beep 1kHz
    
    # Temperatur
    temp = imu.get_temperature()

    status = db.get_button_state()
    temp = imu.get_temperature()
    barking = db.get_button_state()
    status = {
        'name': pset.dog_name,
        'location_long': pset.dog_location_long,
        'location_lat': pset.dog_location_lat,
        'acceleration': betrag,
        'barking': barking[0],
        'temp': temp
    }

    publish_values('dog/hello', status)
    client.publish('dog/hello', payload='button')


def publish_values(topic, kwargs):
    payload = {'timestamp': time.time()}

    for key, value in kwargs.items():
        payload[key] = value

    publish_as_json(topic, payload, retain=True)


def publish_as_json(topic, payload, *args, **kwargs):
    client.publish(
        topic,
        json.dumps(payload, separators=(',', ':')),
        *args, **kwargs
    )

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
    #client.connect('m21.cloudmqtt.com', 13840, 60)

    # Register state changed callback to function cb_state_changed
    db.register_callback(db.CALLBACK_STATE_CHANGED, cb_state_changed)

    ticks = time.time() # Anz. Sekunden für activity timer
    ticks_connected = time.time(); # Anz. Sekunden für connection reset timer
    ticks_status = time.time()
    
    beschleunigung = 0.0 # Lin.Beschleunigung (max. in letzter Zeiteinheit)

    # Main loop
    while True:
        
        # Connecting to Cloud
        print('Trying to connect...')
        try:
            client.connect('m21.cloudmqtt.com', 13840, 60)
            imu.leds_on()
        except gaierror:
            time.sleep(3)
            print('Connection error, trying again... (3 sec)')
            imu.leds_off()
            continue

        # wir sind connected
        ticks_connected = time.time()
        print('Connected!')
        
        # Sensing loop
        while True:
        
            # Lineare Beschleunigung
            a, b, c = imu.get_linear_acceleration()
            betrag = sqrt(pow(a, 2)+pow(b, 2)+pow(c, 2))
            if betrag > beschleunigung:
                beschleunigung = betrag

            # SEND ACCELERATION (DO NOT PUBLISH!)
            if time.time() > ticks+0.1:

                if beschleunigung > 1000:
                    temp = imu.get_temperature()
                    w, x, y, z = imu.get_quaternion()
                    barking = db.get_button_state()
                    # client.publish('dog/activity', payload='button')
                    # client.publish('dog/activity', status[0])
                    status = {
                        'name': pset.dog_name,
                        'location_long': pset.dog_location_long,
                        'location_lat': pset.dog_location_lat,
                        'acceleration': betrag,
                        'barking': barking[0],
                        'temp': temp
                    }

                    # print(status)
                    # publish_values('dog/status', status)
                    # promt user with a 'beeep'
                    ps.beep(50, 2000) # 200ms beep 1kHz


                ticks = time.time()
                w, x, y, z = imu.get_quaternion()
                beschleunigung = 0.0

            # SEND STATUS
            if time.time() > ticks_status+1.0:
                temp = imu.get_temperature()
                w, x, y, z = imu.get_quaternion()
                barking = db.get_button_state()
                status = {
                    'name': pset.dog_name,
                    'location_long': pset.dog_location_long,
                    'location_lat': pset.dog_location_lat,
                    'acceleration': betrag,
                    'barking': barking[0],
                    'temp': temp
                }

                # print(status)
                publish_values('dog/status', status)

                ticks_status = time.time()

            # CONNECTED?
            if time.time() > ticks_connected+6.0:
                ticks_connected = time.time()
                try:
                    test = client.socket().recv(1)
                # except error:
                except:
                    try:
                        client.reconnect()
                        imu.leds_on()
                    except gaierror:
                        print('Connection lost, trying to reconnect...')
                        imu.leds_off()

    ipcon.disconnect()
