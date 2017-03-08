import threading

# !/usr/bin/python
# Targets (websites) for external scans.
import os.path
from pysrc.es_ops import EsQuery
from datetime import datetime
from pysrc.es_connect import EsConnect

'''
{
'requested_by': <user>,
'target': <host>,
'scanner': <nikto,openvas,etc.>,
'status': <done, error, pending, scanning>
'scan_id': <scan id>
'scan_request_start_datetime': <2017-01-23T00:00>,
'scan_start_datetime': <2017-01-23T00:00>,
'scan_end_datetime': <2017-01-23T00:00>,
'create_datetime': <2017-01-23T00:00>,
}



{
  "took" : 1,
  "timed_out" : false,
  "_shards" : {
    "total" : 1,
    "successful" : 1,
    "failed" : 0
  },
  "hits" : {
    "total" : 1,
    "max_score" : 1.0,
    "hits" : [ {
      "_index" : "schedule_list",
      "_type" : "schedules",
      "_id" : "AVoDFj48sW_x73cABngb",
      "_score" : 1.0,
      "_source" : {
        "requested_by" : "test user",
        "status" : "Pending",
        "scan_id" : null,
        "target" : "www.google.com",
        "scan_end_datetime" : null,
        "scan_request_start_datetime" : "20170203002752.632287",
        "create_datetime" : "20170203002752.632327",
        "scan_start_datetime" : null,
        "scanner" : "openvas"
      }
    } ]
  }
}

'''

class Schedule(object):
    INDEX_NAME = "schedule_list"
    TYPE_NAME = "schedules"

    TIME_FMT = "%Y%m%d%H%M%S.%f"
    schedule_status = ["Pending", "In Queue", "Scanning", "Scanned"]

    esq_TMP = None

    def __init__(self, requested_by, target,scanner,scan_request_start_datetime,scan_start_datetime=None,scan_end_datetime=None, status=schedule_status[0],scan_id=None):
        # For log
        """ instantiate the class """
        self.requested_by = requested_by
        self.target = target
        self.scanner = scanner
        self.status = status
        self.scan_id = scan_id
        self.scan_request_start_datetime = scan_request_start_datetime
        self.scan_start_datetime = scan_start_datetime
        self.scan_end_datetime = scan_end_datetime
        self.create_datetime =  datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def create_mapping_if_not_exists(self):
        esConnection = EsConnect().getConnection()

        mapping = {
          "mappings":{
              self.TYPE_NAME :{

                "properties": {
                  "scan_request_start_datetime": {
                    "type": "date",
                    "format": "yyyy-MM-dd HH:mm:ss"
                  }
                ,
                "scan_start_datetime":{
                    "type": "date",
                    "format": "yyyy-MM-dd HH:mm:ss"

                },
                "scan_end_datetime":{
                    "type": "date",
                    "format": "yyyy-MM-dd HH:mm:ss"

                },
                "create_datetime":{
                    "type": "date",
                    "format": "yyyy-MM-dd HH:mm:ss"
                  }

          }
        }
        }
        }

        if esConnection.indices.exists(self.INDEX_NAME):
            print "Schedule indice exists"
        else:
            print esConnection.indices.create(index=self.INDEX_NAME, body=mapping)

    def add_schedule(self):
        #if esConnection.indices.exists(self.INDEX_NAME):
        #    print ("Creating mapping")
        self.create_mapping_if_not_exists()

        create_datetime = datetime.now().isoformat(' ')
        print create_datetime
        esq = EsQuery()
        data = {'requested_by':self.requested_by, 'target': self.target,'scanner': self.scanner,'status': self.status, 'scan_id': self.scan_id,'scan_request_start_datetime':self.scan_request_start_datetime,'scan_start_datetime':self.scan_start_datetime,'scan_end_datetime':self.scan_end_datetime,'create_datetime':self.create_datetime}
        esq.index(self.INDEX_NAME, self.TYPE_NAME, data)

    def get_all_schedule(self):
        esq = EsQuery()
        res = esq.scrollEs(self.INDEX_NAME)

    def dataTableReadEs(self, queryReq, size):
        esq = EsQuery()

        res = esq.queryEs(self.INDEX_NAME, queryReq, sizeVal=size)

        return res['hits']['hits'], res['hits']['total']