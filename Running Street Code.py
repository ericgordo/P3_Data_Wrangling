# -*- coding: utf-8 -*-
"""
File Rant To Complete P3 from Auditing to SQL Database Creation
Created on Thu Sep 29 12:00:53 2016
@author: ericgordo
"""
import open_map_functions as omf
import pprint
import sqlite3
import csv
import re

#Tahoe
file="/Users/ericgordo/Documents/Udacity/P3_data_wrangling/P3/Lake_Tahoe_xml"


lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

"""Auditing of data, Investigation and Printed Results"""

print "Type of Tags"
print omf.count_tags(file)
print "Type of Key Values"
print omf.check_key_characters(file)
print "Users"
print omf.check_users(file)    
print "streets"
streets= omf.audit_streets(file)
pprint.pprint(dict(streets)) 
print "Phone Numbers"
print omf.audit_key(file,'phone')
print len(omf.audit_key(file,'phone'))
print "Cities"
pprint.pprint(omf.audit_key(file, 'addr:city'))
print "States"
print omf.audit_key(file, 'addr:state')
print "City - State Cross-field Audit"
print omf.cross_audit_cities(file)


mapping = { "66.7": "Hwy 50",
            "27.4": "Hwy 80",
            "Blvd": "Boulevard",
            "Ln":"Lane",
            "Rd":"Road",
            "St":"Street",
            }


#RUNNING PROCESS_MAP TAKES LONG TIME
#Only RUN When Done with Auditing
omf.process_map(file, validate=True)


'''
CREATING SQL DATABASE
'''
sqlite_file='lake_tahoe.db'
conn=sqlite3.connect(sqlite_file)
cur=conn.cursor()

'''
NODE TAGS
'''
#Create the nodes_tags table, with coloumn names and data type
cur.execute('''
            CREATE TABLE nodes_tags(id INTEGER,
                                    key TEXT,
                                    value TEXT, 
                                    type TEXT, 
                                    FOREIGN KEY (id) REFERENCES nodes(id))''')           
conn.commit()
#read csv file and directory
with open('nodes_tags.csv','rb') as fin:
    dr=csv.DictReader(fin)
    to_db=[(i['id'].decode("utf-8"),i['key'].decode("utf-8"),i['value'].decode(
                "utf-8"),i['type'].decode("utf-8")) for i in dr]
    
cur.executemany("INSERT INTO nodes_tags(id, key, value,type) VALUES (?, ?, ?, ?);", to_db)
conn.commit()

'''
NODES
'''
#Create the Nodes table, with coloumn names and data type
#cur.execute('''DROP TABLE nodes''')
cur.execute('''
            CREATE TABLE nodes(id INTEGER PRIMARY KEY NOT NULL,
            lat REAL, lon REAL, user TEXT, uid INTEGER, version INTEGER,
            changeset INTEGER, timestamp TEXT)
            ''')
            
conn.commit()
#read csv file and directory
with open('nodes.csv','rb') as fin:
    dr=csv.DictReader(fin)
    to_db=[(i['id'].decode("utf-8"), i['lat'].decode("utf-8"),i['lon'].decode("utf-8"),
            i['user'].decode("utf-8"), i['uid'].decode("utf-8"), i['version'].decode("utf-8"),
            i['changeset'].decode("utf-8"), i['timestamp'].decode("utf-8")) for i in dr]

cur.executemany("INSERT INTO nodes(id, lat, lon, user, uid, version, changeset, timestamp) \
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
                , to_db)
conn.commit()

'''
Ways_Nodes
'''
cur.execute('''
            CREATE TABLE ways_nodes (
            id INTEGER NOT NULL,
            node_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            FOREIGN KEY (id) REFERENCES ways(id),
            FOREIGN KEY (node_id) REFERENCES nodes(id))
            ''')
            
conn.commit()
with open('ways_nodes.csv','rb') as fin:
    dr=csv.DictReader(fin)
    to_db=[(i['id'].decode("utf-8"), i['node_id'].decode("utf-8"),i["position"].decode("utf-8")) for i in dr]

cur.executemany("INSERT INTO ways_nodes(id, node_id, position) VALUES (?, ?, ?);", to_db)
conn.commit()

'''
Ways Tags
'''
cur.execute('''
            CREATE TABLE ways_tags (
            id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            type TEXT,
            FOREIGN KEY (id) REFERENCES ways(id))
            ''')
            
conn.commit()
#read csv file and directory
with open('ways_tags.csv','rb') as fin:
    dr=csv.DictReader(fin)
    to_db=[(i['id'].decode("utf-8"), i['key'].decode("utf-8"),i["value"].decode("utf-8"),
           i["type"].decode("utf-8")) for i in dr]

cur.executemany("INSERT INTO ways_tags(id, key, value, type) VALUES (?, ?, ?,?);", to_db)
conn.commit()

'''
Ways
'''
cur.execute('''
            CREATE TABLE ways (
            id INTEGER PRIMARY KEY NOT NULL,
            user TEXT,
            uid INTEGER,
            version TEXT,
            changeset INTEGER,
            timestamp TEXT)
            ''')
            
conn.commit()
#read csv file and directory
with open('ways.csv','rb') as fin:
    dr=csv.DictReader(fin)
    to_db=[(i['id'].decode("utf-8"), i['user'].decode("utf-8"),i["uid"].decode("utf-8"),
           i["version"].decode("utf-8"), i['changeset'].decode("utf-8"),i['timestamp'].decode("utf-8"))
           for i in dr]

cur.executemany("INSERT INTO ways(id, user, uid, version, changeset,timestamp) \
                VALUES (?, ?, ?, ?, ?, ?);", to_db)
conn.commit()


