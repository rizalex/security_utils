import XMLtoJSON
import json

if __name__=="__main__":
	base_path = "C:\\NVD_CVE\\cve-master\\"
	output_name = "ALL_nvdcve.json"
	XMLtoJSON.conv_json(base_path, output_name)

	data_file = str('C:\\NVD_CVE\\cve-master\\ALL_nvdcve.json')
	with open(data_file, 'r') as f:
		data = json.load(f)
		print data
		