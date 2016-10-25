# -*- coding: utf-8 -*-
"""
All Functions Created Throughout the Lesson and Functions Called Upon
For P3 on Udacity's Data Wrangling Course
Created on Thu Sep 29 12:00:53 2016
@author: ericgordo
"""
#All Imports
from collections import defaultdict
import xml.etree.ElementTree as ET
import re
import csv
import codecs
import cerberus
import schema  #Seperate Python File

'''
Quiz 1 count_tags function ____________________________________________________
'''
def count_tags(filename):
    tags_dict={}
    for event, element in ET.iterparse(filename, events=("start",)):
        element_tag=element.tag
        if element_tag not in tags_dict:
            tags_dict[element_tag]=1
        else:
            tags_dict[element_tag]+=1
    return tags_dict

'''
Quiz 2 Tag Types ______________________________________________________________
'''
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

def key_type(element, keys):
    if element.tag == "tag":
        k=element.attrib["k"]
        if re.search(lower, k):
            keys["lower"]+=1
        elif re.search(lower_colon, k):
            keys["lower_colon"]+=1
        elif re.search(problemchars, k):
            keys["problemchars"]+=1
            print "Problem: " + k
        else:
            keys["other"]+=1
    return keys

#process_map function name changed to check_key_characters
def check_key_characters(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)
    return keys

'''
Quiz 3 Exploring Users ________________________________________________________
'''
def get_user(element):
    uid=""
    if element.tag == 'node':
        uid=element.attrib["uid"]
    if element.tag == 'way':
        uid=element.attrib["uid"]
    if element.tag == 'relation':
        uid=element.attrib["uid"]
    return uid

#process_map name changed to check_users
def check_users(filename):
    users = set()
    for _, element in ET.iterparse(filename):
        if get_user(element):
            users.add(get_user(element))
    return users

'''
Quiz 4 Improving Street Names _________________________________________________
'''

street_type_re = re.compile(r'\S+\.?$', re.IGNORECASE)

# UPDATE THESE VARIABLES
mapping = { "66.7": "Hwy 50",
            "27.4": "Hwy 80",
            "Blvd": "Boulevard",
            "Ln":"Lane",
            "Rd":"Road",
            "St":"Street",
            }
expected = []

def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def audit_streets(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types


def update_name(name, mapping):
    better_name=name
    m=street_type_re.search(name)
    if m:
        if m.group() in mapping.keys():
            better_street_type = mapping[m.group()]
            better_name = street_type_re.sub(better_street_type, name)
    return better_name


phone_start= re.compile('^\s*?\+?1\-?\s?')
def is_phone(elem):
    """Takes an element and returns true if element is tagged as a phone number"""
    return (elem.attrib['k'] == 'phone') or (elem.attrib['k'] == 'contact:phone')

def update_number(number):
    """If a phone number matchers defined regular expression, phone number is striped of starting +1 code"""
    better_number=number
    if re.search(phone_start,number):
            better_number = re.sub(phone_start,'',number)
    return better_number

def is_state(elem):
    """Takes an element and returns true if element is tagged as a state name"""
    return (elem.attrib['k'] == 'addr:state')

def update_state(state):
    "Updates State Names to only be Nevada or California"""
    new_state=state
    state_mapping={"CA":"California", "NV":"Nevada", "California":"California", "Nevada":"Nevada"}
    if state in state_mapping.keys():
        new_state=state_mapping[state]
    return new_state
'''
Quiz 5 Preparing for Database _________________________________________________
'''
NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

#these variables already defined above
LOWER_COLON = lower_colon
PROBLEMCHARS = problemchars
SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']



def order_tags(child,element):
    tags={}
    if re.search(PROBLEMCHARS, child.attrib['k']):
        tags={}
    if re.search(LOWER_COLON, child.attrib['k']):
        tags['id']=element.attrib['id']
        tags['value']=child.attrib['v']
        tags['key']=child.attrib['k'].split(":",1)[1]
        tags['type']=child.attrib['k'].split(":",1)[0]
    else:
        tags['id']=element.attrib['id']
        tags['value']=child.attrib['v']
        tags['key']=child.attrib['k']
        tags['type']="regular"
    return tags

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    if element.tag == 'node':
        for child in element:
            if is_street_name(child):
                child.attrib['v']=update_name(child.attrib['v'],mapping)
            if is_phone(child):
                child.attrib['v']=update_number(child.attrib['v'])
            if is_state(child):
                child.attrib['v']=update_state(child.attrib['v'])
            node_tags=order_tags(child, element)
            tags.append(node_tags)
        node_attribs=node_attribs.fromkeys(node_attr_fields)
        for field in node_attr_fields:
            node_attribs[field]=element.attrib[field]
        return{'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        for i,child in enumerate(element):
            if child.tag=='nd':
                way_node={}
                way_node['id']=element.attrib['id']
                way_node['node_id']=child.attrib['ref']
                way_node['position']=i
                way_nodes.append(way_node)
            if child.tag=='tag':
                if is_phone(child):
                    child.attrib['v']=update_number(child.attrib['v'])
                if is_street_name(child):
                    child.attrib['v']=update_name(child.attrib['v'],mapping)
                if is_state(child):
                    child.attrib['v']=update_state(child.attrib['v'])
                way_tags=order_tags(child, element)
                tags.append(way_tags)
        way_attribs=way_attribs.fromkeys(way_attr_fields)
        for field in way_attr_fields:
            way_attribs[field]=element.attrib[field]
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""
    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_strings = (
            "{0}: {1}".format(k, v if isinstance(v, str) else ", ".join(v))
            for k, v in errors.iteritems()
        )
        raise cerberus.ValidationError(
            message_string.format(field, "\n".join(error_strings))
        )

class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])

'''
Other Auditing Functions Used _______________________________________________________________
'''
def cross_audit_cities(file):
    """Takes Lake Tahoe OSM File and returns Dictionary with all cities tagged in each corresponding state"""
    osm_file = open(file, "r")
    dic={}
    California=set()
    Nevada=set()
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        state_name= None
        city_name= None
        for tag in elem.iter("tag"):
            if tag.attrib['k'] == "addr:state":
                state_name=update_state(tag.attrib['v'])
            if tag.attrib['k'] == "addr:city":
                city_name=tag.attrib['v']
        if state_name!= None and city_name != None:
            if state_name == 'California':
                California.add(city_name)
            if state_name == 'Nevada':
                Nevada.add(city_name)
    dic["California"]=California
    dic["Nevada"]=Nevada
    osm_file.close()
    return dic


def get_all_keys(file):
    """Searches through an OSM file and returns all 'key' values"""
    keys=set()
    for _, element in ET.iterparse(file):
        if get_key(element) not in keys:
            keys.add(get_key(element))
    return keys

def get_key(element):
    if element.tag == "tag":
        return element.attrib["k"]

def audit_key(file, key):
    """Goes through a file and finds all tag values associated with a particular key"""
    osm_file = open(file, "r")
    dic = set()
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        for tag in elem.iter("tag"):
            if tag.attrib['k'] == key:
                dic.add(tag.attrib['v'])
    osm_file.close()
    return dic

def print_sorted_dict(d):
    keys = d.keys()
    keys = sorted(keys, key=lambda s: s.lower())
    for k in keys:
        v = d[k]
        print "%s: %d" % (k, v)
