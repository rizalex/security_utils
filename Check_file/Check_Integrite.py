import argparse
import os
import time
import logging
from shutil import copy2
from check_pdf import PDF
from check_docx import DOCX
from check_doc import DOC
from check_xlsx import XLSX
from check_xls import XLS
from Check_Integrite_tools import Integrite_tools


def Parse_argument():
	parser = argparse.ArgumentParser()
	parser.add_argument("-t", "--target_list", required=True, help="Input Target path")
	parser.add_argument("-o", "--output", required=True, help="Output Target path")
	parser.add_argument("--all", action="store_true", help="Check *.pdf, *.docx file")
	parser.add_argument("--pdf", action="store_true", help="Check pdf file")
	parser.add_argument("--docx", action="store_true", help="Check docx file")
	parser.add_argument("--doc", action="store_true", help="Check doc file")
	parser.add_argument("--xlsx", action="store_true", help="Check xlsx file")
	parser.add_argument("--xls", action="store_true", help="Check xls file")

	return parser.parse_args()



def copy_file(file_name, ext):
	try:
		copy2(os.path.join(tools.get_intput_target_list(), file_name),  os.path.join(os.path.join(tools.get_output_base_folder_name(), tools.get_curtime()), os.path.join(ext, file_name)))
	finally:
		tools.print_and_logging(str("%s%-6s%s%s%s" % ("[  copy_", ext, "] ", "file_name=", file_name)))
	

def start_pdf(file_name):
	if pdf.check_each_PDF(tools.get_intput_target_list(), file_name):
		copy_file(file_name, "pdf")
		tools.add_correct_cnt()
	else:
		tools.add_fail_cnt()

def start_docx(file_name):
	if docx.check_each_DOCX(tools.get_intput_target_list(), file_name):
		copy_file(file_name, "docx")
		tools.add_correct_cnt()
	else:
		tools.add_fail_cnt()

def start_doc(file_name):
	if doc.check_each_DOC(tools.get_intput_target_list(), file_name):
		copy_file(file_name, "doc")
		tools.add_correct_cnt()
	else:
		tools.add_fail_cnt()

def start_xlsx(file_name):
	if xlsx.check_each_XLSX(tools.get_intput_target_list(), file_name):
		copy_file(file_name, "xlsx")
		tools.add_correct_cnt()
	else:
		tools.add_fail_cnt()

def start_xls(file_name):
	if xls.check_each_XLS(tools.get_intput_target_list(), file_name):
		copy_file(file_name, "xls")
		tools.add_correct_cnt()
	else:
		tools.add_fail_cnt()

def check_condition(file_name):
	if tools.get_args().all:
		if file_name.split('.')[-1].lower()=="pdf":
			start_pdf(file_name)

		elif file_name.split('.')[-1].lower()=="docx":
			start_docx(file_name)

		elif file_name.split('.')[-1].lower()=="doc":
			start_doc(file_name)

		elif file_name.split('.')[-1].lower()=="xlsx":
			start_xlsx(file_name)

		elif file_name.split('.')[-1].lower()=="xls":
			start_xls(file_name)

	elif tools.get_args().pdf:
		if file_name.split('.')[-1].lower()=="pdf":
			start_pdf(file_name)

	elif tools.get_args().docx:
		if file_name.split('.')[-1].lower()=="docx":
			start_docx(file_name)

	elif tools.get_args().doc:
		if file_name.split('.')[-1].lower()=="doc":
			start_doc(file_name)

	elif tools.get_args().xlsx:
		if file_name.split('.')[-1].lower()=="xlsx":
			start_xlsx(file_name)

	elif tools.get_args().xls:
		if file_name.split('.')[-1].lower()=="xls":
			start_xls(file_name)

	else:
		tools.print_and_logging(str("[Error] Please choose at leat one file type. All, pdf, docx, xlsx."))

