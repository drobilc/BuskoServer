from .prevoznik import Prevoznik
import requests
from bs4 import BeautifulSoup
import datetime
import re

class Alpetour(Prevoznik):
	
	def __init__(self):
		self.seja = requests.Session()
		#https://www.alpetour.si/wp-admin/admin-ajax.php
		self.prenesiSeznamPostaj()

	def prenesiSeznamPostaj(self):
		postajeUrl = "https://www.alpetour.si/avtobusni-prevozi/javni-linijski-prevozi/avtobusni-vozni-redi/"
		response = self.seja.get(postajeUrl)
		html = BeautifulSoup(response.text, "html.parser")
		field = html.find("select", {"id": "fid"})
		postaje = {}
		if field:
			options = field.findAll("option")
			for option in options:
				postajaId = option["value"]
				postajaIme = option.text
				postaje[postajaIme] = postajaId
		self.postaje = postaje

	def seznamPostaj(self):
		if len(self.postaje) <= 0:
			self.prenesiSeznamPostaj()
		return list(self.postaje.keys())

	def obstajaPostaja(self, imePostaje):
		return imePostaje in self.postaje

	def prenesiSurovePodatke(self, vstopnaPostaja, izstopnaPostaja, datum):
		if type(datum) is datetime.datetime:
			datum = datum.strftime("%Y-%m-%d")
		vozniRedUrl = "https://www.alpetour.si/wp-admin/admin-ajax.php"

		podatki = {
			"action": "showRoutes",
			"fromID": self.postaje[vstopnaPostaja],
			"toID": self.postaje[izstopnaPostaja],
			"date": datum,
			"general": "false"
		}
		response = self.seja.post(vozniRedUrl, data=podatki)
		#html = BeautifulSoup(response.text, "html.parser")
		return response.json()

	def prenesiVozniRed(self, vstopnaPostaja, izstopnaPostaja, datum):
		podatki = self.prenesiSurovePodatke(vstopnaPostaja, izstopnaPostaja, datum)
		prevoziPodatki = []
		for vrstica in podatki["schedule"]:
			uraPrihoda = datetime.datetime.strptime(vrstica["PRIHOD_FORMATED"], "%H:%M")
			uraOdhoda = datetime.datetime.strptime(vrstica["ODHOD_FORMATED"], "%H:%M")
			casPrihoda = datum.replace(hour=uraPrihoda.hour, minute=uraPrihoda.minute)
			casOdhoda = datum.replace(hour=uraOdhoda.hour, minute=uraOdhoda.minute)
			prevoz = {
				"prihod": casPrihoda,
				"odhod": casOdhoda,
				"trajanje": vrstica["CAS_FORMATED"],
				"peron": vrstica["ROD_PER"],
				"prevoznik": vrstica["RIDER"],
				"cena": "{} EUR".format(vrstica["VZCL_CEN"]),
				"razdalja": "{} km".format(vrstica["KM_POT"]),
				"url": ""
			}
			if prevoz["peron"] == None:
				prevoz["peron"] = " "
			if len(prevoz["prevoznik"]) > 20:
				prevoz["prevoznik"] = prevoz["prevoznik"].split(" ")[0].replace(",", "")
			prevoziPodatki.append(prevoz)
		return prevoziPodatki

if __name__ == "__main__":
	bus = Alpetour()
	print(bus.prenesiVozniRed("Ljubljana AP", "Kamne", datetime.datetime.now()))