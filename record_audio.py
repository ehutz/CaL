import argparse
from sys import byteorder
from array import array
from struct import pack
import pyaudio
import wave
from mongoHelper import *
import mongodb_setup

# START: Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-p", type=str, help="PATH")
parser.add_argument("-t", type=float, help="RECORD_TIME_SEC")
parser.add_argument("-r", type=int, help="RATE")
parser.add_argument("-c", type=str, help="IP")
parser.add_argument("-s", type=str, help="SESSION")
parser.add_argument("-f", type=str, help="FILENAME")
args = parser.parse_args()

path = ""
record_sec = 0
RATE = 44100
host_ip = ""
conn = None
session_name = ""
requested_audio_filename = ""

if args.p:
    path = args.p
if args.t:
    record_sec = args.t
if args.r:
    RATE = args.r
if args.c:
    host_ip = args.c
    conn = MongoClient(host_ip, 27017)
if args.s:
    session_name = args.s
if args.f:
    requested_audio_filename = args.f
    session_name = args.f
        
print('PAST ARGS')

THRESHOLD = 500
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 44100

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

"Records from the microphone and outputs the resulting data to 'path'"
sample_width, data = record(float(record_sec))
data = pack('<' + ('h'*len(data)), *data)

wf = wave.open(path, 'wb')
wf.setnchannels(1)
wf.setsampwidth(sample_width)
wf.setframerate(RATE)
wf.writeframes(data)
wf.close()

addSessionAudio(conn, session_name, requested_audio_filename+'.wav')
setStatus(conn, session_name, 'COMPLETE')
