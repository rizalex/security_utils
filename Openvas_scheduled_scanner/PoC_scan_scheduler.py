from __future__ import print_function
import sys
from time import sleep
from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.scheduler import Scheduler
# pip install apscheduler==2.1.2
from threading import Semaphore
import threading
from functools import partial
from openvas_lib import report_parser
from openvas_lib import VulnscanManager, VulnscanException
from schedule_stack import ScheduleStack
import time
# pip install openvas_lib
import xml.etree.ElementTree as ElementTree
from xmljson import parker
from xml.etree.ElementTree import fromstring
import json
from json import dumps
from pysrc.es_ops import EsQuery
from schedule import Schedule
from datetime import datetime, date, time, timedelta
import logging
import socket

logging.basicConfig()

ScheduleStack = ScheduleStack()
sched = BackgroundScheduler()
sched.start()  # start the scheduler

openvas_address = "127.0.0.1"
openvas_manager_port = 9390
openvas_timeout = 9999999
openvas_username = "admin"
openvas_password = "3c555855-46c3-486a-924d-97c0f36ddf37"
openvas_profiles = ["Full and fast"]
schedule_status = ["Pending", "In Queue", "Scanning", "Scanned"]

schedule_frequency = 5  # min
INDEX_NAME = "schedule_list"
TYPE_NAME = "schedules"
scan_stack_max_queue = 3


# returns scans to start within the next 'schedule_frequency' minutes
def get_schedule_soon():
    # 2016-01-23T00:00
    esq = EsQuery()

    dt_start = datetime.now()
    dt_end = dt_start + timedelta(minutes=schedule_frequency)
    dt_end = dt_end.strftime("%Y-%m-%d %H:%M:%S")
    dt_start = dt_start.strftime("%Y-%m-%d %H:%M:%S")
    # print(dt_start)
    # print(dt_end)
    # 2017-02-05 04:44:56
    # 2017-02-05 04:54:56


    queryReq = {
        "query": {
            "range": {
                "scan_request_start_datetime": {
                    "gt": dt_start,
                    "lt": dt_end
                }
            }

        }
    }

    res = esq.queryEs(INDEX_NAME, queryReq)
    # print("HERE")
    # print (str(res))
    output = res["hits"]["hits"]
    # print("THERE " +str(output))
    jsonArray = []
    applicableScans = []
    for x in output:
        #   print("Inside")
        keyList = x.keys()
        data = {}
        values = x.values()[3]
        # print("Value : %s" % str(values))
        data['_id'] = x.values()[2]
        data['status'] = values['status']
        data['scan_id'] = values['scan_id']
        data['target'] = values['target']
        data['scan_request_start_datetime'] = values['scan_request_start_datetime']
        data['create_datetime'] = values['create_datetime']
        data['requested_by'] = values['requested_by']
        data['scan_end_datetime'] = values['scan_end_datetime']
        data['scanner'] = values['scanner']
        data['scan_start_datetime'] = values['scan_start_datetime']
        # print("data ")

        applicableScans.append(data)
    # if not applicableScans:
    jsonArray = json.dumps(applicableScans)
    # print ("JSONARRAY" + str(jsonArray))
    return jsonArray


def get_schedule_by_es_id(id):
    esproc = EsQuery()
    resData = esproc.match_query(INDEX_NAME, {'_id': id}, 1)
    return resData


# def update_schedule(data, idVal):
#    esq = EsQuery()
#    return esq.update(INDEX_NAME, TYPE_NAME, idVal, data)

# Called when json is sent to scan server
def update_schedule(es_id, status=None, scan_id=None, target=None, scan_request_start_datetime=None,
                    scan_end_datetime=None, scanner=None, scan_start_datetime=None):
    es_json = get_schedule_by_es_id(es_id)[0]
    if (status is None):
        status = es_json['status']
    if (scan_id is None):
        scan_id = es_json['scan_id']
    if (target is None):
        target = es_json['target']
    if (scan_request_start_datetime is None):
        scan_request_start_datetime = es_json['scan_request_start_datetime']
    if (scan_end_datetime is None):
        scan_end_datetime = es_json['scan_end_datetime']
    if (scanner is None):
        scanner = es_json['scanner']
    if (scan_start_datetime is None):
        scan_start_datetime = es_json['scan_start_datetime']

    data = {'requested_by': es_json['requested_by'], 'target': target, 'scanner': scanner, 'status': status,
            'scan_id': scan_id, 'scan_request_start_datetime': scan_request_start_datetime,
            'scan_start_datetime': scan_start_datetime, 'scan_end_datetime': scan_end_datetime,
            'create_datetime': es_json['create_datetime']}
    esq = EsQuery()
    return esq.update(INDEX_NAME, TYPE_NAME, es_id, data)


