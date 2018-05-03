from pathlib import Path
from flask import Flask, send_file, request, abort
from time import sleep, mktime
import requests
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
setStatus(conn, session, 'IN PROGRESS')
#pprint(getSessions(conn))
#pprint(getUsernames(conn))
'''
def check_username_password():
    if request.authorization == None:
        return True
    username = request.authorization.username
    password = request.authorization.password
    if collection.find({'username': username, 'password':password}).count() > 0:
        return True
    return False

'''		
def callback_client(ch, method, properties, body):
    bod = pickle.loads(body)
    #pprint(pickle.loads(body))
    
    addTimestamp(conn, bod['username'], session, str(bod['message'] - server_start_time), None)
    
    #exit() # Used to terminate server
        
def callback_pixycam(ch, method, properties, body):
    bod = pickle.loads(body)
    #pprint(pickle.loads(body))
    
    addTimestamp(conn, bod['username'], session, str(float(bod['message']) - float(server_start_time)), bod['image'])
    
    #exit() # Used to terminate server
        
if __name__ == '__main__':
    try:
        while True:
            # Tell audio to start recording
            print('[Checkpoint] GET request to audio.py to record sent')
            r = requests.get('http://0.0.0.0:20000/audio/record?filename='
                             + session
                             + '&session='
                             + session
                             + '&record_time_sec='
                             + str(audio_record_time_seconds))
            
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
        

    
