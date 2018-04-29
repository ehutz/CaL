#!/usr/bin/env python3
import logging
import socket
import sys
import array
import datetime
from time import sleep, time
from flask import Flask, request, abort
from zeroconf import ServiceInfo, Zeroconf
import fcntl
import struct
import mongodb_setup

# Audio code below found at : https://stackoverflow.com/questions/892199/detect-record-audio-in-python

# Installing pyaudio on your raspberry pi
# Follow instructions at https://www.raspberrypi.org/forums/viewtopic.php?t=25173
    # sudo apt-get update
    # sudo apt-get upgrade
    # sudo git clone http://people.csail.mit.edu/hubert/git/pyaudio.git
    # sudo apt-get install libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev
    # sudo apt-get install python3-dev
    # cd pyaudio
    # sudo python3 setup.py install

from sys import byteorder
from array import array
from struct import pack

import pyaudio
import wave

THRESHOLD = 500
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 44100
RECORD_SECONDS = 20 # 1 hour and 20 minutes (4800 seconds)

def is_silent(snd_data):
    "Returns 'True' if below the 'silent' threshold"
    return max(snd_data) < THRESHOLD

def normalize(snd_data):
    "Average the volume out"
    MAXIMUM = 16384
    times = float(MAXIMUM)/max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i*times))
    return r

def trim(snd_data):
    "Trim the blank spots at the start and end"
    def _trim(snd_data):
        snd_started = False
        r = array('h')

        for i in snd_data:
            if not snd_started and abs(i)>THRESHOLD:
                snd_started = True
                r.append(i)

            elif snd_started:
                r.append(i)
        return r

    # Trim to the left
    snd_data = _trim(snd_data)

    # Trim to the right
    snd_data.reverse()
    snd_data = _trim(snd_data)
    snd_data.reverse()
    return snd_data

def add_silence(snd_data, seconds):
    "Add silence to the start and end of 'snd_data' of length 'seconds' (float)"
    r = array('h', [0 for i in range(int(seconds*RATE))])
    r.extend(snd_data)
    r.extend([0 for i in range(int(seconds*RATE))])
    return r

def record():
    """
    Record a word or words from the microphone and 
    return the data as an array of signed shorts.

    Normalizes the audio, trims silence from the 
    start and end, and pads with 0.5 seconds of 
    blank sound to make sure VLC et al can play 
    it without getting chopped off.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=1, rate=RATE,
        input=True, output=True,
        frames_per_buffer=CHUNK_SIZE)

    num_silent = 0
    snd_started = False

    r = array('h')

    #while 1:
    for i in range(0, int(44100 / CHUNK_SIZE * RECORD_SECONDS)):
        # little endian, signed short
        snd_data = array('h', stream.read(CHUNK_SIZE))
        if byteorder == 'big':
            snd_data.byteswap()
        r.extend(snd_data)

        silent = is_silent(snd_data)

        if silent and snd_started:
            num_silent += 1
        elif not silent and not snd_started:
            snd_started = True

    sample_width = p.get_sample_size(FORMAT)
    stream.stop_stream()
    stream.close()
    p.terminate()

    r = normalize(r)
    #r = trim(r)
    #r = add_silence(r, 0.5)
    return sample_width, r

def record_to_file(path):
    "Records from the microphone and outputs the resulting data to 'path'"
    sample_width, data = record()
    data = pack('<' + ('h'*len(data)), *data)

    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()

if __name__ == '__main__':
    print("please speak a word into the microphone")
    record_to_file('test.wav')
    print("done - result written to test.wav")

'''
if __name__ == '__main__':
    app = Flask(__name__)
    
    
    def reviewTimer():
        printout = ""
        list_out = ""
        if len(laps) > 0:
            list_out = "Lap List: \n\r" + " seconds,\n\r".join(laps) + " seconds"
        if start <= 0:
            printout = "Last timer end length: " + str(stop)
        else:
            printout = "Current running time: " + str(time() - start) + " seconds"
        return  ("This is a timer. \n\r"
        + printout
        + "\n"
        + list_out
        + "\n")


    def startTimer():
        global start, laps
        start = time()
        laps=[]
        return "starting timer!"
    
    
    def checkTimer():
        if start > 0:
            curr_lap = time() - start
            return str(curr_lap)
        else:
            return "not running"


    def stopTimer():
        global stop, start
        if start > 0:
            stop = time() - start
            start = 0
            return str(stop)
        else:
            return "you must start the timer"
    
    
    def lapTimer():
        global start, laps
        curr_lap = time() - start
        laps.append(str(curr_lap))
        return str(curr_lap)


    @app.route("/timer",  methods = ['GET'])
    def getTimer():
        fcn = request.args.get('fcn', type=str, default= "")
        if fcn == "check":
            return checkTimer() + "\n"
        return reviewTimer() + "\n"


    @app.route("/timer",  methods = ['POST'])
    def postTimer():
        fcn = request.args.get('fcn', type=str, default="")
        ret = ""
        print(fcn)
        if fcn == "start":
            ret = startTimer()
        elif fcn == "stop":
            ret = stopTimer()
        elif fcn == "lap":
            ret = lapTimer()
        return (ret + "\n\r")

    
    app.run(host="0.0.0.0", port=20000, debug=True)
       
    try:
        while True:
            print("running")
            sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        print("Unregistering...")
        zeroconf.unregister_service(info)
        zeroconf.close()
'''
