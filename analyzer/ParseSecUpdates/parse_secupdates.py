#!/usr/bin/python
import csv
import glob, os


input_raw = []
with open('input') as f:
  input_raw = f.readlines()

input = [line.strip() for line in input_raw]

# input[0] - location of input data
# input[1] - folder with sub-folders (each server) with logs
# input[2] - Bulletin csv
# input[3] - Folder with xml files with descriptions of CVRF

# output: names of servers, type of system, missing/present, cve, description of cve

kbs = []
with open(input[0] + '/' + input[2], 'rb') as f:
  reader = csv.DictReader(f, delimiter=',')
  kbs = list(reader)

log_loc = input[0] + '/' + input[1]
servers = os.walk(log_loc).next()[1] # [x[0] for x in os.walk(log_loc)]

servers_kb = {}
for server in servers:
  kb_loc = os.walk(log_loc + '/' + server).next()[1][0]
  # find a file
  os.chdir(log_loc + '/' + server + '/' + kb_loc)

  with open(glob.glob("*_kb.csv")[0], 'rb') as f:
    reader = csv.DictReader(f, delimiter=',')
    servers_kb[server] = list(reader)

for kb in kbs:
  # remove first KB letters
  kb_bulletin_id = kb['Bulletin KB']
  kb_component_id = kb['Component KB']
  for server, server_log in servers_kb.items():
    kb_id_found = False 
    for log in server_log:
      log_id = log['HOTFIX_ID'][2:] 
      if ((kb_bulletin_id == log_id) or (kb_component_id == log_id)):
        kb_id_found = True
        break
    kb[server] = kb_id_found

with open(input[0] + '/' + 'SecUpdates.csv', 'wb') as f: 
    w = csv.DictWriter(f, kbs[0].keys())
    w.writeheader()
    for kb in kbs:
      w.writerow(kb)

