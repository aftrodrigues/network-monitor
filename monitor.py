#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess as sub
import time
import logging as log
import json
import signal
import signal
import sys
import argparse
import collections
import os
import simpleNamespace
import traceback

location = 'pping/output.txt'
output_file = location
default_interface = 'enp3s0'
MAX_TIME = 30
process = []

def get_data(file, old_lines = 0):
	""" recupera as ultima linhas adicionadas do arquivo dado
	file: String, local e nome do arquivo onde esta os dados
	old_lines: Integer, devolve as ultimas linhas a partir dessas linhas
	"""

	actual_lines = sub.check_output(['wc', '-l', file])
	actual_lines = int(actual_lines.split(' ')[0])
	
	txt = sub.check_output(['tail', '-n', str(actual_lines - old_lines), location])
	log.debug("actual_line: %s / new_lines(txt): %s" % (actual_lines, len(txt)))
	return (txt, actual_lines)


def parser(line):
	"""
	line: time, rtt, fr->min, fBytes, dBytes, pBytes, hosts#
	time: in epoch format
	fr->min: shortest round trip delay seen so far for this flow 
	fBytes: total bytes of flow through CP including this pkt
	dBytes: total bytes of in
	pBytes: 
	hosts: flow in the form:  srcIP:port+dstIP:port
	"""

	line = line.split(" ")
	if len(line) < 6:
		log.debug("Linha pequena")
		return (None,) * 5

	try:
		tm = float(line[0])  # time when the packet was receive, in epoch
	except Exception as e:
		log.error(e)
		log.error('inside: %s' % line)
		return (None,) * 5

	rtt = float(line[1])  # the round-trip-time
	fr_min = float(line[2])  # minimun rtt

	hosts = line[-1].split("+")
	send, recv = '', ''
	try:
		send = hosts[0].split(":")[0]  # send of the packet
		recv = hosts[1].split(":")[0]  # receiver of the packet
	except IndexError:
		log.error('IndexError')
		log.error('line: %s' % line)

	log.debug("[%f] %s -> %s _ %s [%s]" % (tm, send, recv, rtt, fr_min))
	return (tm, send, recv, rtt, fr_min)


def validate_data(data):
	"""
	Verifica se há dados na tupla e transforma eles de string para o formato desejado,

	return: tupla, (int, string, string, float, float) = tm, send, recv, rtt, fr_min
			or
			None, se houver algum dado mal informado.
	"""
	tm, send, recv, rtt, fr_min = data
	if tm is None:
		return None

	tm = int(tm)

	return tm, send, recv, rtt, fr_min


def save_data(results, data):
	"""
	Adiciona os dados da tupla no dicionário de informações de time, host, receiver e informações dos pacotes
	"""
	tm, send, recv, rtt, fr_min = data
	if tm is None:
		return
	if int(tm) not in results:
		results[int(tm)] = {}

	if send not in results[int(tm)]:
		results[int(tm)][send] = {}

	if recv not in results[int(tm)][send]:
		results[int(tm)][send][recv] = [[rtt, fr_min]]
	else:
		data = results[int(tm)][send][recv]
		data.append( [rtt, fr_min] )


def traver_data(data):
	"""
	Percorre a arvore, devolvendo uma tupla com todos os dados de cada vez.
	"""
	for tm in data:
		for send in data[tm]:
			receivers = data[tm][send]
			for recv in receivers:
				info = receivers[recv]
				#log.debug('returning: %s %s %s %s' % (tm, send, recv, info))
				yield tm, send, recv, info


def resume_data(results):
	"""
	resume as informações contidas no dicionário, transformando a lista de informações por segundo
	em maior, menor, média e total de packets utilizados.
	:param results: dict( <times> : dict ( <senders>: dict( <receivers>: list( [rtt, min->rtt]))))
	:return: dict( <times> : dict ( <senders>: dict( <receivers>: (maior, menor, media, total))))
	"""
	for tm, send, recv, infos in traver_data(results):
		if time.time() - tm < 1:
			#  the program is still fetching one second of information about this period of time
			continue
		
		soma, total, media = 0, 0, 0
		max_rtt, min_rtt = 0, 0
		previous_rtt, jitter = None, 0
		min_jtt, max_jtt, sum_jtt = float('inf'), 0, 0

		if len(infos) > 0:
			max_rtt = infos[0][0]
			min_rtt = infos[0][0]

		for register in infos:
			actual_rtt = register[0]
			if actual_rtt > max_rtt:
				max_rtt = actual_rtt
			if actual_rtt < min_rtt:
				min_rtt = actual_rtt
			soma += actual_rtt
			total += 1

			# Jitter calculation
			if previous_rtt is None:
				previous_rtt = register[0]
			else:
				jitter = previous_rtt - actual_rtt
				if jitter < min_jtt:
					min_jtt = jitter
				if jitter > max_jtt:
					max_jtt = jitter
				sum_jtt += abs(jitter)

		if soma != 0 and total != 0:
			media = soma/total
		else:
			media = max_rtt

		header = '[%s] %s -> %s' % ( time.strftime('%H:%M:%S', time.gmtime(tm)), send, recv)
		log.info(header)
		log.info('rtt: max:%s / min:%s / media:%s / total: %s' %
			(format_float_string(max_rtt, 's'),
			format_float_string(min_rtt, 's'),
			format_float_string(media, 's'),
			total))

		if total == 1:
			log.info('jtt: max:%s / min %s / sum %s / media %s' %
				(max_jtt, min_jtt, sum_jtt, sum_jtt / total))
		else:
			log.info('jtt: max:%s / min %s / sum %s / media %s' %
			(format_float_string(max_jtt, 's'),
				format_float_string(min_jtt, 's'),
				format_float_string(sum_jtt, 's'),
				format_float_string(sum_jtt / total, 's')))
		infos = simpleNamespace.SimpleNamespace(max_rtt=max_rtt, min_rtt=min_rtt, media=media, total=total)


