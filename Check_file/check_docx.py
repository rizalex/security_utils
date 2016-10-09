import os
from docx import Document


class DOCX(object):
	def __init__(self):
		self.correct_cnt = 0
		self.fail_cnt = 0

	def add_correct_cnt(self):
		self.correct_cnt = self.correct_cnt + 1

	def get_correct_cnt(self):
		return self.correct_cnt

	def add_fail_cnt(self):
		self.fail_cnt = self.fail_cnt + 1

	def get_fail_cnt(self):
		return self.fail_cnt

	def check_each_DOCX(self, file_path, file_name):
		file_full_path = os.path.join(file_path, file_name)
		
		try :
			d = open(file_full_path,'rb')
			docx = Document(d)
			#print "[Success] Success to open PDF, Filename=", file_name
			self.add_correct_cnt()
			return True

		except Exception as e:
			#print "[Fail] Fail to open PDF, Filename=", file_name, "Error=", e
			self.add_fail_cnt()
			pass

		finally:
			d.close()