def main():
	"""
	when add more function must check it!!
	- make output folder
	- add argument
	- check_condition
	- make def check_(function name)
	- summary
	- __name__== '__main__'
	"""

	
	os.mkdir(os.path.join(tools.get_output_base_folder_name(), tools.get_curtime()))
	logging.basicConfig(level=logging.DEBUG, filename=os.path.join(os.path.join(tools.get_output_base_folder_name(), tools.get_curtime()),'result.txt'), filemode="a", format="%(asctime)-15s %(levelname)-8s %(message)s")
	tools.set_logging(logging)
	if tools.get_args().all:
		os.mkdir(os.path.join(os.path.join(tools.get_output_base_folder_name(), tools.get_curtime()), 'pdf'))
		os.mkdir(os.path.join(os.path.join(tools.get_output_base_folder_name(), tools.get_curtime()), 'docx'))
		os.mkdir(os.path.join(os.path.join(tools.get_output_base_folder_name(), tools.get_curtime()), 'doc'))
		os.mkdir(os.path.join(os.path.join(tools.get_output_base_folder_name(), tools.get_curtime()), 'xlsx'))
		os.mkdir(os.path.join(os.path.join(tools.get_output_base_folder_name(), tools.get_curtime()), 'xls'))
	elif tools.get_args().pdf:
		os.mkdir(os.path.join(os.path.join(tools.get_output_base_folder_name(), tools.get_curtime()), 'pdf'))
	elif tools.get_args().docx:
		os.mkdir(os.path.join(os.path.join(tools.get_output_base_folder_name(), tools.get_curtime()), 'docx'))
	elif tools.get_args().doc:
		os.mkdir(os.path.join(os.path.join(tools.get_output_base_folder_name(), tools.get_curtime()), 'doc'))
	elif tools.get_args().xlsx:
		os.mkdir(os.path.join(os.path.join(tools.get_output_base_folder_name(), tools.get_curtime()), 'xlsx'))
	elif tools.get_args().xls:
		os.mkdir(os.path.join(os.path.join(tools.get_output_base_folder_name(), tools.get_curtime()), 'xls'))

	for root, dirs, files in os.walk(tools.get_intput_target_list()):
		tools.set_intput_target_list(root)
		for file_name in files:
			check_condition(file_name)
			tools.add_read_file_cnt()
	tools.print_and_logging(str(""))
	tools.print_and_logging(str("-------------------------------------Summary-------------------------------------"))
	try:
		tools.print_and_logging(str("%-10s%s%6d\t%s%6d" %("[pdf]","openable_cnt:", pdf.get_correct_cnt(), "unopenable_cnt:", pdf.get_fail_cnt())))
		tools.print_and_logging(str("%-10s%s%6d\t%s%6d" %("[docx]","openable_cnt:", docx.get_correct_cnt(), "unopenable_cnt:", docx.get_fail_cnt())))
		tools.print_and_logging(str("%-10s%s%6d\t%s%6d" %("[doc]","openable_cnt:", doc.get_correct_cnt(), "unopenable_cnt:", doc.get_fail_cnt())))
		tools.print_and_logging(str("%-10s%s%6d\t%s%6d" %("[xlsx]","openable_cnt:", xlsx.get_correct_cnt(), "unopenable_cnt:", xlsx.get_fail_cnt())))
		tools.print_and_logging(str("%-10s%s%6d\t%s%6d" %("[xls]","openable_cnt:", xls.get_correct_cnt(), "unopenable_cnt:", xls.get_fail_cnt())))
	except Exception as e:
		pass

	tools.print_and_logging("")
	tools.print_and_logging(str("---------------------------------------------------------------------------------"))
	#tools.print_and_logging(str("[Result]\tread_cnt:"+str(tools.get_read_file_cnt())+"\topenable_cnt:"+ str(tools.get_correct_cnt())+ "\tunopenable_cnt:"+ str(tools.get_fail_cnt())))
	tools.print_and_logging(str("%-10s%s%10d\t%s%8d\t%s\t%d" %("[Result]", "read_cnt:", tools.get_read_file_cnt(), "openable_cnt:", tools.get_correct_cnt(), "unopenable_cnt:", tools.get_fail_cnt())))
	tools.print_and_logging(str("---------------------------------------------------------------------------------"))



if __name__== '__main__':
	args = Parse_argument()
	curtime = time.strftime("%Y%m%d%H%M%S")
	tools = Integrite_tools()
	pdf = PDF()
	docx = DOCX()
	doc = DOC()
	xlsx = XLSX()
	xls = XLS()

	tools.set_init_data(args.target_list, args.output, curtime)
	tools.set_args(args)
	main()