def resume_data_backup(results):
	"""
	resume as informações contidas no dicionário, transformando a lista de informações por segundo
	em maior, menor, média e total de packets utilizados.
	:param results: dict( <times> : dict ( <senders>: dict( <receivers>: list( [rtt, min->rtt]))))
	:return: dict( <times> : dict ( <senders>: dict( <receivers>: (maior, menor, media, total))))
	"""
	for tm in results:
		if time.time() - tm < 1:
			#  the program is still fetching one second of information about this period of time
			continue
		sends = results[tm]
		for send in sends:
			receivers = sends[send]
			for recv in receivers:
				data = receivers[recv]
				soma_rtt, n_packets, media = 0, 0, 0
				max_rtt, min_rtt = 0, 0
				previous_rtt, jitter = None, 0
				min_jtt, max_jtt, sum_jtt = float('inf'), 0, 0

				if len(data) > 0:
					maior = data[0][0]
					menor = data[0][0]

				for register in data:
					actual_rtt = register[0]
					# max and min rtt
					if actual_rtt > max_rtt:
						max_rtt = actual_rtt
					if actual_rtt < min_rtt:
						min_rtt = actual_rtt
					# soma e quantidade para fazer a media
					soma_rtt += actual_rtt
					n_packets += 1

					# Jitter calculation
					if previous_rtt is None:
						previous_rtt = register[0]
					else:
						jitter = previous_rtt - actual_rtt
						if jitter < min_jtt:
							min_jtt = jitter
						if jitter > max_jtt:
							max_jtt = jitter
						sum_jtt += abs(jitter)

				if soma_rtt and n_packets:
					media = soma_rtt/n_packets

				header = '[%s] %s -> %s' % ( time.strftime('%H:%M:%S', time.gmtime(tm)), send, recv)
				log.info(header)
				log.info('rtt: max:%s / min:%s / media:%s / total: %s' %
							(format_float_string(max_rtt, 's'),
							format_float_string(min_rtt, 's'),
							format_float_string(media, 's'),
							n_packets))

				if n_packets != 1:
					log.info('jtt: max:%s / min %s / sum %s / media %s' %
								(format_float_string(max_jtt, 's'),
								format_float_string(min_jtt, 's'),
								format_float_string(sum_jtt, 's'),
								format_float_string(sum_jtt / n_packets, 's')))
				else:
					log.info('jtt: max:%s / min %s / sum %s / media %s' %
								(max_jtt, min_jtt, sum_jtt, sum_jtt / n_packets))
				receivers[ recv ] = simpleNamespace.SimpleNamespace(maior=maior, menor=menor, media=media, total=total)


def processor(results=None, txt=''):
	"""
	pega as linhas contidas no arquivo, e processa elas.
	retorna um dict de dict, com tempo, sender, receiver, [ maior rtt, menor rtt, media, jitter]
	"""
	if results is None:
		results = collections.OrderedDict()

	lines = txt.split('\n')
	log.debug(len(lines))
	for line in lines:
		#  time, send, recv, rtt, fr_min = parser(line)
		data_tupla = parser(line)

		if None not in data_tupla:
			save_data(results, data_tupla)

	resume_data(results)
	return results
		

def dump_result(result):
	" not used "
	for tm, packets in result.items():
		for send in packets:
			for recv, data in packets[send].items():
				if len(data) < 5:
					log.debug('[%s] %s -> %s : %s' % (tm, send, recv, data))
	

def make_relatory(seconds=float('inf')):
	"""
	Gera um relatorio por segundo.
	Fica em loop aqui ate passar MAX_TIME segundos.
	"""
	lines = 0
	seconds_passed = 0
	results = None
	while seconds_passed < seconds:
		old_time = time.gmtime()
		print("++++++++++"*7)
		data, lines = get_data(location, lines)
		if len(data) != 0:
			log.debug('len: [%s] / data: %s' % (lines, data[-1]))
			
			processor(results, data)
			#dump_result(results)

		while(time.gmtime().tm_sec == old_time.tm_sec ):
			time.sleep(0.05)
		seconds_passed += 1


