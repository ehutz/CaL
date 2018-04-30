from flask import Flask, request, abort
import logging
import socket
import sys
from time import sleep
import requests
from canvas_token import *
import json
from collections import OrderedDict
from pprint import pprint
import mongodb_setup
from pymongo import MongoClient
import rmq_params
import pika
import pickle

# START: Setup RabbitMQ
credentials = pika.PlainCredentials(rmq_params.rmq_params["username"], rmq_params.rmq_params["password"])
parameters = pika.ConnectionParameters('localhost', 5672, rmq_params.rmq_params["vhost"], credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.exchange_declare(exchange=rmq_params.rmq_params["exchange"], exchange_type='direct', auto_delete=True)

client = MongoClient('localhost', 27017)

db = client['project_3']
collection = db['collection_1']

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

if __name__ == '__main__':
    # Run Flask server
    app = Flask(__name__)

    @app.route("/canvas")
    def canvas():
        is_valid = check_username_password()
        if(is_valid):
            return list_group_files()
        else:
            abort(403)
        return 'Bad'
    
    @app.route("/canvas/download")
    def canvas_dowload():
        is_valid = check_username_password()
        if(is_valid):
            requested_filename = request.args.get('filename', type=str, default='')
            return download(requested_filename)
        else:
            abort(403)
        return 'Bad'
    
    @app.route("/canvas/upload", methods = ['POST'])
    def canvas_upload():
        is_valid = check_username_password()
        if(is_valid):
            requested_filename = request.form.get('filename', type=str, default=None)
            requested_file = request.files['file']
            print(requested_file)
            return upload(requested_filename, requested_file)
        else:
            abort(403)
        return 'Bad'
    
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
        
    app.run(host="0.0.0.0", port=20002, debug=True)
    # END: FLASK
    
    try:
        c_num = 1
        client_num = '_' + str(c_num)
        while True:
            # Declare client queue
            channel.queue_declare(queue='client'+str(client_num), auto_delete=True) #TODO: Change auto_delete to False?
            channel.queue_bind(exchange=rmq_params.rmq_params["exchange"], queue='client'+str(client_num))
        
            c_num += 1
            client_num = '_' + str(c_num)
            
            sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        pass
        

    