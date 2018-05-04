import argparse
from audio import *
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
setStatus(conn, None, 'COMPLETE')
