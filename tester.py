from pymongo import MongoClient
from pprint import pprint
from mongoHelper import ViewUserNames
conn = MongoClient('192.168.1.16', 27017)
stats = { "road": 2,"man" : 1}
stats2 = { "road": 3,"man" : 2}
##client = conn #MongoClient('mongodb://localhost:27017')
m= conn.CaL
ViewUserNames(conn)
##db.collection_1.insert({"First_name":"Madelyn", "Last_name":"Newcomb"})
##db.utilization.insert(stats)
##db.utilization.insert(stats2)
#print(db.utilization.count())
#print(m.Users.count())
#cursor = m.Users.find({})
#for c in cursor: pprint(c)