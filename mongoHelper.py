from pymongo import MongoClient
from pprint import pprint

#checks if a username exists and returns the boolean
def userExists(conn, username):
    db = conn.CaL
    if db.CaL.find({'username' : username}).count() > 0:
        return True
    return False

#adds a user to the list of users. Returns true if successful and
#it is not attempting to overwrite an exxisting user
def addUser(conn, username, password):
    db = conn.CaL
    print(db.Users.count())
    if userExists(conn, username):
        return False
    db.Users.insert({"username":username, "password":password})
    return True

#given a list of usernames, the session, the timestamp, and the (optional) image
#the timestamp is listed in the individual users' tables,
#and the timestamp and image is stored int he session's table
def addTimestamp(conn, usernames, session, timestamp, image):
    db = conn.CaL
    #update the session's table
    sess_collection  = db[session]
    if(image == None)
        sess_collection.insert({'timestamp':timestamp, 'image', None})
    else
        #inserts the image for the current timestamp
        sess_collection.insert({'timestamp':timestamp, 'image', image})
        #add image to timestamp
    #update user collections
    for username in usernames
        if userExists(conn, username):
            pid_collection = db[username]
            if pid_collection.find({'session' : session}).count() > 0:
                #update existing list
                curr_stamps = pid_collection.find_one({'session' : session}).timestamps
                curr_stamps = list(set(curr_stamps.append(timestamp)))
                print(",".join(curr_stamps))
                pid_collection.update({'session' : session}, {'timestamps', curr_stamps})
            else:
                pid_collection.insert({'session' : session, 'timestamps' : [timestamp]})

#returns the list of usernames
def getUsernames(conn):
    db = conn.CaL
    #print(db.Users.count())
    cursor = db.Users.find({})
    uList = []
    for c in cursor: uList.append(c.username)
    return uList

#returns the list of sessions
def getSessions(conn):
    db = conn.CaL
    #print(db.Sessions.count())
    cursor = db.Session.find({})
    sList = []
    for c in cursor: sList.append(c.username)
    return sList

#returns the image associated with a timestamp.
#If the image does not exist, it will returna  None type
def getTimestampImage(conn, session, timestamp):
    db = conn.CaL
    coll = db[session]
    image = coll.find_one({'timestamp' : timestamp}).image
    return image
