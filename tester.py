from pymongo import MongoClient
from pprint import pprint
from mongoHelper import *
from pathlib import Path
from time import sleep
import subprocess
conn = MongoClient('192.168.1.16', 27017)
user1 = { "username": "mike","password" : "allstar"}
user2 = { "username": "mikey","password" : "whoo"}
##client = conn #MongoClient('mongodb://localhost:27017')
#m= conn.CaL
#getUsernames(conn)
#addUser(conn, "mike", "allstar")
#addUser(conn, "mickey", "mouse")
#getUsernames(conn)
##db.collection_1.insert({"First_name":"Madelyn", "Last_name":"Newcomb"})
##db.utilization.insert(stats)
##db.utilization.insert(stats2)
#print(db.utilization.count())
#print(m.Users.count())
#cursor = m.Users.find({})
db = conn.CaL
user_session_collection = db['ehutz'] # Stores user requested timestamps corresponding to images per session
list_of_sessions = getSessions(conn)

for document in user_session_collection.find({}):
    pprint(document)
'''
session = input("Enter session name: ")
tmstmp = input("Enter timestamp: ")
with open('received/image_'+tmstmp+'.jpg', 'wb') as f:
    f.write(getTimestampImage(conn, session, tmstmp))
    f.close()
   ''' 
printUserInfo(conn, "m1newc")
while True:
            session_name = input("Choose a session:")
            session_time = input("Select a time to seek in the last session:")
            
            
            command = "ffmpeg -i %s -ss %s ./temp.wav" % (session_name+'.wav',
                                                                        session_time)
            myfile = Path("./temp.wav")
            
            process = subprocess.call(['rm', './temp.wav'])
            while process != 0:
                sleep(0.01)
            process = subprocess.Popen(command.split())
            while process.poll() == None:
                sleep(0.1)
            process = subprocess.call(['aplay', './temp.wav'])
            while process != 0:
                sleep(0.01)
            #print(userExists(conn, 'ehutz'))
