#!/usr/bin/env python

import time
from pprint import pprint
from zapv2 import ZAPv2

#using apikey -daemon -port 8080 -host 127.0.0.1 -config api.key=kq68ak0mo6nsn2mjesl3t3au33

target = 'http://demo.testfire.net/'
# By default ZAP API client will connect to port 8080
#zap = ZAPv2()
#Use the line below if ZAP is not listening on port 8080, for example, if listening on port 8090
zap = ZAPv2(proxies={'http': 'https://127.0.0.1:8080', 'https': 'https://127.0.0.1:8080'})

apikey = 'kq68ak0mo6nsn2mjesl3t3au33' # Change to match the API key set in ZAP, or use None if the API key is disabled

# do stuff
print 'Accessing target %s' % target
# try have a unique enough session...
zap.urlopen(target)
# Give the sites tree a chance to get updated
time.sleep(2)

print 'Spidering target %s' % target
scanid = zap.spider.scan(target, apikey=apikey)
# Give the Spider a chance to start
time.sleep(2)
while (int(zap.spider.status()) < 100):
    print 'Spider progress %: ' + zap.spider.status()
    time.sleep(2)

print 'Spider completed'
# Give the passive scanner a chance to finish
time.sleep(5)

print 'Scanning target %s' % target
scanid = zap.ascan.scan(target, apikey=apikey)
while (int(zap.ascan.status()) < 100):
    print 'Scan progress %: ' + zap.ascan.status()
    time.sleep(5)

print 'Scan completed'

# Report the results
f = open('out2.txt', 'w')
f.write('Hosts: ' + ', '.join(zap.core.hosts))
f.write('Sites: ' + ', '.join(zap.core.sites))
f.write('Urls: ' + ', '.join(zap.core.urls))
f.write('Alerts: ')
pprint(zap.core.alerts(), f)
f.close()