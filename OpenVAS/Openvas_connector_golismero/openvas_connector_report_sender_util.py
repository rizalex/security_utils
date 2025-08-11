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
from pysrc.es_ops import EsQuery
import socket
import json
from datetime import datetime
import StringIO

openvas_address = "127.0.0.1"
openvas_manager_port = 9390
openvas_timeout = 9999999
openvas_username = "admin"
openvas_password = "3c555855-46c3-486a-924d-97c0f36ddf37"
openvas_profiles = ["Full and fast"]
ES_VULN_INDEX = 'parsed_scans'
ES_VULN_TYPE = 'client_scans'
ScanStack = ScanStack()


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
def get_scan_results(scan_id, target, user):
    scanner = VulnscanManager(openvas_address, openvas_username, openvas_password, openvas_manager_port,
                              openvas_timeout)
    openvas_results = scanner.get_results(scan_id)
    print('got results')
    data = socket.gethostbyname_ex(target)[2]
    scanned_ip = data[0]
    # scanned_host = ElementTree.SubElement(openvas_results, "host")
    scanned_host = target
    # openvas_scan_id = ElementTree.SubElement(openvas_results, "openvas_scan_id")
    openvas_scan_id = scan_id

    data = {}
    # nothing here yet
    data['user_id'] = user
    # Shouldn't be hardcoded once integrated
    data['scanner'] = 'Openvas'
    data['host'] = target
    data['timestamp']=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = []

    xmlstring = ((ElementTree.tostring(openvas_results, encoding='ISO-8859-1', method='xml')))
    # print(xmlstring)
    for elem in openvas_results.findall('result'):
        # filter by host
        qodElement = int(elem.find('qod')[0].text)
        threatStatus = (elem.find('threat').text)
        #print(threatStatus)
        if qodElement > 79 and threatStatus != "Error":
            print(threatStatus)
            if (str(elem.find('host').text) == scanned_ip or elem.find('host').text.strip('www.') == scanned_host.strip('www.')):
                #print("matched")
                #print("scanned_ip: " + scanned_ip + "|" + "elem.find('host'): " + elem.find('host').text)
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
                    #print (tags)
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
                scan['port'] = port
                scan['cve_id'] = cve
                scan['cvss_base'] = cvss_base
                scan['qod'] = qodElement
                scan['summary'] = summary
                scan['name'] = name
                scan['family'] = family
                scan['affected'] = affected
                scan['solution'] = solution
                scan['port'] = port
                scan['xref'] = xref

                if port is None and cve is None and cvss_base is None and summary is None and name is None and family is None and affected is None and solution is None and port is None and xref is None:
                    print("All none!")
                else:
                    results.append(scan)

    results = list(map(dict,frozenset(frozenset(i.items())for i in results)))
    data['results'] = results

    json_data = json.dumps(data)
    parsed = json.loads(json_data)
    print(json.dumps(parsed, indent=4, sort_keys=True))
    '''
    io = StringIO.StringIO()
    io.write(json.dumps(data))
    buffer = io.getvalue()
    while True:
        try:
            sock.write(buffer)
            break
        except Exception:
            pass
    '''
    esq = EsQuery()
    ES_VULN_INDEX = 'parsed_scans'
    ES_VULN_TYPE = 'client_scans'
    print("storing results to ES index %s" % (ES_VULN_INDEX))
    response = esq.index(ES_VULN_INDEX, ES_VULN_TYPE, parsed)
    if response:
        print(response)
    #   delete_scan_results(scan_id)


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

#get_scan_results("0e989573-cfd5-4fcd-8e12-5baf9d69b743", "www.horangi.com", "lesult")
#get_scan_results("ea0cdcb4-54a3-49c6-8bc6-4ff684383c1a", "www.pandoros.com", "pandoros")
get_scan_results("c2870def-a41e-4be8-b3ad-896c6850ad5e", "www.ajcurbing.com", "samslocker")
get_scan_results("2a693fb5-e5a5-4173-98b5-2a52d1a2f160", "www.208guns.com", "samslocker")
get_scan_results("fb569e2a-cf0c-4899-a217-31a9f65115d7", "www.samslockerboise.com", "samslocker")

'''
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
