from pymongo import MongoClient
from pprint import pprint
#conn = MongoClient('192.168.1.16', 27017)
stats = { "road": 2,"man" : 1}
stats2 = { "road": 3,"man" : 2}
#client = conn #MongoClient('mongodb://localhost:27017')
def ViewUserNames(conn):
    db = conn.CaL
    print(db.Users.count())
    cursor = db.Users.find({})
    for c in cursor: pprint(c)#This script contains functions to access the mongodb database

def addUser(conn, username, password):
    db = conn.CaL
    print(db.Users.count())
    if userExists(conn, username):
        return False
    db.Users.insert({"username":username, "password":password})
    return True


def addUser(conn, username, password):
    db = conn.CaL
    if userExists(conn, username):
        return False
    db.Users.insert({"username":username, "password":password})
    return True


def addTimestamp(conn, username, session, timestamp):
    db = conn.CaL
    if userExists(conn, username):
        return False
    pid_collection = db[username]
    if pid_collection.find({'session' : session}).count() > 0:
        #update existing list
        print("updating session")
        curr_stamps = pid_collection.find_one({'session' : session}).timestamps
        curr_stamps.append(timestamp)
        print(",".join(curr_stamps))
        pid_collection.update({'session' : session}, {'timestamps', curr_stamps})
    else:
        pid_collection.insert({'session' : session, 'timestamps' : [timestamp]})
    return True


def userExists(conn, username):
    db = conn.CaL
    if db.CaL.find({'username' : username}).count() > 0:
        return True
    return False
#db.collection_1.insert({"First_name":"Madelyn", "Last_name":"Newcomb"})
#db.utilization.insert(stats)
#db.utilization.insert(stats2)
#print(db.utilization.count())
