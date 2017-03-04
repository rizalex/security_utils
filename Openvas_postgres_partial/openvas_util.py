from __future__ import print_function
from threading import Semaphore
import threading
from functools import partial
from openvas_lib import report_parser
from openvas_lib import VulnscanManager, VulnscanException
from scan_stack import ScanStack
import time
# pip install openvas_lib
import xml.etree.ElementTree as ElementTree
from xmljson import parker
from xml.etree.ElementTree import fromstring
from json import dumps
#from pysrc.es_ops import EsQuery
import socket
import json
from datetime import datetime
import StringIO

import json
import sqlalchemy
from apps import app
from apps.users.models import User, Website, ScanResult, Severity
from config import config
from pprint import pprint

openvas_address = "139.59.58.50"
openvas_manager_port = 9390
openvas_timeout = 9999999
openvas_username = "admin"
openvas_password = "MeatsAndMor3!"
openvas_profiles = ["Full and fast"]
ES_VULN_INDEX = 'parsed_scans'
ES_VULN_TYPE = 'client_scans'
ScanStack = ScanStack()


# return Severity from param score
def score_severity(score):
    if score == None:
        score = 0
    score = float(score)
    if score == 0:  # informational
        return Severity.informational
    elif 0.1 <= score <= 3.9:  # low
        return Severity.low
    elif 4.0 <= score <= 6.9:  # medium
        return Severity.medium
    elif 7.0 <= score <= 8.9:  # high
        return Severity.high
    else:  # critical!!!
        return Severity.critical


# callback method for launch_callback_scanner()
def my_print_status(i):
    print(str(i))


# Do not call this directly for large scans
def launch_normal_scanner(target, profile):
    scanner = VulnscanManager(openvas_address, openvas_username, openvas_password, openvas_manager_port,
                              openvas_timeout)
    scan_id, target_id = scanner.launch_scan(target=target,  # Target to scan
                                             profile=profile)

    print("launched: scan id = " + scan_id + "target id= " + target_id)


# UNTESTED YET
# GETS RESULTS AND PUSHES TO DB
def get_scan_results(scan_id, target, user_id):
    data = socket.gethostbyname_ex(target)[2]
    scanned_ip = data[0]
    scanned_host = target

    """
    #Activate for actual process
    scanner = VulnscanManager(openvas_address, openvas_username, openvas_password, openvas_manager_port,
                              openvas_timeout)
    openvas_results = scanner.get_results(scan_id)
    print('got results')
    # scanned_host = ElementTree.SubElement(openvas_results, "host")x
    # openvas_scan_id = ElementTree.SubElement(openvas_results, "openvas_scan_id")
    openvas_scan_id = scan_id

    xmlstring = ((ElementTree.tostring(openvas_results, encoding='ISO-8859-1', method='xml')))
    print(xmlstring)

    file = open("test.xml", "w")
    file.write(xmlstring)
    file.close()

    """
    #Use this for testing, faster
    openvas_results = ElementTree.parse('test.xml')
    print("read from flat file")
    #

    for elem in openvas_results.findall('result'):

        # filter by host
        qodElement = int(elem.find('qod')[0].text)
        threatStatus = (elem.find('threat').text)
        if qodElement > 79 and threatStatus != "Error":
            print("scanned_ip: " + scanned_ip + "|" + "elem.find('host'): " + elem.find('host').text)
            if (str(elem.find('host').text) == scanned_ip or elem.find('host').text.strip('www.') == scanned_host.strip('www.')):
                print("matched")
                print("scanned_ip: " + scanned_ip + "|" + "elem.find('host'): " + elem.find('host').text)
                scan = {}
                port = elem.find('port').text
                nvt = elem.find('nvt')
                cve = nvt.find('cve').text
                cvss_base = nvt.find('cvss_base').text
                name = nvt.find('name').text
                family = nvt.find('family').text
                xref = nvt.find('xref').text
                summary = None
                cvss_base_vector = None
                affected = None

                solution = None
                if nvt.find('tags') is not None:
                    tags = nvt.find('tags').text
                    # print (tags)
                    tagArray = (tags).split('|')
                    for tag in tagArray:
                        tagKey = tag.split('=')[0]
                        if tagKey == 'summary':
                            summary = tag.split('=')[1]
                        elif tagKey == 'cvss_base_vector':
                            cvss_base_vector = tag.split('=')[1]
                        elif tagKey == 'affected':
                            affected = tag.split('=')[1]
                        elif tagKey == 'solution':
                            solution = tag.split('=')[1]

                if cve=="NOCVE":
                    description = str(name)+"|"+str(summary)+"|"+str(solution)
                else:
                    description="|"
                '''
                scan['port'] = port
                scan['cve_id'] = cve
                scan['cvss_base'] = cvss_base
                scan['qod'] = qodElement
                scan['summary'] = summary
                scan['name'] = name
                scan['family'] = family
                scan['affected'] = affected
                scan['solution'] = solution
                scan['xref'] = xref
                '''
                if port is None and cve is None and cvss_base is None and summary is None and name is None and family is None and affected is None and solution is None and port is None and xref is None:
                    print("All none!")
                else:
                    print("creating")
                    psql_create(user_id, target, cve, port, cvss_base, description, family)
    '''
    if response:
        print(response)
        #   delete_scan_results(scan_id)
    '''

