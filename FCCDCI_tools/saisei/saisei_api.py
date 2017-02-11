import urllib2
import json
import argparse

list_len = 40
#api_list = {
#	"Interfaces_List":"/rest/top/configurations/running/interfaces",
#	"Hosts_List":"/rest/top/configurations/running/fibs/fib0/hosts/",
#	"User_List":"/rest/top/configurations/running/users/"
#	"root":"/rest/top/configurations/running"
#}
saisei_root = "/rest/top/configurations/running"

def make_json(base_url, username, password):
	collecttion={}
	url = base_url+saisei_root
	req = json.loads(get_data(url, username,password))
	leaf_dict_data = {}

	for req_list_num in range(len(req["collection"])):
		#print req["collection"][req_list_num].keys()
		for data_key in sorted(req["collection"][req_list_num].keys()):
			leaf_dict_data = find_leaf_url(req["collection"][req_list_num], data_key, base_url, username, password, leaf_dict_data)
		#call_href(base_url, url, username, password, url_list)
	return leaf_dict_data

def find_leaf_url(data, data_key, base_url, username, password, leaf_dict_data):
	if type(data[data_key])==dict:
		if 'link' in data[data_key]:
			leaf_dict_data = call_href(base_url, data[data_key]['link']['href'], username, password, leaf_dict_data)
		elif data_key == 'link':
			pass
		else:
			print "NO URL: ",
			print data[data_key]
		return leaf_dict_data
	else:
		return leaf_dict_data



def call_href(base_url, called_url, username, password, leaf_dict_data):
	req = json.loads(get_data(str(base_url+called_url), username ,password))
	for leaf in req["collection"]:
		if 'link' in leaf:
			#print called_url
			if leaf['link']['href'] == called_url and not('entries' in leaf):
				leaf_url = str(base_url+leaf['link']['href'][1:])
				print "Find leaf: "+leaf_url
				try:
					leaf_dict_data[leaf_url]=json.loads(get_data(leaf_url,username, password))['collection'][0]
				except Exception as e:
					print "Error occur call_href"
					print leaf_url
					print get_data(leaf_url,username, password)
					print leaf_dict_data
					print e
					pass

				print "Add json_data"
			elif 'entries' in leaf and leaf['entries']['link']['href'] != called_url:
				call_href(base_url, leaf['entries']['link']['href'], username, password, leaf_dict_data)
			elif leaf['link']['href'] != called_url:
				call_href(base_url, leaf['link']['href'], username, password, leaf_dict_data)
			else:
				print "Very Strange!!", 
				print leaf
	return leaf_dict_data
def get_data(url, username, password):
	try:
		return request_data(url, username, password)		
	except urllib2.HTTPError as e:
		pass

def request_data(url, username, password):
    p = urllib2.HTTPPasswordMgrWithDefaultRealm()
    p.add_password(None, url, username, password)
    handler = urllib2.HTTPBasicAuthHandler(p)
    opener = urllib2.build_opener(handler)
    urllib2.install_opener(opener)
    return urllib2.urlopen(url).read()

if __name__=="__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('-u', '--url', required = True, help='Input url')
	parser.add_argument('-i', '--id', required = True, help='Input username')
	parser.add_argument('-p', '--password', required = True, help='Input password')
	parser.add_argument('-n', '--filename', required = True, help='Out file name')
	args = parser.parse_args()

	result = make_json(args.url, args.id, args.password)
	
#	print json.dumps(result, sort_keys=True, indent = 5)

	with open('./'+args.filename, 'w') as out:
		json.dump(result, out, sort_keys=True)