def add_to_aps_scheduler(data):
    if data['status'] == schedule_status[0]:
        # job = sched.add_date_job(add_to_queue, data['scan_request_start_datetime'], [data])
        ##UPGRADE TO LATEST SCHEDULER
        job = sched.add_job(add_to_queue, 'date', data['scan_request_start_datetime'], args=[data])
    update_schedule(data['_id'], schedule_status[1], data['scan_id'], data['target'],
                    data['scan_request_start_datetime'], data['scan_end_datetime'], data['scanner'],
                    data['scan_start_datetime'])


## ONLY USE THIS OR FACE EPIC LAGS
# add to queue and trigger scan avalaibility check
def add_to_queue(data):
    ScheduleStack.wait_queue.append(data)
    if (len(ScheduleStack.wait_queue) != 0) and (len(ScheduleStack.scan_queue) < ScheduleStack.max_scan_queue):
        ScheduleStack.scan_queue.append(ScheduleStack.wait_queue[0])
        es_id = ScheduleStack.wait_queue[0]['_id']
        target = ScheduleStack.wait_queue[0]['target']
        profile = 'Full and fast'
        t = threading.Thread(target=launch_stack_scanner, args=(target, profile, ScheduleStack.scan_queue[0],))
        update_data = ScheduleStack.wait_queue[0]
        del ScheduleStack.wait_queue[0]
        t.daemon = True
        t.start()
        update_schedule(data['_id'], schedule_status[2], None, None,
                        None, None, None,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        # launch_stack_scanner(target,profile,ScanStack.scan_queue[0])
        print("launched from stack immediately!")
        # print(str(ScanStack.wait_queue))


## ONLY USE THIS TO REMOVE SCANS FROM QUEUE. USE THE TOP METHOD TO REMOVE SCANNED ITEMS. NO WAY TO CANCEL SCAN IN PROGRESS YET
def remove_from_queue(data):
    ScheduleStack.wait_queue.remove(data)


'''
OPENVAS SCAN METHODS START HERE
'''


# 1
def stack_iterate_and_loop():
    ##60 Seconds Loop~! This is the main method
    ScheduleStack.max_scan_queue = scan_stack_max_queue

    while True:
        print('time now: ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        upcomingScans = json.loads(get_schedule_soon())
        if len(upcomingScans) != 0:
            for scan in upcomingScans:
                if scan['status'] == schedule_status[0]:
                    # If status is pending
                    print("upcoming found")
                    add_to_aps_scheduler(scan)
        if (len(ScheduleStack.wait_queue) != 0) and (len(ScheduleStack.scan_queue) < ScheduleStack.max_scan_queue):
            print("starting immediate check true")
            ScheduleStack.scan_queue.append(ScheduleStack.wait_queue[0])
            es_id = ScheduleStack.wait_queue[0]['_id']
            target = ScheduleStack.wait_queue[0]['target']
            profile = 'Full and fast'
            t = threading.Thread(target=launch_stack_scanner, args=(target, profile, ScheduleStack.scan_queue[0],))
            update_data = ScheduleStack.wait_queue[0]
            del ScheduleStack.wait_queue[0]
            t.daemon = True
            t.start()
            update_schedule(es_id, schedule_status[2], None, None,
                            None, None, None,
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            # launch_stack_scanner(target,profile,ScanStack.scan_queue[0])
            print("launched from stack!")

        elif len(ScheduleStack.scan_queue) >= ScheduleStack.max_scan_queue or (
                len(ScheduleStack.wait_queue) == 0 and len(ScheduleStack.scan_queue) == 0) or (
                len(ScheduleStack.scan_queue) <= ScheduleStack.max_scan_queue and len(ScheduleStack.wait_queue) == 0):
            sleep(60)
            print("Sleeping for 60")
        else:
            sleep(30)
            print("Sleeping for 30")


# need to add profile
def launch_stack_scanner(target, profile, scan_stack):
    sem = Semaphore(0)
    # Configure
    manager = VulnscanManager(openvas_address, openvas_username, openvas_password, openvas_manager_port,
                              openvas_timeout)
    # Launch
    scan_id, target_id = manager.launch_scan(target,
                                             profile=profile,
                                             callback_end=partial(lambda x: x.release(), sem),
                                             callback_progress=my_print_status)
    # Wait
    sem.acquire()
    ScheduleStack.scan_queue.remove(scan_stack)
    # Finished scan
    update_schedule(scan_stack['_id'], schedule_status[3], scan_id, target,
                    None, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), None, None
                    )
    # (es_id, status=None, scan_id=None, target=None, scan_request_start_datetime=None, scan_end_datetime=None, scanner=None, scan_start_datetime=None):
    print("es id: " + scan_stack['_id'])
    print("finished: scan id = " + scan_id + " target id= " + target_id)
    get_scan_results(scan_id, target)


# for calling 1 scan
def launch_callback_scanner(target, profile):
    sem = Semaphore(0)
    # Configure
    manager = VulnscanManager(openvas_address, openvas_username, openvas_password, openvas_manager_port,
                              openvas_timeout)

    # Launch
    scan_id, target_id = manager.launch_scan(target,
                                             profile=profile,
                                             callback_end=partial(lambda x: x.release(), sem),
                                             callback_progress=my_print_status)
    # Wait
    sem.acquire()
    # Finished scan
    print("finished: scan id = " + scan_id + "target id= " + target_id)
    return "done!"


# callback method for launch_callback_scanner()
def my_print_status(i):
    print(str(i))


# GETS RESULTS AND PUSHES TO DB
def get_scan_results(scan_id, target):
    scanner = VulnscanManager(openvas_address, openvas_username, openvas_password, openvas_manager_port,
                              openvas_timeout)
    openvas_results = scanner.get_results(scan_id)
    # filters value is unstable

    #filter by host

    data = socket.gethostbyname_ex(target)
    scanned_ip = repr(data)

    #scanned_host = ElementTree.SubElement(openvas_results, "host")
    scanned_host = target
    #openvas_scan_id = ElementTree.SubElement(openvas_results, "openvas_scan_id")
    openvas_scan_id = scan_id

    data = {}
    # nothing here yet
    data['user_id'] = None
    # Shouldn't be hardcoded once integrated
    data['scannersUsed'] = 'Openvas'
    data['sitesScanned'] = 'Openvas'
    data['sitesScanned'] = target
    results = []

    xmlstring = ((ElementTree.tostring(openvas_results, encoding='ISO-8859-1', method='xml')))
    #print(xmlstring)
    for elem in openvas_results.findall('result'):

        #filter by host

        if elem.find('host').text == scanned_ip or elem.find('host').text.strip('www.') == scanned_host.strip('www.'):

            scan={}
            scan['hostname'] = elem.find('host').text
            port = elem.find('port').text
            nvt=elem.find('nvt')
            cve = nvt.find('cve').text
            cvss_base = nvt.find('cvss_base').text
            name = nvt.find('name').text
            family = nvt.find('family').text
            xref = nvt.find('xref').text


            summary = None
            cvss_base_vector = None
            affected = None
            solution = None


            if elem.find('tags') is not None:

                tags = elem.find('tags').text
                tagArray = (ElementTree.tostring(tags, encoding='ISO-8859-1', method='xml')).split('|')
                for tag in tagArray:
                    tagKey = tag.split('|')[0]
                    if tagKey=='summary':
                        summary = tag.split('|')[1]
                    elif tagKey=='cvss_base_vector':
                        cvss_base_vector = tag.split('|')[1]
                    elif tagKey == 'affected':
                        affected = tag.split('|')[1]
                    elif tagKey == 'solution':
                        solution = tag.split('|')[1]


            scan['port'] = port
            scan['cve_id'] = cve
            scan['cvss_base'] = cvss_base
            scan['summary'] = summary
            scan['name'] = name
            scan['family'] = family
            scan['affected'] = affected
            scan['solution'] = solution
            scan['port'] = port
            scan['xref'] = xref

            results.append(scan)

    data['scans'] = results
    json_data = json.dumps(data)
    parsed = json.loads(json_data)
    print (json.dumps(parsed, indent=4, sort_keys=True))
'''
    esq = EsQuery()
    ES_VULN_INDEX = 'es_scan_data'
    ES_VULN_TYPE = 'vuln'
    print("storing results to ES index %s" % (ES_VULN_INDEX))
    response = esq.index(ES_VULN_INDEX, ES_VULN_TYPE, json_data)
    if response:
        delete_scan_results(scan_id)
'''

def delete_scan_results(scan_id):
    scanner = VulnscanManager(openvas_address, openvas_username, openvas_password, openvas_manager_port,
                              openvas_timeout)
    scanner.delete_scan(scan_id)


def delete_target_results(target_id):
    scanner = VulnscanManager(openvas_address, openvas_username, openvas_password, openvas_manager_port,
                              openvas_timeout)
    scanner.delete_target(target_id)


'''
OPENVAS SCAN METHODS END HERE
'''

#this = Schedule('client_id', 'www.qwerty123456.com', 'openvas', '2017-02-08 14:49:59', None, None, "Pending", None)
#this.add_schedule()
#stack_iterate_and_loop()

get_scan_results('9d00b9b3-7c25-4c8f-9be2-19d3792da8ea','127.0.0.1')
