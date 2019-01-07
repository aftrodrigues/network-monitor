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