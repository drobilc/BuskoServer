from .prevoznik import Prevoznik
import requests
from bs4 import BeautifulSoup
import datetime
import re

class Arriva(Prevoznik):
	
	def __init__(self):
		self.seja = requests.Session()

		# Najdemo api kljuc na strani
		response = self.seja.get("https://arriva.si/")
		assert "apiData" in response.text
		assert "cTimeStamp" in response.text
		assert "datetime" in response.text

		datetimeRegex = r'\"datetime\"\s*:\s*\"([^\"]*)\"'
		timestampRegex = r'\"cTimeStamp\"\s*:\s*\"([^\"]*)\"'

		datetimeMatch = re.search(datetimeRegex, response.text, re.MULTILINE)
		timestampMatch = re.search(timestampRegex, response.text, re.MULTILINE)

		self.datetime = datetimeMatch.group(1)
		self.timestamp = timestampMatch.group(1)

		self.postaje = self.prenesiSeznamPostaj()
		self.imenaPostaj = dict([(item[0].lower(), item[1]) for item in self.postaje.items()])

	def prenesiSeznamPostaj(self):
		get_parameters = {
			"JSON": 1,
			"SearchType": "2",
			"cTIMESTAMP": self.datetime,
			"cTOKEN": self.timestamp,
			"POS_NAZ": "%"
		}
		response = self.seja.get("https://prometws.alpetour.si/WS_ArrivaSLO_TimeTable_DepartureStations.aspx", params=get_parameters)

		postaje = {}
		for postaja in response.json()[0]['DepartureStations']:
			postaje[postaja["POS_NAZ"]] = postaja["JPOS_IJPP"]
		return postaje

	def seznamPostaj(self):
		return [postaja for postaja in self.postaje]

	def obstajaPostaja(self, imePostaje):
		return imePostaje.lower() in self.imenaPostaj
	
	def postajaId(self, imePostaje):
		# Najprej preverimo ali postaja sploh obstaja
		if not self.obstajaPostaja(imePostaje):
			return None
		# Ce obstaja, vrnemo njen id (poiscemo jo v slovarju imenaPostaj)
		return self.imenaPostaj[imePostaje.lower()]

	def prenesiVozniRed(self, vstopnaPostaja, izstopnaPostaja, datum):
		url = "https://arriva.si/vozni-redi/?departure=Ljubljana+AP&departure_id=138922&destination=Ajdov%C5%A1%C4%8Dina&destination_id=137011&trip_date=15.02.2019"
		get_parameters = {
			"departure": vstopnaPostaja,
			"departure_id": self.postajaId(vstopnaPostaja),
			"destination": izstopnaPostaja,
			"destination_id": self.postajaId(izstopnaPostaja),
			"trip_date": datum.strftime("%d.%m.%Y")
		}
		response = self.seja.get("https://arriva.si/vozni-redi/", params=get_parameters)
		
		html = BeautifulSoup(response.text, "html.parser")
		prevozi_divs = html.find_all("div", {"class": "connection"})

		vsi_prevozi = []
		for prevoz_div in prevozi_divs:
			if 'connection-header' in prevoz_div['class']:
				continue
			osnovni_podatki = prevoz_div.find("div", {"class": "departure-arrival"})
			odhod = osnovni_podatki.find("tr", {"class": "departure"}).find("td").text
			prihod = osnovni_podatki.find("tr", {"class": "arrival"}).find("td").text
			razdalja = prevoz_div.find("div", {"class": "length"}).text
			cena = prevoz_div.find("div", {"class": "price"}).text
			prevoznik = prevoz_div.find("div", {"class": "prevoznik"}).find_all("span")[-1].text

			# Popravimo ceno in razdaljo v stevila
			cena = float(cena.replace("EUR", "").strip())
			razdalja = float(razdalja.replace("km", "").strip())

			uraPrihoda = datetime.datetime.strptime(prihod, "%H:%M")
			uraOdhoda = datetime.datetime.strptime(odhod, "%H:%M")

			prihod = datum.replace(hour=uraPrihoda.hour, minute=uraPrihoda.minute)
			odhod = datum.replace(hour=uraOdhoda.hour, minute=uraOdhoda.minute)

			# Preverimo ali se je vmes zamenjal dan
			if prihod < odhod:
				prihod = prihod + datetime.timedelta(days = 1)

			dodatni_podatki = prevoz_div.find("div", {"class": "display-path"})["data-args"]

			vsi_prevozi.append({
				"prihod": prihod,
				"odhod": odhod,
				"peron": "",
				"prevoznik": prevoznik,
				"cena": cena,
				"razdalja": razdalja,
				"_parametri_postaje": dodatni_podatki
			})

		return vsi_prevozi

	def vmesnePostaje(self, prevoz):
		relacije = []

		get_parameters = eval(prevoz["_parametri_postaje"])
		get_parameters["action"] = "get_DepartureStationList"

		response = self.seja.get("https://arriva.si/wp-admin/admin-ajax.php", params=get_parameters)

		html = BeautifulSoup(response.text, "html.parser")
		vrstice = html.find_all("tr")

		# Preskocimo vsako drugo vrstico
		for vrstica in vrstice:
			if len(vrstica.text.strip()) < 1:
				continue
			stolpci = vrstica.find_all("td")

			ime_postaje = stolpci[-1].text
			prihod = stolpci[0].text

			datumPrihoda = prevoz['odhod']
			uraPrihoda = datetime.datetime.strptime(prihod, "%H:%M")
			datumPrihoda = datumPrihoda.replace(hour=uraPrihoda.hour, minute=uraPrihoda.minute)

			if datumPrihoda < prevoz['odhod']:
				datumPrihoda = datumPrihoda + datetime.timedelta(days = 1)

			relacije.append({
				"postaja": ime_postaje,
				"cas_prihoda": datumPrihoda
			})

		return relacije