#!/usr/bin/python
import csv
from random import randint

fileName = 'logons_redacted_fixed20160520'

originalData = []
uniqueIP = {}

with open(fileName + '.csv', 'rb') as f:
  reader = csv.DictReader(f, delimiter=',')
  for row in reader:
    src = row["Source"]
    dest = row["Destination"]

    uniqueIP[src] = {"src IP" : src}

    originalData.append(row)

# randomly generate fake IPs
for key, val in uniqueIP.iteritems():
  src = val["src IP"]
  #if (src == ""):
  #    continue
  srcIpArr = src.split(".")
  if (len(srcIpArr) < 4):
      print "skip this broken IP: " + src 
      continue
  srcIpArr[0] = str(randint(0,255))
  srcIpArr[1] = str(randint(0,255))
  src = ".".join(srcIpArr)

  uniqueIP[key]["fake IP"] = src

for row in originalData:
  row["Source"] = uniqueIP[row["Source"]]["fake IP"] if ("fake IP" in uniqueIP[row["Source"]]) else row["Source"]

keys = originalData[0].keys()
with open(fileName + "_fakeIP.csv", 'wb') as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(originalData)

