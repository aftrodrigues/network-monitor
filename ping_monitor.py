import sys
import os
import traceback
import subprocess as sub
import time
from threading import Thread
import logging as log
import argparse

process = []

class ping_monitor:

	def __init__(self, interface, interval, ip, log):
		self.iface = interface
		self.interval = interval
		self.ip = ip
		self.process = None
		self.log = log

		if self.interval < .2:
			raise Exception("Ping interval can't less than 200ms")


	def __str__(self):
		return '<ping_monitor to %s' % self.ips


	def start_monitor(self):
		"""
		Start to ping to destiny.
		return: Bool, if the monitor start or not.
		"""

		results = []
		log.info('begin monitor in ip %s' % self.ip)
		
		self.log.debug('Sending ping to %s' % self.ip)
		ping = sub.Popen(['ping', '-i', str(self.interval), #  interval >= 200ms
									  '-D',	# Show epoch time
									  '-n', #  Numeric output only
									  self.ip],   #  ip to ping
									  stdout=sub.PIPE,  # redirect the data out to pipe
									  stderr=sub.PIPE)  # reduret tge data out to pipe
		process.append(ping)
		self.process = ping

		# header do ping
		self.log.debug('ping header: %s' % self.process.stdout.readline().replace('\n', ''))
		self.log.debug('subprocess status: %s\n' % ('Alive' if ping.poll() is None else 'Dead'))

		return True if ping.poll() is None else False
	

	def stop(self):
		p = self.process
		log.debug('Process %s / status: %s' % (p.pid, 'Dead' if p.poll() else 'Alive'))
		log.debug('status: %s' % p.poll())
		
		if p and p.poll() is None:
			p.terminate()
			log.debug('after terminate: %s' % p.stdout.read())
			log.debug('status: %s' % p.poll())

		if p and p.poll() is None:
			p.kill()
			log.debug('after kill: %s' % p.stdout.read())
			log.debug('status: %s' % p.poll())

		log.debug('')


	def get_data(self, limit_buffer=1024):
		"""
		Read from the stdout from ping and parsing the results until the last ping

		return: list of tuples, each tuple in the format (time_of_packet, rtt)
		"""

		buffer = 0
		results = []

		# first line
		pkt_info = self.process.stdout.readline().replace('\n', '')
		pkt_time, pkt_rtt = self._parse_line(pkt_info)

		results.append( (pkt_time, pkt_rtt) )

		# continue until the actual moment
		while self.interval < (time.time() - float(pkt_time)):

			# next packet:
			pkt_info = self.process.stdout.readline().replace('\n', '')
			pkt_time, pkt_rtt = self._parse_line(pkt_info)

			results.append( (pkt_time, pkt_rtt) )		

		return results
	

	def _parse_line(self, str):
		"""
		"""
		splited = str.split(" ")

		pkt_time = splited[0][1:-1]

		pkt_rtt = splited[7].split("=")[-1]
		pkt_rtt = float( pkt_rtt )

		# SI converter
		if splited[8][0] == 'm':
			pkt_rtt = pkt_rtt / 1000
		
		return (pkt_time, pkt_rtt)


	def _str_ping_bottom_parse(self, str):
		parsed = str.splitlines()
		data = parsed[-1]
		rtt_min, rtt_avg, rtt_max, rtt_mdev = data.split(" = ")[1].split("/")
		print("%s/%s/%s/%s" %(rtt_min, rtt_avg, rtt_max, rtt_mdev))

	def get_statistics(self, data=()):
		data = list( data )

		if len(data) == 0:
			return (0, 0, 0, 0, 0)

		rtt_max, rtt_min = data[0][1], data[0][1]
		total, sample = data[0][1], 1
		previous = data[0][1]
		variation = 0
		
		del data[0]

		for tm, rtt in data:
			sample += 1
			total += rtt

			if rtt > rtt_max:
				rtt_max = rtt
			elif rtt < rtt_min:
				rtt_min = rtt

			variation += abs(previous - rtt)

		return rtt_max, total / sample, rtt_min, variation, sample


def set_argparse():
	"""
	Configure the argument Parser to receive parameters by command line
	"""
	
	args_parser = argparse.ArgumentParser( description='Active monitor using ping.' )
			
	args_parser.add_argument('-i', '--interface', default=None, 
		help='in which interface is to the program listen. Can be omit')
	
	args_parser.add_argument('-f', '--frequency', type=int, default=2, 
		help='pings by seconds. Can\'t be greater than 5')

	args_parser.add_argument('-t', '--interval', type=int, default=1,
		help='Seconds between the analysis of the latency')

	args_parser.add_argument('-l', '--level', default='INFO', 
		help='level of log, [info, error, debug, warning]')

	args_parser.add_argument('-p', '--ips', nargs='*', default=[],
		help='List of IPs to Monitor')

	args = args_parser.parse_args()
	args.level = args.level.upper()

	return args


def clean_up():
	"""
	Kill all the process created by this script and appends to global
	variable <process>.
	"""

	for p in process:
		log.debug(p)
		log.debug('Process %s / status: %s' % (p.pid, 'Dead' if p.poll() is None else 'Alive'))
		log.debug('status: %s' % p.poll())
		

		if p and p.poll() is None:
			p.terminate()
			log.debug('after terminate: %s' % p.stdout.read())
			log.debug('status: %s' % p.poll())

		if p and p.poll() is None:
			p.kill()
			log.debug('after kill: %s' % p.stdout.read())
			log.debug('status: %s' % p.poll())



def main(args):
	log.debug(args)
	i = 0
	count = 10

	monitors = []

	for ip in args.ips:
		monitor = ping_monitor(args.interface, 1/args.frequency, ip, log)
		monitors.append( monitor )
		monitor.start_monitor()

	
	while True:
		time_now = time.time()
		while time.time() - time_now < args.interval:
			time.sleep(.1)
		
		for monitor in monitors:
			dados = monitor.get_data()
			statistics = monitor.get_statistics(dados)
			log.info('%s: rtt_max/avg/min/variation/sample: %s' % (monitor.ip , 
									('%.6f %.6f %.6f %.6f %d' % statistics)))

		print('')


	for monitor in monitors:
		monitor.stop()


if __name__ == '__main__':
	args = set_argparse()
		
	if args.level == 'DEBUG':
		format = '%(funcName)-8s [%(lineno)3s]: %(msg)s'
	else:
		format = '%(msg)s'

	log.basicConfig(level=args.level, format=format)


	try:
		main(args)

	except KeyboardInterrupt:
		log.debug('\nKeyboard Interruption')

	except Exception as e:
		log.debug(traceback.format_exc())

	finally:
		clean_up()
		print('')

		try:
			sys.exit(0)

		except SystemExit:
			os._exit(0)