def psql_create(user_id, host, cve_id, port_string, cvss_base, description, family):
    user, host = None, None
    try:  # scans for market does not have user and website on the other tables
        user = User.query.filter(User.first_name == user_id).one()
        host = Website.query.filter(Website.hostname == host).one()
    except sqlalchemy.orm.exc.NoResultFound as e:
        pass
    scan_data = {
        'vuln_id': cve_id,
        'scan_id': 0,  # we don't need
        'manual': False
    }
    if user and host:
        scan_data['user_id'] = user.id
        scan_data['website_id'] = host.id
    port, protocol_type = port_string.split('/')
    try:
        port = int(port)
        scan_data['port'] = port  # do not store for those with no port (like "general")
    except ValueError as e:
        print("Errored: " + str(e))
        pass

    scan_data['description'] = description
    scan_data['family'] = family
    scan_data['port_type'] = protocol_type

    score = cvss_base
    severity = score_severity(score)
    scan_data['severity'] = severity
    ScanResult.create(commit=True, **scan_data)
    print
    "created"
    pprint(scan_data)


def delete_scan_results(scan_id):
    scanner = VulnscanManager(openvas_address, openvas_username, openvas_password, openvas_manager_port,
                              openvas_timeout)
    scanner.delete_scan(scan_id)


def delete_target_results(target_id):
    scanner = VulnscanManager(openvas_address, openvas_username, openvas_password, openvas_manager_port,
                              openvas_timeout)
    scanner.delete_target(target_id)


# need to add profile
def launch_stack_scanner(target, profile, scan_stack):
    sem = Semaphore(0)
    # Configure
    manager = VulnscanManager(openvas_address, openvas_username, openvas_password, openvas_manager_port,
                              openvas_timeout)
    # Launch
    print("Target " + target)

    scan_id, target_id = manager.launch_scan(target.split('|')[1],
                                             profile=profile,
                                             callback_end=partial(lambda x: x.release(), sem),
                                             callback_progress=my_print_status)
    # Wait
    sem.acquire()
    ScanStack.scan_queue.remove(scan_stack)
    # Finished scan
    print("finished: scan id = " + scan_id + "target id= " + target_id)
    get_scan_results(scan_id, target.split('|')[1], target.split('|')[0])


## ONLY USE THIS OR FACE EPIC LAGS
def add_to_queue(target, profile):
    ScanStack.wait_queue.append(target + "," + profile)
    # print(str(ScanStack.wait_queue))


## ONLY USE THIS TO REMOVE SCANS FROM QUEUE. USE THE TOP METHOD TO REMOVE SCANNED ITEMS. NO WAY TO CANCEL SCAN IN PROGRESS YET
def remove_from_queue(target, profile):
    ScanStack.wait_queue.remove(target + "," + profile)
    # print(str(ScanStack.wait_queue))

'''
#For batch scanning
with open('./input/websiteslist.txt') as f:
    lines = f.read().splitlines()
    for line in lines:
        add_to_queue(line, "Full and fast")

##60 Seconds Loop~! This is the main method
ScanStack.max_scan_queue = 3
while True:
    if (len(ScanStack.wait_queue) != 0) and (len(ScanStack.scan_queue) < ScanStack.max_scan_queue):
        ScanStack.scan_queue.append(ScanStack.wait_queue[0])
        targetArray = ScanStack.wait_queue[0].split(",")
        target = targetArray[0]
        profile = targetArray[1]

        t = threading.Thread(target=launch_stack_scanner, args=(target, profile, ScanStack.wait_queue[0],))
        del ScanStack.wait_queue[0]
        t.daemon = True
        t.start()

        # launch_stack_scanner(target,profile,ScanStack.scan_queue[0])
        print("launched from stack!")

    elif len(ScanStack.scan_queue) >= ScanStack.max_scan_queue or (
                    len(ScanStack.wait_queue) == 0 and len(ScanStack.scan_queue) == 0):
        time.sleep(60)

    else:  # nothing to do here, catchall
        time.sleep(60)
    print("ended")
'''
'''
#for direct scanning
launch_stack_scanner(target, profile, scan_stack)
'''

if __name__ == '__main__':
    with app.app_context():
        get_scan_results("7c613d61-9f55-4134-be37-2a4d1324f73a", 'www.moo.com', '4')


