import xmltodict
import json
import os
files = [
	"nvdcve-2.0-2002.xml", "nvdcve-2.0-2003.xml", "nvdcve-2.0-2004.xml", "nvdcve-2.0-2005.xml",
	"nvdcve-2.0-2006.xml", "nvdcve-2.0-2007.xml", "nvdcve-2.0-2008.xml", "nvdcve-2.0-2009.xml",
	"nvdcve-2.0-2010.xml", "nvdcve-2.0-2011.xml", "nvdcve-2.0-2012.xml", "nvdcve-2.0-2013.xml",
	"nvdcve-2.0-2014.xml", "nvdcve-2.0-2015.xml", "nvdcve-2.0-2016.xml"
		 ]

#files = ["test.xml", "test.xml"]
def opennvdcve_XML(file_loc):
	with open(file_loc) as data_file:
		dict_data = xmltodict.parse(data_file.read(), xml_attribs=True)
		if not isinstance(dict_data, list): 
			dict_data = [dict_data]
		return dict_data

def write_json(xml, base_path, output_name, file_name, flag):
	try:
		outfile = open(str(base_path+output_name), 'a')
		outfile.write(str("\""+file_name+"\": "))
		for entry in enumerate(d['nvd']['entry'] for d in xml):
			outfile.write("%s\n" % json.dumps(entry))
		if flag:
			outfile.write(str(","))
		
	except Exception as e:
		print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Wirte JSON Error", e

	finally:
		outfile.close()

def check_output_file(base_path, output_name):
	if os.path.exists(str(base_path+output_name)):
		print str(base_path+output_name)," file exist. <File removed>"
		os.remove(str(base_path+output_name))

def conv_json(base_path, output_name):
	check_output_file(base_path, output_name)
	try:
		flag=True
		i=0
		outfile = open(str(base_path+output_name), 'a')
		outfile.write("{")
		outfile.close()
		for file_name in files:
			i = i+1
			print str(base_path+file_name)
			xml = opennvdcve_XML(str(base_path+file_name))
			if i == len(files):
				flag=False
			write_json(xml, base_path, output_name, file_name, flag)
		outfile = open(str(base_path+output_name), 'a')
		outfile.write("}")
		outfile.close()			

	except Exception as e:
		print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!ReadXML ERROR", e
		outfile.close()


if __name__=='__main__':
	base_path = "C:\\NVD_CVE\\cve-master\\"
	output_name = "ALL_nvdcve.json"
	conv_json(base_path, output_name)
