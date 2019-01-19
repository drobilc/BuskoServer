# -*- coding: utf-8 -*-
from .prevoznik import Prevoznik
import requests
from bs4 import BeautifulSoup
import datetime

class APLjubljana(Prevoznik):
	
	def __init__(self):
		self.seja = requests.Session()
		self.postaje = self.prenesiSeznamPostaj()

	def prenesiSeznamPostaj(self):
		response = self.seja.get("https://www.ap-ljubljana.si/_vozni_red/get_postajalisca_vsa_v2.php")
		lines = response.text.strip().split("\n")
		postaje = {}
		for line in lines:
			idPostaje, imePostaje = line.split("|")
			idPostaje = (int(idPostaje.split(":")[0]), int(idPostaje.split(":")[1]))
			postaje[idPostaje] = imePostaje.strip()
		return postaje

	def seznamPostaj(self):
		return list(self.postaje.values())

	def obstajaPostaja(self, imePostaje):
		return imePostaje in self.postaje.values()

	def postajaId(self, imePostaje):
		for postaja in self.postaje:
			if self.postaje[postaja] == imePostaje:
				return postaja

	def prenesiVozniRed(self, vstopnaPostaja, izstopnaPostaja, datum):
		if type(datum) is datetime.datetime:
			datum = datum.strftime("%d.%m.%Y")
		url = "https://www.ap-ljubljana.si/_vozni_red/get_vozni_red_0.php"
		repsonse = self.seja.post(url, data={
			"VSTOP_ID": self.postajaId(vstopnaPostaja),
			"IZSTOP_ID": self.postajaId(izstopnaPostaja),
			"DATUM": datum
		})
		prevozi = []
		for vrstica in repsonse.text.split("\n"):
			podatki = vrstica.split("|")
			if len(podatki) < 2:
				continue
			odhod = podatki[6]
			prihod = podatki[7]
			trajanje = podatki[8]
			cena = podatki[9]
			uraPrihoda = datetime.datetime.strptime(prihod, "%Y-%m-%d %H:%M:%S")
			uraOdhoda = datetime.datetime.strptime(odhod, "%Y-%m-%d %H:%M:%S")
			prevoz = {
				"prihod": uraPrihoda,
				"odhod": uraOdhoda,
				"trajanje": trajanje,
				"peron": "",
				"prevoznik": "AP LJUBLJANA",
				"cena": "{} EUR".format(cena),
				"razdalja": "/",
				"url": ""
			}
			prevozi.append(prevoz)
		return prevozi

if __name__ == "__main__":
	ap = APLjubljana()
	print(ap.prenesiVozniRed("LJUBLJANA AVTOBUSNA POSTAJA", "Velenje", datetime.datetime.now()))