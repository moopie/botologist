import logging
log = logging.getLogger(__name__)

import json
import urllib.error

import botologist.http
import botologist.plugin


def get_owm_json(*args, **kwargs):
	response = botologist.http.get(*args, **kwargs)
	contents = response.read().decode('utf-8')
	response.close()
	return contents


class WeatherPlugin(botologist.plugin.Plugin):
	def __init__(self, bot, channel):
		super().__init__(bot, channel)
		self.api_key = self.bot.config.get('openweathermap_apikey')

	@botologist.plugin.command('weather')
	def weather(self, cmd):
		'''Find out what the weather is somewhere.

		Example: !weather amsterdam
		'''
		if len(cmd.args) < 1:
			return 'Usage: !weather city'

		city = '-'.join(cmd.args)
		url = 'http://api.openweathermap.org/data/2.5/weather'
		query_params = {'q': city, 'units': 'metric', 'APPID': self.api_key}

		try:
			response = get_owm_json(url, query_params=query_params)
		except urllib.error.URLError:
			log.warning('OpenWeatherMap request caused an exception', exc_info=True)
			return 'An HTTP error occured, try again later!'

		data = json.loads(response)
		status = int(data['cod'])

		if status == 404:
			return 'Error: City not found'
		elif status != 200:
			return data['message']

		location = '{}, {}'.format(data['name'], data['sys']['country'])
		weather = data['weather'][0]['description']

		retval = 'Weather in {}: {}'.format(location, weather)
		if 'temp' in data['main']:
			retval += ' - temperature: {}°C'.format(data['main']['temp'])

		return retval
