import requests
from .prevoznik import Prevoznik
import datetime
import dateutil.parser

class Prevozi(object):

	def __init__(self):
		self.seja = requests.Session()
		self.postaje = self.prenesiSeznamPostaj()
	
	def prenesiSeznamPostaj(self):
		postaje = []

		parametri = {
			'unit': 0,
			'topN': 8000,
			'order': 3
		}

		# V Sloveniji je 12 razlicnih regij, preberemo podatke vseh naselij v teh regijah
		for i in range(13):
			response = requests.get('https://www.stat.si/KrajevnaImena/Search/ByUnit/{:02d}'.format(i), params=parametri)
			nova_naselja = response.json()

			for naselje in nova_naselja:
				postaje.append(naselje['Naselje']['NaseljeIme'].lower())
		
		return postaje

	def seznamPostaj(self):
		return self.postaje

	def obstajaPostaja(self, imePostaje):
		return imePostaje.lower() in self.postaje

	def prenesiVozniRed(self, vstopnaPostaja, izstopnaPostaja, datum):
		parametri = {
			'f': vstopnaPostaja,       	# Vstopna postaja
			't': izstopnaPostaja,     	# Izstopna postaja
			'fc': 'SI',                 # Drzava vstopne postaje
			'tc': 'SI',                 # Drzava izstopne postaje
			'd': datum.strftime('%Y-%m-%d'),
			'exact': True,				# Ce iscemo LE prevoze med tema mestoma
			'intl': False
		}
		response = requests.get('https://prevoz.org/api/search/shares/', params=parametri)
		podatki = response.json()

		prevozi = []

		for prevoz in podatki['carshare_list']:
			cas_prevoza = dateutil.parser.parse(prevoz['date_iso8601'])
			cena = prevoz['price']
			prevozi.append({
				"prihod": cas_prevoza,
				"odhod": cas_prevoza,
				"peron": "",
				"prevoznik": "prevozi.org",
				"cena": cena,
				"razdalja": 0
			})


		return prevozi

	def vmesnePostaje(self, prevoz):
		return []