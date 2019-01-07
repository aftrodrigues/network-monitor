import passive_monitor
import pping_function
import logging as log

def teste():
	output = 'teste.txt'
	pping_monitor = passive_monitor.pping_monitor(log)
	pping_monitor.output = output

	txt = pping_monitor._get_data_from_file(output, 0)

	if txt != pping_function.get_data_from_file(output, 0):
		print('Error in the function get_data_from_file')


	for line in txt:
		try:
			if pping_monitor._parser(line) != pping_function.pping_parser(line):
				print('Error in the function parser')
		except:
			pass
	
	data1, data2 = {}, {}

	pping_monitor._added_raw_data(data1, pping_monitor._parser(txt[0])) 
	pping_function.save_data(data2, pping_monitor._parser(txt[0]))
	if data1 != data2:
		print('Error in the function _added_raw_data')

	if pping_monitor._interprete_data(data1) != pping_function.resume_data(data1):
		print('Error in the function _interprete_data')

	pping_monitor.run()
	
	for k, v in pping_monitor.data.iteritems():
		print('%s -> %s' % (k, v))

if __name__ == '__main__':
	teste()