def set_argparse():
	"""
	Configura o argument Parser da linha de comando, e retorna o parser
	"""
	
	args_parser = argparse.ArgumentParser(
		description='active/passive monitor, that show latency(rtt) and jitter,'+\
		' resuming the information each second For DEFAULT, only listen in one interface')
	args_parser.add_argument('-l', '--level', default='INFO', 
		help='level of log, [info, error, debug, warning]')
	args_parser.add_argument('-i', '--interface', default=None, 
		help='in which interface is to the program listen')
	args_parser.add_argument('-a', '--active', default=False, action='store_true',
		help='Generate a lot of traffic tcp in the interface')

	""" Tráfego UDP pelo iperf3 gera um pacote tcp por segundo, o que não é muito útil """
	args_parser.add_argument('-z', '--analyzer', action='store_true', 
		help='Analize one file generate by pping and defined by -f, --file.'+\
		' DEFAULT: analize the file output.txt')
	args_parser.add_argument('-f', '--file', default=str(output_file),
		help='File to be output the pping or/and to be analyzed')
	args_parser.add_argument('-t', '--time', type=int, default=-1,
		help='During how much time is to be listen. If ommit, wait ctrl+c from user to stop.')
	return args_parser


def parse_arguments(parser):
	"""
	Valida os argumentos recebidos via linha de comando e devolve eles.
	params:
	parser: <class argparse.ArgumentParser>, o parser com os argumentos

	return: <class argparse.Namespace>
	"""
	args = parser.parse_args()
	print('args: %s' % args)

	args.level = args.level.upper()
	if args.level not in ['INFO', 'DEBUG', 'ERROR', 'WARNING']:
		raise Exception('command line argument not valid')

	return args


def args_interpreter(args):
	print('log format: %s' % args.level)


	if args.analyzer:
		print('analisando arquivo %s' % (args.file))
	else:
		if args.time < 0:
			args.time = 'inf'
		if args.active:
			print('Gerando tráfego com TCPDUMP')
		print("Listen in the interface %s for %s's" % (args.interface, float(args.time)))


def main():
	args_parser = set_argparse()
	args = parse_arguments(args_parser)

	log_format = '[%(asctime)s] %(funcName)s[%(lineno)d]: %(msg)s'

	log.basicConfig(level=args.level, format=log_format)
	log.debug('DEBUG: start time: %s' % time.time())
	#  TODO: take automaticate the interface in the computer
	if args.interface is None:
		args.interface = default_interface
	args_interpreter(args)

	# Initialing the subprocess 'necessarios'
	if args.analyzer is False:
		log.info('INFO: Starting pping...')
		arq_output = open(args.file, 'w')
		pping_process = sub.Popen(['./pping/pping', '-m', '-i', args.interface, '-q'], stdout=arq_output)
		process.append(simpleNamespace.SimpleNamespace(name='pping', process=pping_process))

		if args.active:
			log.info('Starting transmission test with iperf3')
			#iperf3_process = sub.Popen(['iperf3',  '-c', 'futebol-cbtm'], stdout=sub.PIPE)
			#process.append(iperf3_process)
			#print(iperf3_process)

	make_relatory(seconds=args.time)
	clean_up()	
	log.debug('end time: %s' % time.time())


def clean_up():
	"""
	Close all the process open by this script, referenced by the GLOBAL list process.
	:return:
	"""
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


def format_float_string(value, unit, step=1000):
	"""
	Converte o valor para algo entre 0 e o step( 1000 por default )
	e acrescenta ao final do valor um sinal de grandeza e um sinal de unidade.
	Params:
	value: int ou float, o valor a ser transformado
	unit: string, a unidade de medida do valor
	step: int ou float, a escala da 'transformation' a ser utilizada

	return: string, no formato '<value><Posfixo><Unit>'
	"""
	ds, neg = 0, 0
	decPosfix = ['m', 'u']
	incPosfix = ['k', 'M', 'G', 'T']

	if value < 0:
		value = value * -1
		neg = 1

	if value != 0:
		if value > 1:
			while value > 1000 and ds+1 < len(incPosfix):
				value = value / 1000
				ds += 1
		else:
			while value < 1 and abs(ds-1) < len(decPosfix):
				value = value * 1000
				ds -= 1

	if neg:
		value = value * -1

	value = str('%.2f' % value)
	if ds < 0:
		ds = (-ds)-1
		value += decPosfix[ds]
	elif ds > 0:
		value += incPosfix[ds]

	return str(value) + str(unit)


if __name__ == '__main__':
	#  Examples to make by hand the command line handler
	#print('Number of arguments: %s' % len(sys.argv))
	#print('Argument list: %s' % sys.argv)
	
	try:
		main()	
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
