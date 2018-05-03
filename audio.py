#!/usr/bin/env python3
from pathlib import Path
import logging
import socket
import sys
import array
import datetime
from time import sleep, time, mktime
from flask import Flask, request, abort, send_file
from zeroconf import ServiceInfo, Zeroconf
import fcntl
import struct
import mongodb_setup
from mongoHelper import *

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

import argparse

# START: Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-s", help="TCP_IP")
args = parser.parse_args()
if args.s:
    host_ip = args.s

THRESHOLD = 500
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 44100
#RECORD_SECONDS = 20 # 1 hour and 20 minutes (4800 seconds)

conn = MongoClient(host_ip, 27017)

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

def record(record_sec):
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
    for i in range(0, int(44100 / CHUNK_SIZE * record_sec)):
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

def record_to_file(path, record_sec):
    "Records from the microphone and outputs the resulting data to 'path'"
    sample_width, data = record(float(record_sec))
    data = pack('<' + ('h'*len(data)), *data)

    wf = wave.open(path, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(sample_width)
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()

if __name__ == '__main__':
    print('[Checkpoint] audio.py running...')
    
    app = Flask(__name__)

    @app.route("/audio/record",  methods = ['GET'])
    def recordAudio():
        global requested_audio_filename
        requested_audio_filename = request.args.get('filename', type=str, default= "")
        session_name = request.args.get('session', type=str, default= "")
        global time_to_record_sec
        time_to_record_sec = request.args.get('record_time_sec', type=float, default= -1)
        print(time_to_record_sec)
        print("Recording...")
        global audio_record_start_time
        audio_record_start_time = mktime(datetime.datetime.now().timetuple())
        record_to_file('../CaL_Audio/'+requested_audio_filename + '.wav', time_to_record_sec)
        print("Finished Recording")
        addSessionAudio(conn, session_name, requested_audio_filename+'.wav')
        return "Done - result written to " + requested_audio_filename + '.wav'
            
    @app.route("/audio/retrieve_file",  methods = ['GET'])
    def getAudio():
        if Path('../CaL_Audio/'+requested_audio_filename+'.wav').is_file():
            print('Sending file...')
            return send_file('../CaL_Audio/'+requested_audio_filename + '.wav', mimetype="audio/wav", as_attachment=True,
                             attachment_filename=requested_audio_filename + '.wav')
        else:
            print('File DNE')
            return requested_audio_filename + ".wav file does not exist."
    
    @app.route("/status", methods=['GET'])
    def status():
        if (float(audio_record_start_time)+float(time_to_record_sec)*2) > mktime(datetime.datetime.now().timetuple()):
            return 'SESSION IN PROGRESS'
        else:
            return 'SESSION COMPLETE'

    app.run(host="0.0.0.0", port=20000, debug=True)
       
    try:
        while True:
            sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        print("Done")
