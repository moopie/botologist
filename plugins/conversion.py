import logging
log = logging.getLogger(__name__)

import datetime
import re
import requests
import requests.exceptions

import botologist.plugin


def format_number(number):
	if not isinstance(number, int):
		number = float(number)
		if number % 1 == 0.0:
			number = int(number)

	if isinstance(number, int):
		f_number = '{:,}'.format(number)
	else:
		f_number = '{:,.2f}'.format(float(number))

	if len(f_number) > 12:
		f_number = '{:.2}'.format(float(number))

	return f_number


def get_duckduckgo_data(url, query_params):
	return requests.get(url, query_params, timeout=2).json()


def get_conversion_result(query):
	query_params = {'q': query.lower(), 'format': 'json', 'no_html': 1}

	try:
		data = get_duckduckgo_data('https://api.duckduckgo.com', query_params)
	except requests.exceptions.RequestException:
		log.warning('DuckDuckGo request failed', exc_info=True)
		return False

	if data['AnswerType'] == 'conversions' and data['Answer']:
		return data['Answer']


_rate_expr = re.compile(r'<Cube currency=["\']([A-Za-z]{3})["\'] rate=["\']([\d.]+)["\']/>')
def get_currency_data():
	url = 'http://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'
	try:
		response = requests.get(url, timeout=2)
	except requests.exceptions.RequestException:
		log.warning('ECB exchange data request failed', exc_info=True)
		return {}

	matches = _rate_expr.findall(response.text)
	currency_data = {}
	for currency, exchange_rate in matches:
		currency_data[currency.upper()] = float(exchange_rate)
	log.info('Found %d currencies', len(currency_data))

	return currency_data


class Currency:
	last_fetch = None
	currency_data = None
	aliases = {'NIS': 'ILS', 'EURO': 'EUR'}

	@classmethod
	def currencies(cls):
		cls.load()
		return cls.currency_data.keys()

	@classmethod
	def convert(cls, amount, from_cur, to_cur):
		cls.load()

		try:
			amount = float(amount)
		except ValueError:
			return None

		from_cur = from_cur.upper()
		to_cur = to_cur.upper()

		if from_cur in cls.aliases:
			from_cur = cls.aliases[from_cur]
		if to_cur in cls.aliases:
			to_cur = cls.aliases[to_cur]

		if from_cur == to_cur:
			return None

		if from_cur == 'EUR':
			if to_cur not in cls.currency_data:
				return None
			return amount * cls.currency_data[to_cur]
		if to_cur == 'EUR':
			if from_cur not in cls.currency_data:
				return None
			return amount / cls.currency_data[from_cur]

		if from_cur in cls.currency_data and to_cur in cls.currency_data:
			amount = amount / cls.currency_data[from_cur]
			return amount * cls.currency_data[to_cur]

		return None

	@classmethod
	def load(cls):
		now = datetime.datetime.now()
		if cls.last_fetch:
			diff = now - cls.last_fetch
		if not cls.last_fetch or diff.seconds > 3600:
			cls.currency_data = get_currency_data()
			cls.last_fetch = now


def _conversion_regex():
	amount_pattern = r'((?:[\d][\d,. ]*?|[\.][\d]*?)[km]??)'
	unit_pattern = r'((?:(?:square|cubic) )?[a-z.,]+)'
	pattern = amount_pattern + r' ?' + unit_pattern + r' (into|in|to) ' + unit_pattern
	return re.compile(pattern, re.I)


class ConversionPlugin(botologist.plugin.Plugin):
	regex = _conversion_regex()

	@botologist.plugin.reply(threaded=True)
	def convert(self, msg):
		match = self.regex.search(msg.message)
		if not match:
			return

		conv_from = match.group(2)
		conv_to = match.group(4)
		if conv_from == conv_to:
			return

		amount = match.group(1).lower().replace(' ', '').replace(',', '')

		try:
			if amount.endswith('k'):
				real_amount = float(amount[:-1]) * 1000
			elif amount.endswith('m'):
				real_amount = float(amount[:-1]) * 1000000
			else:
				real_amount = float(amount)
		except ValueError:
			return

		if real_amount % 1 == 0.0:
			real_amount = int(real_amount)

		if ',' in conv_to:
			retvals = []
			for conv_to in conv_to.split(','):
				result = Currency.convert(real_amount, conv_from, conv_to)
				if result:
					format_result = format_number(result)
					retvals.append('{} {}'.format(format_result, conv_to))
			if retvals:
				format_amount = format_number(real_amount)
				return '{} {} = {}'.format(
					format_amount,
					conv_from,
					', '.join(retvals),
				)
		else:
			result = Currency.convert(real_amount, conv_from, conv_to)
			if result:
				format_amount = format_number(real_amount)
				format_result = format_number(result)
				return '{} {} = {} {}'.format(
					format_amount, conv_from, format_result, conv_to
				)

		# this format is a bit hard-coded to duckduckgo
		parts = (real_amount, conv_from, match.group(3), conv_to)
		query = ' '.join(str(part) for part in parts)
		result = get_conversion_result(query)
		if result:
			return result
