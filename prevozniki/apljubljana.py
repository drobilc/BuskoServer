# -*- coding: utf-8 -*-
from .prevoznik import Prevoznik
import requests
from bs4 import BeautifulSoup
import datetime

class APLjubljana(Prevoznik):
	
	def __init__(self):
		self.seja = requests.Session()

		# Hranimo dva slovarja:
		#   * postaje: { id_postaje (int) : ime_postaje (string, case sensitive) }
		#   * imenaPostaj: { ime_postaje (string, case insensitive): id_postaje (int) }
		self.postaje = self.prenesiSeznamPostaj()

		# Na podlagi prenesenega slovarja ustvarimo nov slovar, kjer obrnemo vrstni red elementov
		self.imenaPostaj = dict([(item[1].lower(), item[0]) for item in self.postaje.items()])

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
		# Funkcija vrne case sensitive seznam postaj
		return list(self.postaje.values())

	def obstajaPostaja(self, imePostaje):
		# Sprejmemo ime postaje in preverimo ali postaja s takim imenom obstaja (case insensitive)
		return imePostaje.lower() in self.imenaPostaj

	def postajaId(self, imePostaje):
		# Najprej preverimo ali postaja sploh obstaja
		if not self.obstajaPostaja(imePostaje):
			return None
		# Ce obstaja, vrnemo njen id (poiscemo jo v slovarju imenaPostaj)
		return self.imenaPostaj[imePostaje.lower()]

	def prenesiVozniRed(self, vstopnaPostaja, izstopnaPostaja, datum):
		# Datum najprej pretvorimo v ustrezen format (v niz)
		if type(datum) is datetime.datetime:
			datum = datum.strftime("%d.%m.%Y")
		
		response = self.seja.post("https://www.ap-ljubljana.si/_vozni_red/get_vozni_red_0.php", data={
			"VSTOP_ID": self.postajaId(vstopnaPostaja),
			"IZSTOP_ID": self.postajaId(izstopnaPostaja),
			"DATUM": datum
		})

		prevozi = []
		for vrstica in response.text.split("\n"):
			podatki = vrstica.split("|")
			if len(podatki) < 2:
				continue
			odhod = podatki[6]
			prihod = podatki[7]
			cena = float(podatki[9])
			uraPrihoda = datetime.datetime.strptime(prihod, "%Y-%m-%d %H:%M:%S")
			uraOdhoda = datetime.datetime.strptime(odhod, "%Y-%m-%d %H:%M:%S")
			dodatniPodatki = podatki[-1]

			# Podatka o razdalji tukaj nimamo
			prevoz = {
				"prihod": uraPrihoda,
				"odhod": uraOdhoda,
				"peron": "",
				"prevoznik": "AP LJUBLJANA",
				"cena": cena,
				"razdalja": 0,
				"_vmesne_postaje_data": dodatniPodatki
			}
			prevozi.append(prevoz)
		return prevozi

	def vmesnePostaje(self, prevoz):
		response = self.seja.post("https://www.ap-ljubljana.si/_vozni_red/get_linija_info_0.php", data={
			"flags": prevoz['_vmesne_postaje_data']
		})
		relacije = []
		for vrstica in response.text.split("\n")[1:]:
			podatki = vrstica.split("|")
			if len(podatki) < 2:
				continue
			postaja = podatki[1]
			cas = datetime.datetime.strptime(podatki[2], "%Y-%m-%d %H:%M:%S")

			relacije.append({
				"postaja": postaja,
				"cas_prihoda": cas
			})
		return relacije