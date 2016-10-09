from pyPdf import PdfFileReader 
import argparse
import os
import time
from shutil import copy2
from docx import Document

def Parse_argument():
	parser = argparse.ArgumentParser()
	parser.add_argument("-i", "--input", required=True, help="Input Target path")
	parser.add_argument("-o", "--output", required=True, help="Output Target path")
	parser.add_argument("--pdf", action="store_true", help="Check pdf file")
	parser.add_argument("--docx", action="store_true", help="Check docx file")
	return parser.parse_args()


def path_check(args):
	if os.path.isdir(args):
		return True
	else:
		return False

def make_output_folder(curtime, args):
	if path_check(args.output+"\\\\"+curtime):
		print "Please try again"
	else:
		os.mkdir(args.output+"\\\\"+curtime)
		return True


def check_each_PDF(file_path, file_name):
	try :
		file_full_path = str(file_path + "\\\\" + file_name)
		file_full_path = os.path.normcase(file_full_path)
		pdf = PdfFileReader(open(file_full_path, 'rb'))
		print "[Success] Success to open PDF, Filename=", file_name
		return True
	except Exception as e:
		print "[Fail] Fail to open PDF, Filename=", file_name, "Error=", e
		pass

def check_PDFs(args, curtime, open_cnt, fail_cnt):
	for root, dirs, files in os.walk(args.input):
		for file in files:
			if check_each_PDF(args.input, file) and os.path.isfile(args.input + "\\\\" +file):
				copy2(args.input+"\\\\"+file, args.output+"\\\\"+curtime+"\\\\"+file)
					
				open_cnt = open_cnt + 1
			else:
				fail_cnt = fail_cnt + 1

def start(args, curtime):
	open_cnt = 0
	fail_cnt = 0
	if args.pdf:
		check_PDFs(args, curtime, open_cnt, fail_cnt)

	print "[Success] :", open_cnt, "\t [fail] :", fail_cnt


if __name__== '__main__':
	args = Parse_argument()
	if path_check(args.input) and path_check(args.output):
		curtime = time.strftime("%Y%m%d%H%M%S")
		make_output_folder(curtime, args)
		start(args, curtime)
		

	else:
		if not os.path.isdir(args.input):
			print "Incorrect input path. Please check path again!"
		if not os.path.isdir(args.output):
			print "Incorrect output path. Please check path again!"
