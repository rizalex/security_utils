#!/usr/bin/env python

import time
import datetime
from pprint import pprint
from zapv2 import ZAPv2

import sqlalchemy
from sqlalchemy.sql.expression import func, and_, or_, desc
from apps import app
from apps.extensions.db import db
from apps.database import User, Website, ScanResult, Severity, SecurityBrief, Averages
from pprint import pprint

ZAP_address = "127.0.0.1"
ZAP_port = "8080"
ZAP_API_key = 'kq68ak0mo6nsn2mjesl3t3au33'
ZAP_TIME_FMT = "%Y-%m-%dT%H:%M:%SZ"

#using apikey -daemon -port 8080 -host 127.0.0.1 -config api.key=kq68ak0mo6nsn2mjesl3t3au33
#./zap.sh -daemon -port 8080 -host 139.59.23.38 -config api.key=kq68ak0mo6nsn2mjesl3t3au33

target = 'https://demo.testfire.net/'
zap = ZAPv2(apikey='kq68ak0mo6nsn2mjesl3t3au33',
    proxies={'http': 'https://' + ZAP_address + ':' + ZAP_port, 'https': 'https://' + ZAP_address + ':' + ZAP_port})


def start_scan(user_id, target):

    print 'Accessing target %s' % target
    # try have a unique enough session...
    zap.urlopen(target)
    # Give the sites tree a chance to get updated
    time.sleep(2)

    print 'Spidering target %s' % target
    scanid = zap.spider.scan(target)
    # Give the Spider a chance to start
    time.sleep(2)
    while (int(zap.spider.status(scanid)) < 100):
        print 'Spider progress %: ' + zap.spider.status()
        time.sleep(2)

    print 'Spider completed'
    # Give the passive scanner a chance to finish
    time.sleep(5)

    print 'Scanning target %s' % target
    scanid = zap.ascan.scan(target)
    while (int(zap.ascan.status(scanid)) < 100):
        print 'Scan progress %: ' + zap.ascan.status(scanid)
        time.sleep(5)

    print 'Scan completed'

    parse_create_results(user_id,target)

def parse_create_results(user_id,target):
    creation_time = (datetime.datetime.now().strftime(ZAP_TIME_FMT))
    for alert in zap.core.alerts():
        user_id
        target = alert['url']
        #Check if target is still assumed is the same, this is because of spidering the URL will not be the same for the same target
        cve_cwe = alert['cweid']
        #Don't see any CVEs for now, only the more general CWEs
        #We got to corelate the output for ZAP and Openvas
        port = "80,443/TCP"
        #hardcoded to web application ports
        cvss_base = None
        description = alert['description'].join(alert['solution'])
        family = ""
        pg_scan_id = ""
        psql_create(user_id, target, cve_cwe, port, cvss_base, description, family, creation_time, pg_scan_id)
    #might have to delete results here

def psql_create(user_id, hostname, cve_id, port_string, cvss_base, description, family, creation_time, scan_id):
    user, host = None, None
    #try:    # scans for market does not have user and website on the other tables
    #    user = User.query.filter(User.first_name == user_id).one()
    #    host = Website.query.filter(or_(
    #        Website.hostname == hostname,
    #        Website.hostname == 'www.' + hostname
    #    )).one()
    #except sqlalchemy.orm.exc.NoResultFound as e:
    #    if "Market" not in user_id:
    #        print("user_id = %s no host or user in other tables" % user_id)
    scan_data = {
        'vuln_id': cve_id,
        'scan_id': scan_id,
        'manual': False,
        'date_created' : creation_time
    }
    if user and host:
        scan_data['user_id'] = user.id
        scan_data['website_id'] = host.id
    port, protocol_type = port_string.split('/')
    try:
        #port = int(port)
        #cannot assume port to be a number
        scan_data['port'] = port  # do not store for those with no port (like "general")
    except ValueError as e:
        print("Errored: " + str(e))
        pass

    scan_data['description'] = description
    scan_data['family'] = family
    scan_data['port_type'] = protocol_type

    score = cvss_base
    #need a number for unclassified
    print ("severity score ".join(str(score)))
    severity = score_severity(score)
    scan_data['severity'] = severity
    ScanResult.create(commit=True, **scan_data)
    print ("created")
    # pprint(scan_data)

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


print(datetime.datetime.now().strftime(ZAP_TIME_FMT))
start_scan(1, target)