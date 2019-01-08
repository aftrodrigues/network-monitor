#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argument_parse import *

import passive_monitor
import active_monitor

from threading import Thread
import argparse
import time
import collections
import traceback
import logging as log

global main_process

class server_monitor(Thread):
	def __init__(self, active_monitor, passive_monitor, interface, interval=2, hosts=[]):
		self.Thread.__init__()
		self.passive = passive_monitor
		self.active = active_monitor
		self.interval = interval
		self.hosts = hosts

		self.exec_flag = False
		self.data = collections.OrderedDict()

	def run(self):
		self.exec_flag = True
		self.passive.start()
		#self.active.set_monitor()

		while self.exec_flag:
			time_now = time.time()

			new_data = self.passive.get_data()
			

			self.data.update( self._filter(new_data) )

			if not self.sufficient_data():
				self.active.start()

			while time.time() - time_now < self.interval and self.exec_flag:
				time.sleep(.2)
	
	def stop(self):
		self.exec_flag = False
		self.passive.stop()
		self.active.stop()

	def get_data(self):
		return self.data


	def _filter(self, new_data):
		filtered = collections.OrderedDict()
		if len(self.hosts) == 0:
			filtered = new_data	
		else:
			for tm in new_data:
				for send in new_data[tm]:
					if send in self.hosts:
						if tm not in filtered:
							filtered[tm] = {}
						filtered[tm][send] = new_data[tm][send]
		return filtered


def main(args):
	global main_process

	log_format = '[%(asctime)s] %(funcName)s[%(lineno)d]: %(msg)s'

	log.basicConfig(level=args.level, format=log_format)
	log.debug('DEBUG: start time: %s' % time.time())

	#active = active_monitor.active_monitor()
	#passive = passive_monitor.pping_monitor(interface='enp3s0', log)
	main_process = server_monitor(	active_monitor.active_monitor, 
									passive_monitor.pping_monitor, 
									interface='enp3s0',
									hosts=['143.54.12.128'])
	#main_process.start()
	return
	#  TODO: take automaticate the interface in the computer
	if args.interface is None:
		args.interface = default_interface
	args_interpreter(args)

	# Initialing the subprocess 'necessarios'
	if args.active:
		log.info('Starting transmission test with iperf3')
		#iperf3_process = sub.Popen(['iperf3',  '-c', 'futebol-cbtm'], stdout=sub.PIPE)
		#process.append(iperf3_process)
		#print(iperf3_process)


# need refactor!
def clean_up():
	"""
	Close all the process open by this script, referenced by the GLOBAL list process.
	:return:
	"""
	global main_process

	main_process.stop()


	process = []
	log.debug('Cleaning')

	child_process = ''
	for p in process:
		log.info('Stopping child proccess: [%s] %s' % ( p.process.pid, p.name))
		if p.process is not None:
			child_process += ('' if len(child_process) == 0 else '\|') + str(p.process.pid)
			p.process.kill()

	if child_process:
		ps = sub.Popen(('ps', '-ax'), stdout=sub.PIPE)
		output = sub.check_output(('grep', child_process), stdin=ps.stdout)
		ps.wait()
		log.info('Verify if all the child process was closed: \n%s' % output)
	log.info('Exiting')



if __name__ == '__main__':
	args_parser = set_argparse()

	try:
		main( args=parse_arguments(args_parser) )

	except KeyboardInterrupt:
		log.info('Keyboard Interruption')
		clean_up()

		try:
			sys.exit(0)
		except SystemExit:
			os._exit(0)

	except Exception as e:
		clean_up()
		print(traceback.format_exc())
		raise e
	finally:
		clean_up()
		pass