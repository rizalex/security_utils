import os

class Integrite_tools(object):
	def __init__(self):
		self.correct_cnt = 0
		self.fail_cnt = 0
		self.read_file_cnt = 0
		self.correct_file_list=[]

	def set_curtime(self, curtime):
		self.curtime = curtime

	def get_curtime(self):
		return self.curtime

	def set_output_base_folder_name(self, out_path):
		self.output_base_folder_name = out_path

	def get_output_base_folder_name(self):
		return self.output_base_folder_name

	def set_intput_target_list(self, in_path):
		self.intput_target_list = in_path

	def get_intput_target_list(self):
		return self.intput_target_list

	def set_init_data(self, target_list, output, curtime):
		self.curtime = curtime
		self.output_base_folder_name = output
		self.intput_target_list = target_list

	def set_append_correct_file_list(self, file_path, file_name):
		self.correct_file_list.append(os.path.join(file_path, file_name))

	def get_correct_file_list(self):
		return self.correct_file_list

	def add_read_file_cnt(self):
		self.read_file_cnt = self.read_file_cnt + 1

	def get_read_file_cnt(self):
		return self.read_file_cnt

	def add_correct_cnt(self):
		self.correct_cnt = self.correct_cnt + 1

	def get_correct_cnt(self):
		return self.correct_cnt

	def add_fail_cnt(self):
		self.fail_cnt = self.fail_cnt + 1

	def get_fail_cnt(self):
		return self.fail_cnt

	def set_args(self, args):
		self.args = args

	def get_args(self):
		return self.args

	def set_logging(self, logging):
		self.logging = logging

	def get_logging(self):
		return self.logging

	def print_and_logging(self, str):
		print str
		self.logging.info(str)

	def path_check(self, dir_path):
		if os.path.isdir(dir_path):
			return True
		else:
			return False