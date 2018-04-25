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


def getIP(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,
        struct.pack('256s', ifname[:15])
        )[20:24])
IP = getIP(b'wlan0')
start = 0
stop = 0
laps = []


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    
    if len(sys.argv) > 1:
        assert sys.argv[1:] == ['--debug']
        logging.getLogger('zeroconf').setLevel(logging.DEBUG)

    desc = {'path': '/timer'}
    hostname = socket.gethostname()
    info = ServiceInfo("_http._tcp.local.",
                       "Custom_RPI._http._tcp.local.",
                       socket.inet_aton(IP), 20000, 0, 0,
                       desc, "ash-2.local.")

    zeroconf = Zeroconf()
    print("Registration of a service, press Ctrl-C to exit...")
    zeroconf.register_service(info)

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

