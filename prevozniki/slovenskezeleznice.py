# -*- coding: utf-8 -*-
#from .prevoznik import Prevoznik
from prevoznik import Prevoznik
import requests
from bs4 import BeautifulSoup
import datetime

class SlovenskeZeleznice(Prevoznik):
	
	def __init__(self):
		self.seja = requests.Session()
		self.postaje = self.prenesiSeznamPostaj()

	def prenesiSeznamPostaj(self):
		response = self.seja.get("https://www.slo-zeleznice.si/sl/")
		html = BeautifulSoup(response.text, "html.parser")
		select = html.find("select", {"id": "viaPostaja"})
		options = select.find_all("option")
		postaje = {}
		for option in options[1:]:
			optionId = option['value']
			optionText = option.text
			postaje[int(optionId)] = optionText
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
			showDa = datum.strftime("%d.%m.%Y")
			datum = datum.strftime("%Y-%m-%dT00:00:00")
		url = "https://www.slo-zeleznice.si/sl/component/sz_timetable/"
		response = self.seja.get(url, params={
			"vs": self.postajaId(vstopnaPostaja),
			"iz": self.postajaId(izstopnaPostaja),
			"vi": "",
			"da": datum,
			"showDa": showDa
		})
		html = BeautifulSoup(response.text, "html.parser")
		resultsTable = html.find("table", {"class": "timeTable"})
		results = resultsTable.find("tbody").find_all("tr")

		print(results[0])
		for row in results:
			#print(row)
			# Najdemo cas odhoda in cas prihoda
			columnDeparture = row.find("td", {"class": "tdDeparture"})
			columnArrival = row.find("td", {"class": "tdArrival"})
			print(columnDeparture.text, columnArrival.text)
		return []

	def vmesnePostaje(self, prevoz):
		"""url = "https://www.ap-ljubljana.si/_vozni_red/get_linija_info_0.php"
		response = self.seja.post(url, data={
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
		"""
		return []

if __name__ == "__main__":
	sz = SlovenskeZeleznice()
	sz.prenesiVozniRed("Maribor", "Ljubljana", datetime.datetime.now())