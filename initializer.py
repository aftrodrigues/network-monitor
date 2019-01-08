import server_monitor

def main():
	args_parser = set_argparse()
	args = parse_arguments(args_parser)

	log_format = '[%(asctime)s] %(funcName)s[%(lineno)d]: %(msg)s'

	log.basicConfig(level=args.level, format=log_format)
	log.debug('DEBUG: start time: %s' % time.time())

	return
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