#!/usr/bin/python
import csv
#import urllib2
from elasticsearch import Elasticsearch

# refer to 
#     https://qbox.io/blog/building-an-elasticsearch-index-with-python

FILE_URL = 'logons_redacted_fixed20160520.csv' # "http://apps.sloanahrens.com/qbox-blog-resources/kaggle-titanic-data/test.csv"

# http://elasticsearch-py.readthedocs.io/en/master/
ES_HOST = {"host" : "52.77.189.25", # static AWS IP
           "http_auth" : ('es_admin', 'nooffswitch'), # TODO: need secure way - https and certificates
           "port" : 9200}

INDEX_NAME = 'testcase20160524'
TYPE_NAME = 'logons'

ID_FIELD = 'passengerid'

#response = urllib2.urlopen(FILE_URL)
with open(FILE_URL, 'rb') as f:
  csv_file_object = csv.reader(f)
 
  header = csv_file_object.next()
  header = [item.lower() for item in header]

  bulk_data = [] 

  for row in csv_file_object:
    data_dict = {}
    for i in range(len(row)):
      data_dict[header[i]] = row[i]
    op_dict = {
      "index": {
      "_index": INDEX_NAME, 
      "_type": TYPE_NAME, 
      #"_id": data_dict[ID_FIELD]
      }
    }
    bulk_data.append(op_dict)
    bulk_data.append(data_dict)

  # create ES client, create index
  es = Elasticsearch(hosts = [ES_HOST])

  if es.indices.exists(INDEX_NAME):
    # !! careful, takes 10mins to load 20MB
    print("delete carefully, takes ~10mins to upload 20MB...")
    #print("deleting '%s' index..." % (INDEX_NAME))
    #res = es.indices.delete(index = INDEX_NAME)
    #print(" response: '%s'" % (res))

  # since we are running locally, use one shard and no replicas
  request_body = {
    "settings" : {
      "number_of_shards": 1,
      "number_of_replicas": 0
    },
    # http://joelabrahamsson.com/dynamic-mappings-and-dates-in-elasticsearch/
    # http://stackoverflow.com/questions/31994187/add-timestamp-to-elasticsearch-with-elasticsearch-py-using-bulk-api
    "mappings" : {
      TYPE_NAME : {
        "date_detection": "false",
        "properties": {
          "date time": {
            "type": "date",
            "format": "MM/dd/yyyy HH:mm:ss"
          }
        }
      }
    }
  }

  print("creating '%s' index..." % (INDEX_NAME))
  res = es.indices.create(index = INDEX_NAME, body = request_body)
  print(" response: '%s'" % (res))

  # bulk index the data
  print("bulk indexing...")
  res = es.bulk(index = INDEX_NAME, body = bulk_data, refresh = True, request_timeout=100)

  # sanity check
  res = es.search(index = INDEX_NAME, size=2, body={"query": {"match_all": {}}})
  print(" response: '%s'" % (res))