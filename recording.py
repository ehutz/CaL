#!/usr/bin/env python3
#Author:        Jordan Biss
#Date Modified: 30 April 18
#
#The PixyCam angle measurement goes from -180 to 180 degrees. When the lower CC Sig
# is on the right and the higher CC Sig is on the left, the angle is 0 degrees. 
# Therefore, when the CC object is facing right, the angle is zero. As the CC object
# rotates clockwise, the angle becomes negative. As the CC object rotates 
# counterclockwise, the angle becomes positive.
#The coordinates start with (0,0) in the upper left corner. The max X value is
# 320 to the right. The max Y value is 200 down.

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
import sys #probably don't need any more
import re
import os
import time
import multiprocessing
from pymongo import MongoClient #shouldnt need both
import pymongo
from flask import * #shouldnt need from
import pprint
from pptx import Presentation
import PyPDF2
import webbrowser
from picamera import PiCamera

#GLOBAL Variables
dictList = []
conn = MongoClient('192.168.1.16', 27017)

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
					#print('/slides/' + str(dict['time_found']) + '.jpg')
					camera.capture('slides/' + str(dict['time_found']) + '.jpg')
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
		print("CURRET FRAME DICT SIZE: " + str(len(tempDictList)))
		compareToMaster(tempDictList)
		print("MASTER DICT")
		print(len(dictList))
		for elem in dictList:
			if(elem['history'] > 5):
				#Send to server
				pprint.pprint(elem)
		print('\n')
		

		# for elem in dictList:
			# found = False;
			# if collection.count() == 0:
				# collection.insert_one(elem)
				# pprint.pprint(elem)
			# else:
				# for temp in collection.find():
					# if(elem['sig'] == temp['sig']):
						# found = True;
						# #collection.replace_one({'sig':elem['sig']}, elem)
				# if not found:
					# collection.remove()
					# collection.insert_one(elem)
					# pprint.pprint(elem)
		# print(collection.count())

#Main -> Creates a process to read, store, and update data provded by the PixyCam.
# Runs the flask app to connect to and communicate with the server. Then joins
# these two processes together.

try:
	#Set up camera
	camera = PiCamera()
	camera.start_preview()
	time.sleep(2)
	print("CAMERA RUNNING")

	#Set up piping from ./hello_pixy executable
	process = subprocess.Popen(['sudo', './hello_pixy'], stdout=subprocess.PIPE)
	runPixy()
finally:
	camera.stop_preview()
	print("CAMERA STOPPED")
	
	
	
	
	