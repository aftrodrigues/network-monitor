import argparse

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