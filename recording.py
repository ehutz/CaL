#!/usr/bin/env python3
#Author:        Jordan Biss
#Date Modified: 05 May 18
#
#Hooking up PixyCam to RaspberryPi: 
#http://www.cmucam.org/projects/cmucam5/wiki/Hooking_up_Pixy_to_a_Raspberry_Pi
#	sudo apt-get install libusb-1.0-0.dev
#	sudo apt-get install libboost-all-dev
#	sudo apt-get install cmake
#	git clone https://github.com/charmedlabs/pixy.git
#	cd pixy/scripts
#	./build_libpixyusb.sh
#	sudo ./install_libpixyusb.sh
#Hooking up PiCamera to RaspberryPi:
#https://projects.raspberrypi.org/en/projects/getting-started-with-picamera
#	Open the RaspberryPi Configuration Tool
#	Enable Camera
#	Reboot

import json
import subprocess
import sys
import re
import os
import time
import multiprocessing
import pprint
from picamera import PiCamera
import rmq_params
import pika
import pickle
import argparse

# START: Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-s", help="TCP_PORT")
args=parser.parse_args()
rmq_host = "0.0.0.0"
if args.s:
    rmq_host = args.s
	
#GLOBAL Variables
dictList = []

#Gets line from hello_pixy exe. If the line contains "frame", increment. This
# allows the storage of each line prior to getting the following frame. If
# the line contains "sig", check if the line contains "CC Block!" and remove
# it, otherwise its a normal sig. Output is now standardized regardless of CC
# block or sig so then strip and remove : so everything is space separated.
# Add the current time to the string to signify when the signature was detected.
# Then add it to the list of sig strings.
def requestPixycamFrame(temp = []):
	frame = 0
	while frame != 2:
		output = process.stdout.readline().decode()
		output2 = ""
		if output.find('frame')  != -1:
			frame += 1
		elif output.find('sig') != -1:
			if output.find('CC block!') != -1:
				output2 = removeCCStrings(output)
			else:
				output2 = output
			output3 = output2.strip().replace(':','')
			output3 += ' time_found ' + str(int(time.time()))
			temp.append(output3)
	return;

#For color code detections, CC block! needs to be removed from
# the raw string.
def removeCCStrings(string):
	temp = string.replace('CC block!','')
	output = re.sub(r'\(.*\)', '', temp)
	return output
	
#Takes the list of each signature's respective string of data
# and converts each signature string to a sig dictionary and stores
# each signature dictionary into a list of dictionaries. For this project,
# the x, y, height, and width does not matter so this data is removed. A
# just_sent key is added to keep track of when the signature info is sent
# to RabbitMQ. An image key is added as well to refer to the image captured
# at the time the signature is detected.
def convertToDict(temp):
	list = []
	tempDict = {}
	tempDictList = []
	for elem in temp:
		list = elem.split()
		tempDict = dict(zip(list[::2],list[1::2]))
		del tempDict['x']
		del tempDict['y']
		del tempDict['height']
		del tempDict['width']
		tempDict['just_sent'] = False
		tempDict['image'] = ""
		tempDictList.append(tempDict)
	return tempDictList
		
#Takes the list of dictionaries from the current frame and compares to
# the master list. The master list also assigns a history value to each
# signature which acts as a debouncing mechanism for false positives and
# assures accurate transitions between colors. If no signatures were detected
# in the most recent frame, then any signature in the master list needs to
# decrement it's history. Otherwise, iterate through each item recently detected.
# Compare each signature in the master list to the signatures in the current frame, 
# if the signature is already stored in the master list, increment it's history 
# (up to 25). If the history equals 5, then it has officially detected a transition 
# and an image needs to be saved. The image taken by the PiCam is saved locally as 
# well as read in binary into the image key of the signature's dictionary. The image
# binary and the timestamp of the signature is then published to RabbitMQ and
# the just_sent key is set to True. If the signature from the current frame is
# found, then the loop is broken out of to prevent multiple increments due to
# multiple detections of the same signature in a single frame. If the signature
# from the master list is not found in the current frame, it's history is decremented.
# If the history drops below zero, it is removed from the master list. If an item in
# the current frame is not found in the master list, set it's history to 1 and add it
# to the master list.
def compareToMaster(tempDictList):
	if(len(tempDictList) == 0):
		for dict in dictList:
			dict['history'] = dict['history'] - 1
			if(dict['history'] < 0):
				dictList.remove(dict)
	for elem in tempDictList:
		found = False
		for dict in dictList:
			if(dict['sig'] == elem['sig']):
				found = True
				if(dict['history'] < 25):
					dict['history'] = dict['history'] + 1
				if(dict['history'] == 5):
					filename = 'sent/' + str(dict['time_found']) + '.jpg'
					camera.capture(filename)
					file = open(filename,"rb")
					dict['image'] = file.read()
					msg['image'] = dict['image']
					msg['message'] = dict['time_found']
					print("TRANSITION DETECTED")
					print("SENDING TIMESTAMP/IMAGE...")
					channel.basic_publish(exchange=rmq_params.rmq_params["exchange"],
								routing_key=rmq_params.rmq_params["pixycam_queue"],
								body=pickle.dumps(msg))
					dict['just_sent'] = True
					print("TIMESTAMP/IMAGE SENT")
				break
			else:
				dict['history'] = dict['history'] - 1
				if(dict['history'] < 0):
					dictList.remove(dict)
		if(found == False):
			elem['history'] = 1
			dictList.append(elem)
		else:
			break
	
#The stringList holds data from a single frame, each position in the list holds a
# string containing a signature and its data. The string list is populated by the
# requestPixycamFrame call. The tempDictList holds each sig from stringList after it
# has been converted to a dictionary by the convertToDict call. The compareToMaster
# function then accounts for debouncing, determines if a transition has occured
# in order to determine what needs sent to RabbitMQ, and updates the master list.
# The for loop iterates through each item in the master list to reset any flags raised 
# during compareToMaster. This prevents a signature from being sent multiple times.
def runPixy():
	while True:
		stringList = []
		requestPixycamFrame(stringList)
		tempDictList = convertToDict(stringList)
		compareToMaster(tempDictList)
		for elem in dictList:
			if(elem['history'] > 5) and elem['just_sent'] == True:
				elem['just_sent'] = False
				
				
#Main intializes the PiCam, RabbitMQ, and a subprocess to read data from the PixyCam.
# It then calls runPixy which runs continuously until exited by the user. If any errors
# occur or the program fails for any reason at any point, the PiCam will be correctly
# shut down to prevent memory issues.
try:
	#Set up camera
	camera = PiCamera()
	camera.start_preview()
	time.sleep(2)
	print("CAMERA RUNNING")
	
	# Setup RabbitMQ
	print("SETTING UP RABBITMQ")
	credentials = pika.PlainCredentials(rmq_params.rmq_params["username"], rmq_params.rmq_params["password"])
	parameters = pika.ConnectionParameters(rmq_host, 5672, rmq_params.rmq_params["vhost"], credentials)
	connection = pika.BlockingConnection(parameters)
	channel = connection.channel()
	msg = {'username': rmq_params.rmq_params['username'], 'password':rmq_params.rmq_params['password'], 'message': "", 'image': ""}
	print("RABBITMQ SETUP COMPLETE")
	
	#Set up piping from ./hello_pixy executable
	process = subprocess.Popen(['sudo', './hello_pixy'], stdout=subprocess.PIPE)
	runPixy()
finally:
	camera.stop_preview()
	print("CAMERA STOPPED")
				