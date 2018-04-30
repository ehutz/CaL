from pymongo import MongoClient
from pprint import pprint

#checks if a username exists and returns the boolean
def userExists(conn, username):
    db = conn.CaL
    if db.Users.find({'username' : username}).count() > 0:
        #print(username)
        return True
    return False

#checks if a username exists and returns the boolean
def sessionExists(conn, session):
    db = conn.CaL
    if db.Session.find({'session' : session}).count() > 0:
        return True
    return False


#adds a user to the list of users. Returns true if successful and
#it is not attempting to overwrite an exxisting user
def addUser(conn, username, password):
    db = conn.CaL
    #print(db.Users.count())
    if userExists(conn, username):
        return False
    db.Users.insert({"username":username, "password":password})
    return True

#adds a session to the list of sessions. Returns true if successful and
#it is not attempting to overwrite an existing session
def addSession(conn, session):
    db = conn.CaL
    if sessionExists(conn, session):
        #print(db.Session.count())
        return False
    db.Session.insert({"session":session, "audio":None})
    #print(db.Session.count())
    return True

#adds audio to an existing session. Returns true if successful.
#it is not attempting to make a new session if the session does not already exist
def addSessionAudio(conn, session, audio):
    db = conn.CaL
    if sessionExists(conn, session):
        return False
    db.Session.update({"session":session, "audio":audio})
    return True

#given a list of usernames, the session, the timestamp, and the (optional) image
#the timestamp is listed in the individual users' tables,
#and the timestamp and image is stored int he session's table
'''
def addTimestamp(conn, usernames, session, timestamp, image):
    db = conn.CaL
    #update the session's table
    sess_collection  = db[session]
    if(image is None):
        sess_collection.insert({'timestamp':timestamp, 'image': None})
    else:
        #inserts the image for the current timestamp
        sess_collection.insert({'timestamp':timestamp, 'image': image})
        #add image to timestamp
    #update user collections
    for username in usernames:
        if userExists(conn, username):
            pid_collection = db[username]
            print('Username' + username)
            if pid_collection.find({'session' : session}).count() > 0:
                print('IF: new collection')
                #update existing list
                curr_stamps = pid_collection.find_one({'session' : session}).timestamps
                curr_stamps = list(set(curr_stamps.append(timestamp)))
                print(",".join(curr_stamps))
                pid_collection.update({'session' : session}, {'timestamps': curr_stamps})
            else:
                print('ELSE: new collection')
                pid_collection.insert({'session' : session, 'timestamps' : [timestamp]})
'''
def addTimestamp(conn, username, session, timestamp, image):
    #print(timestamp)
    db = conn.CaL
    #update the session's table
    sess_collection  = db[session]
    if(image is None):
        sess_collection.insert({'timestamp':timestamp, 'image': None})
    else:
        #inserts the image for the current timestamp
        sess_collection.insert({'timestamp':timestamp, 'image': image})
        #add image to timestamp
    #update user collections
    if userExists(conn, username):
        pid_collection = db[username]
        #print('Username: ' + username)
        if pid_collection.find({'session' : session}).count() > 0:
            #print('IF: new collection')
            #update existing list
            curr_stamps_1 = pid_collection.find_one({'session' : session})
            #pprint(curr_stamps_1)
            curr_stamps = curr_stamps_1['timestamps']
            #print(curr_stamps)
            curr_stamps = curr_stamps + "," + timestamp #list(set(curr_stamps.append(timestamp)))
            #print(curr_stamps)
            #print(",".join(curr_stamps))
            
            pid_collection.update({'session' : session}, {'timestamps' : curr_stamps})
        else:
            #print('ELSE: new collection')
            pid_collection.insert({'session' : session, 'timestamps' : timestamp})
                
#returns the list of usernames
def getUsernames(conn):
    db = conn.CaL
    #print(db.Users.count())
    cursor = db.Users.find({})
    uList = []
    for c in cursor: uList.append(c["username"])
    return uList

#returns the list of sessions and their audio in a list of tuples
def getSessions(conn):
    db = conn.CaL
    #print(db.Sessions.count())
    #cursor = db.Session.find({})
    sList = []
    #for c in cursor:
    for c in db.Session.find():
        if c is not None:
            #sList.append((c.session, c.audio))
            sList.append(c)
    return sList


#returns the image associated with a timestamp.
#If the image does not exist, it will returna  None type
def getTimestampImage(conn, session, timestamp):
    db = conn.CaL
    coll = db[session]
    image = coll.find_one({'timestamp' : timestamp}).image
    return image
