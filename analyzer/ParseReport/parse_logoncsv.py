#!/usr/bin/python
import csv
import json

def fillField(dict, field, row):
  dict[field].append(row[field]) if not (row[field] in dict[field]) else None
  return dict

# open file
content = ''

nodes = {}
links = {}

# construct a structure
#   {'sourceN:distinationM' : {'count' : L, 'events' : [eventID1, eventID2]}
dummyNode = {"User" : [], "Domain" : [], "Log File" : []}
dummyLink = {"Count" : 0, "Date Time" : [], "Type" : [], "Event ID" : [], "Logon Type" : [], "Auth Protocol" : []}

with open('logons_redacted_10000.csv', 'rb') as f:
  reader = csv.DictReader(f, delimiter=',')
  for row in reader:
    src = row["Source"]
    dest = row["Destination"]
    linkName = src + ":" + dest

    count = nodes[src]["Count"] + 1 if (src in nodes) else 0
    nodes[src] = {"Count" : count}
    count = nodes[dest]["Count"] + 1 if (dest in nodes) else 0
    nodes[dest] = {"Count" : count}
    count = links[linkName]["Count"] + 1 if (linkName in links) else 0
    links[linkName] = {"Count" : count}
    
#    tempNodeSrc = nodes[src] if (src in nodes) else dummyNode.copy()
#    for field in dummyNode:
#      tempNodeSrc = fillField(tempNodeSrc, field, row)
#
#    nodes[src] = tempNodeSrc
#    nodes[dest] = dummyNode.copy()
#
#    tempLink = links[linkName] if (linkName in links) else dummyLink.copy()
#    for field in dummyLink:
#      if (field == "Count"):
#        tempLink["Count"] = tempLink["Count"] + 1
#        continue
#      tempLink = fillField(tempLink, field, row)
#
#    links[linkName] = tempLink.copy()

# convert to a format suitable for d3js and save to json
nodesArr = []
linksArr = []

for key, val in nodes.iteritems():
  tempVal = val
  tempVal["id"] = key
  nodesArr.append(tempVal)

for key, val in links.iteritems():
  tempVal = val
  keySplit = key.split(":")
  tempVal["source"] = keySplit[0]
  tempVal["target"] = keySplit[1]
  linksArr.append(tempVal)

output = {"nodes" : nodesArr, "links" : linksArr}
# http://stackoverflow.com/questions/7100125/storing-python-dictionaries
with open('graph.json', 'w') as fp:
  json.dump(output, fp)
