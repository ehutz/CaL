from pymongo import MongoClient
from pprint import pprint
from mongoHelper import *
conn = MongoClient('localhost', 27017)
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

for document in user_session_collection.find({}):
    pprint(document)
    
print(userExists(conn, 'ehutz'))
