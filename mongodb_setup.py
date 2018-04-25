"""
Write code below to setup a MongoDB server to store usernames and passwords for HTTP Basic Authentication.

This MongoDB server should be accessed via localhost on default port with default credentials.

This script will be run before validating you system separately from your server code. It will not actually be used by your system.

This script is important for validation. It will ensure usernames and passwords are stored in the MongoDB server
in a way that your server code expects.
"""

# Run sudo service mongodb restart !!!!!
# follow instructions at https://www.raspberrypi.org/forums/viewtopic.php?t=25173
    # sudo git clone http://people.csail.mit.edu/hubert/git/pyaudio.git
    # sudo apt-get install libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev
    # sudo apt-get install python3-dev
    # sudo python3 pyaudio/setup.py install

from pymongo import MongoClient
import gridfs

client = MongoClient('192.168.1.16', 27017)

db = client['CaL'] # Capture the Lecture database
fs = gridfs.GridFS(db)
a = fs.put(b'test.wav')
print(fs.get(a).read())
user_collection = db['Users'] # Stores usernames (PID) and passwords
session_collection = db['Session'] # Stores unique session ID, .mp3 file per session, Audio Breakpoint ID
audio_collection = db['Audio'] # Stores Timestamp of audio breakpoint and corresponding image
user_session_collection = db['User_Session'] # Stores user requested timestamps corresponding to images per session

for document in user_collection.find():
    db[document['username']].remove()
       
user_collection.remove()

user_collection.insert({'username':'ehutz', 'password':'raspberry'})
user_collection.insert({'username':'m1newc', 'password':'blueberry'})
user_collection.insert({'username':'bliss', 'password':'blackberry'})

for document in user_collection.find():
    db[document['username']]
    print(document['username'])
    
print(user_collection.count())
