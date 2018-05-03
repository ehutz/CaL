# The same copy of this file should be used by 
# server.py, led.py, processor.py and client.py.
# Each use this to establish a connection with the RabbitMQ Server.
# DO NOT change the key names in this dictionary.
# Feel free to change the values.
#
# Example:
# rmq_params = {"vhost": "vcoolhost", 
# "username": "bryan", 
# "password": "imahokie123", 
# "exchange": "sysexchange", 
# "order_queue": "orders",
# "led_queue": "ledstatus"}

rmq_params = {"vhost": "team4_vhost", 
"username": "admin", 
"password": "VT_Prof", 
"exchange": "team4_ex",
"client_queue": "client_q",
"pixycam_queue": "pixycam_q"}
