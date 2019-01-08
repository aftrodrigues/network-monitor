from threading import Thread 

class active_monitor(Thread):
	def __init__(self, hosts=[], **kwargs):
		self.hosts = hosts

		self.exec_flag = False

	
	def run():
		self.exec_flag = True

	def start_monitor():
		pass

	def stop():
		self.exec_flag = False

	def get_data():
		pass
