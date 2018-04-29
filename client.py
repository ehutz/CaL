#!/usr/bin/python

import rmq_params
import pika
import pickle

# Setup RabbitMQ
credentials = pika.PlainCredentials(rmq_params.rmq_params["username"], rmq_params.rmq_params["password"])
parameters = pika.ConnectionParameters(rmq_host, 5672, rmq_params.rmq_params["vhost"], credentials)
connection = pika.BlockingConnection(parameters)

channel = connection.channel()

print('[Checkpoint] Connected to vhost '
      + '\''
      + rmq_params.rmq_params["vhost"]
      + '\''
      + ' on RMQ server at \''
      + rmq_host
      + '\' as user \''
      + rmq_params.rmq_params["username"]
      + '\'')

def callback(ch, method, properties, body):
    print(body)
    if(body == b'[Checkpoint] Order Update: We finished processing your order.'): # TODO: This needs updated
        exit()

channel.basic_consume(callback,
                      queue="", # TODO: Need to fill something in here
                      no_ack=True)

channel.start_consuming()