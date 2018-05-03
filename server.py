from pathlib import Path
from flask import Flask, send_file, request, abort
import logging
import socket
import sys
from time import sleep, mktime
import requests
#from canvas_token import *
import json
from collections import OrderedDict
from pprint import pprint
from mongoHelper import *
from pymongo import MongoClient
import rmq_params
import pika
import pickle
import datetime

import argparse

# START: Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-t", type=float, help="RECORD_TIME")
args = parser.parse_args()
if args.t:
    audio_record_time_seconds = args.t
    
get_now = datetime.datetime.now()
server_start_time = mktime(get_now.timetuple())
session = get_now.strftime("Session_%Y_%m_%d_%H_%M_%S")

STATUS = 'IN PROGRESS' # Initial status state

# START: Setup RabbitMQ
credentials = pika.PlainCredentials(rmq_params.rmq_params["username"], rmq_params.rmq_params["password"])
parameters = pika.ConnectionParameters('localhost', 5672, rmq_params.rmq_params["vhost"], credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# Declaire RabbitMQ exchange
channel.exchange_declare(exchange=rmq_params.rmq_params["exchange"], exchange_type='direct', auto_delete=True)

# Declare client queue
channel.queue_declare(queue=rmq_params.rmq_params["client_queue"], auto_delete=True)
channel.queue_bind(exchange=rmq_params.rmq_params["exchange"], queue=rmq_params.rmq_params["client_queue"])

# Declare PixyCam Client queue
channel.queue_declare(queue=rmq_params.rmq_params["pixycam_queue"], auto_delete=True)
channel.queue_bind(exchange=rmq_params.rmq_params["exchange"], queue=rmq_params.rmq_params["pixycam_queue"])
            
conn = MongoClient('localhost', 27017)
addSession(conn, session)
pprint(getSessions(conn))
pprint(getUsernames(conn))
'''
token = {'access_token': canvas_token}
downloadable_files = []
downloadable_files_w_url = []

def check_username_password():
    if request.authorization == None:
        return True
    username = request.authorization.username
    password = request.authorization.password
    if collection.find({'username': username, 'password':password}).count() > 0:
        return True
    return False

def list_group_files():
    global downloadable_files
    downloadable_files = []
    global downloadable_files_w_url
    downloadable_files_w_url = []
    r = requests.get('https://canvas.instructure.com/api/v1/groups/45110000000052696/files', params=token)
    list = json.loads(r.text)
    for obj in list:
        filename_key = ["display_name"]
        temp = {x:obj[x] for x in filename_key}
        downloadable_files.append(temp)
        
        keys = ["display_name", "id", "url"]
        temp_url = {y:obj[y] for y in keys}
        downloadable_files_w_url.append(temp_url)
    return json.dumps(downloadable_files, indent=4, sort_keys=True)
		
def download(requested_file):
    downloadable = False
    list_group_files()
    file = []
    while not downloadable:
        pprint(downloadable_files_w_url)
        for elem in downloadable_files_w_url:
            if elem["display_name"] == requested_file:
                downloadable = True
                file = elem
                break
    
    r = requests.get(file["url"], params=token, stream=True)
    if r.status_code == 200:
        with open(requested_file, 'wb') as f:
            f.write(r.content)
            return "Success"
    else:
        return "Failed"
  
def upload(filename, file):
    data = {'name': filename, 'parent_folder_path': ''}

    r = requests.post('https://canvas.instructure.com/api/v1/groups/45110000000052696/files', data=data, params=token)
    list = json.loads(r.text)
    
    #'key' key must go first?? 'file' key must go last.
    files = OrderedDict([
            ('key', list["upload_params"]["key"]),
            ('Filename', list["upload_params"]["Filename"]),
            ('Policy', list["upload_params"]["Policy"]),
            ('acl', list["upload_params"]["acl"]),
            ('content-type', list["upload_params"]["content-type"]),
            ('success_action_redirect', list["upload_params"]["success_action_redirect"]),
            ('x-amz-algorithm', list["upload_params"]["x-amz-algorithm"]),
            ('x-amz-credential', list["upload_params"]["x-amz-credential"]),
            ('x-amz-date', list["upload_params"]["x-amz-date"]),
            ('x-amz-signature', list["upload_params"]["x-amz-signature"]),
            #Might be able to upload as different name through this
            ('file', file)])
    r = requests.post(list["upload_url"], files = files)
    return 'File successfully uploaded to Canvas!'
'''
def callback_client(ch, method, properties, body):
    bod = pickle.loads(body)
    pprint(pickle.loads(body))
    
    addTimestamp(conn, bod['username'], session, str(bod['message'] - server_start_time), None)
    
    #exit() # Used to terminate server
        
def callback_pixycam(ch, method, properties, body):
    bod = pickle.loads(body)
    pprint(pickle.loads(body))
    
    addTimestamp(conn, bod['username'], session, str(bod['message'] - server_start_time), None)
    
    #exit() # Used to terminate server
        
if __name__ == '__main__':
    # Run Flask server
    app = Flask(__name__)
    
    @app.route("/status", methods=['GET'])
    def status():
        print(server_start_time+audio_record_time_seconds)
        print(mktime(datetime.datetime.now().timetuple()))
        if (float(server_start_time) + float(audio_record_time_seconds)*2) > mktime(datetime.datetime.now().timetuple()):
            return 'SESSION IN PROGRESS'
        else:
            return 'SESSION COMPLETE'
        
    @app.route("/audio", methods=['GET'])
    def audio():  
        audio_file = requests.get('http://0.0.0.0:20000/audio/retrieve_file?filename='+ session)
        print(audio_file.headers['content-type'])
        return 'UNDER CONSTRUCTION'
	#if Path('~/CaL/'+audio_file).is_file():
            #return send_file(audio_file, mimetype="audio/wav",attachment_filename=audio_file)
        #else:
            #return audio_file # This is a DNE message from audio.py
    '''
    @app.route("/led", methods=['GET', 'POST'])
    def led():
        is_valid = check_username_password()
        led_exists = (LED_IP != '')
        if(is_valid and led_exists):
            if request.method == 'GET':
                r = requests.get('http://'
                                 + LED_IP
                                 + ':'
                                 + str(LED_Port)
                                 + request.path)
                return r.text
            else: #request.method == 'POST'
                led_data = str(request.get_data()).replace("b'",'').replace("'",'')
                r = requests.post('http://'
                                  + LED_IP
                                  + ':'
                                  + str(LED_Port)
                                  + request.path,
                                  params=led_data)
                return r.text
        elif not is_valid:
            abort(403)
        elif not led_exists:
            abort(503)
        return 'Bad'
            
    @app.route("/timer", methods=['GET', 'POST'])
    def timer():
        is_valid = check_username_password()
        custom_exists = (Custom_IP != '')
        if(is_valid and custom_exists):
            if request.method == 'GET':
                if request.args.get('fcn') != None:
                    r = requests.get('http://'
                                     + Custom_IP
                                     + ':'
                                     + str(Custom_Port)
                                     + request.path,
                                     params='fcn='
                                     + request.args.get('fcn'))
                else:
                    r = requests.get('http://'
                                     + Custom_IP
                                     + ':'
                                     + str(Custom_Port)
                                     + request.path)
                return r.text
            else: #request.method == 'POST'
                custom_data = str(request.get_data()).replace("b'",'').replace("'",'')
                r = requests.post('http://'
                                  + Custom_IP
                                  + ':'
                                  + str(Custom_Port)
                                  + request.path,
                                  params=custom_data)
                return r.text
        elif not is_valid:
            abort(403)
        elif not custom_exists:
            abort(503)
        return 'Bad'
    '''
    #app.run(host="0.0.0.0", port=20002, debug=True)
    
    # END: FLASK
    
    try:
        while True:
            # Tell audio to start recording
            r = requests.get('http://0.0.0.0:20000/audio/record?filename='
                             + session
                             + '&session='
                             + session
                             + '&record_time_sec='
                             + str(audio_record_time_seconds))
            print('[Checkpoint] GET request to audio.py to record sent')
            channel.basic_consume(callback_client,
                      queue=rmq_params.rmq_params["client_queue"],
                      no_ack=True)
            
            channel.basic_consume(callback_pixycam,
                      queue=rmq_params.rmq_params["pixycam_queue"],
                      no_ack=True)

            channel.start_consuming()

            sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        pass
        

    
