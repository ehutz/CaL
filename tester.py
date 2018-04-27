from pymongo import MongoClient
from pprint import pprint
from mongoHelper import ViewUserNames
conn = MongoClient('192.168.1.16', 27017)
user1 = { "username": "mike","password" : "allstar"}
user2 = { "username": "mikey","password" : "whoo"}
##client = conn #MongoClient('mongodb://localhost:27017')
m= conn.CaL
getUsernames(conn)
addUser(conn, "mike", "allstar")
addUser(conn, "mickey", "mouse")
getUsernames(conn)
##db.collection_1.insert({"First_name":"Madelyn", "Last_name":"Newcomb"})
##db.utilization.insert(stats)
##db.utilization.insert(stats2)
#print(db.utilization.count())
#print(m.Users.count())
#cursor = m.Users.find({})
#for c in cursor: pprint(c)