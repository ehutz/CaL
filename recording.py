#!/usr/bin/env python3
#Author:        Jordan Biss
#Date Modified: 30 April 18
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
# block or sig so then strip and remove : so everything is space separated,
# then add it to the list of sig strings
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
# each signature dictionary into a list of dictionaries.
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
					# keys = ['time_found', 'image']
					# mqDict = {x:dict[x] for x in keys}
					# pprint.pprint(mqDict)
					file = open(filename,"rb")
					dict['image'] = file.read()
					msg['image'] = dict['image']
					msg['message'] = dict['time_found']
					print("SENDING TIMESTAMP/IMAGE")
					channel.basic_publish(exchange=rmq_params.rmq_params["exchange"],
								routing_key=rmq_params.rmq_params["pixycam_queue"],
								body=pickle.dumps(msg))
					dict['just_sent'] = True
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
# requestPixycamFrame call. The dictList holds each sig from stringList after it
# has been converted to a dictionary by the convertToDict call. The for loop 
# updates the data of all sigs using the most recently detected sigs by iterating
# through dictList. If the size of the database is 0, insert the elem. Otherwise,
# iterate through each item in the database. If the sig of the current element
# in dictList matches a sig in the database, it updates it; if the sig is not in
# the database, insert it.
def runPixy():
	while True:
		stringList = []
		requestPixycamFrame(stringList)
		tempDictList = convertToDict(stringList)
		compareToMaster(tempDictList)
		#print("MASTER DICT:" + str(len(dictList)))
		for elem in dictList:
			if(elem['history'] > 5) and elem['just_sent'] == True:
				pprint.pprint(elem)
				elem['just_sent'] = False
				
				
#Main -> Creates a process to read, store, and update data provded by the PixyCam.
# Runs the flask app to connect to and communicate with the server. Then joins
# these two processes together.
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
				