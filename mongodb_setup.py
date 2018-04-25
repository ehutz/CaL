"""
Write code below to setup a MongoDB server to store usernames and passwords for HTTP Basic Authentication.

This MongoDB server should be accessed via localhost on default port with default credentials.

This script will be run before validating you system separately from your server code. It will not actually be used by your system.

This script is important for validation. It will ensure usernames and passwords are stored in the MongoDB server
in a way that your server code expects.

Make sure there are at least 3 usernames and passwords.

Make sure an additional username and password is stored where...
	username = admin
	password = pass
"""

from pymongo import MongoClient 

client = MongoClient('localhost', 27017)

db = client['project_3']
collection = db['collection_1']

collection.remove()

collection.insert({'username':'admin', 'password':'pass'})
collection.insert({'username':'mad', 'password':'elyn'})
collection.insert({'username':'liz', 'password':'hutz'})
collection.insert({'username':'jor', 'password':'dan'})
