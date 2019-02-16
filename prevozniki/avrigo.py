from .prevoznik import Prevoznik
import requests
from bs4 import BeautifulSoup
import datetime
import re

class Avrigo(Prevoznik):
	
	def __init__(self):
		self.seja = requests.Session()
		try:
			response = self.seja.get("https://voznired.noleggio-bus.it/VozniRed.aspx")
			html = BeautifulSoup(response.content, "html.parser")
			self.VIEWSTATE = html.find(id="__VIEWSTATE")['value']
			self.VIEWSTATEGENERATOR = html.find(id="__VIEWSTATEGENERATOR")['value']
			self.EVENTVALIDATION = html.find(id="__EVENTVALIDATION")['value']
		except Exception:
			pass
		self.prenesiSeznamPostaj()

	def prenesiSeznamPostaj(self):
		postajeUrl = "https://voznired.noleggio-bus.it/Postajalisca.aspx/GetCompletionList"
		podatki = {"prefixText": "", "count": 1000000}
		response = self.seja.post(postajeUrl, json=podatki)
		jsonData = response.json()
		self.postaje = jsonData['d']

	def seznamPostaj(self):
		if len(self.postaje) <= 0:
			self.prenesiSeznamPostaj()
		return self.postaje

	def obstajaPostaja(self, imePostaje):
		return imePostaje in self.postaje

	def prenesiSurovePodatke(self, vstopnaPostaja, izstopnaPostaja, datum):
		pretvorjenDatum = datum.strftime("%d.%m.%Y")
		vozniRedUrl = "https://voznired.noleggio-bus.it/VozniRed.aspx"

		podatki = {
			"ToolkitScriptManager1": "ToolkitScriptManager1|ButtonPrikazi",
			"ToolkitScriptManager1_HiddenField": ";;AjaxControlToolkit, Version=3.5.40412.0, Culture=neutral, PublicKeyToken=28f01b0e84b6d53e:en-US:cbf1c8cf-15a2-41c3-aef5-c56a1161b5d3:475a4ef5:5546a2b:d2e10b12:effe2a26:37e2e5c9:5a682656:12bbc599:addc6819:c7029a2:e9e598a9",
			"__VIEWSTATE": self.VIEWSTATE,
			"__VIEWSTATEGENERATOR": self.VIEWSTATEGENERATOR,
			"__EVENTVALIDATION": self.EVENTVALIDATION,
			"hiddenInputToUpdateATBuffer_CommonToolkitScripts": 0,
			"__ASYNCPOST": "false",
			"ButtonPrikazi": "Prikazi",
			"TextBoxVstop": vstopnaPostaja,
			"TextBoxIzstop": izstopnaPostaja,
			"TextBoxDatum": pretvorjenDatum
		}
		response = self.seja.post(vozniRedUrl, data=podatki)
		html = BeautifulSoup(response.text, "html.parser")
		return html

	def prenesiVozniRed(self, vstopnaPostaja, izstopnaPostaja, datum):
		html = self.prenesiSurovePodatke(vstopnaPostaja, izstopnaPostaja, datum)

		# Ce ne najdemo voznega reda, je prikazana tabela kontrola vnosa
		if html.find("table", {"id": "TableKontrolaVnosa"}):
			return []

		tabela = html.find("table", {"id": "TableVozniRed"})
		vrstice = tabela.findAll("tr")

		# Dobimo naslove vrstic (prevoznik, prihod, odhod, ...)
		#nasloviVrstic = [stolpec.text.lower() for stolpec in vrstice[0].findAll("td")]
		# Naslovi vrstic so vedno enaki
		nasloviVrstic = ["prevoznik", "odhod", "prihod", "trajanje", "razdalja", "peron", "cena"]

		# Vse podatke shranimo v tabelo
		prevoziPodatki = []

		for vrstica in vrstice[1:]:
			besediloStolpcev = [stolpec.text for stolpec in vrstica.findAll("td")]
			
			potUrl = ""
			link = vrstica.find("a")
			if "onclick" in link.attrs:
				izlusceni_podatki = []

				pattern = re.compile(r"ShowPotekVoznje\((.*)\);", re.IGNORECASE)
				atribut = link['onclick']
				rezultati = pattern.search(link['onclick'])
				if rezultati:
					podatki = re.split(r",\s?", rezultati.group(1))
					for podatek in podatki:
						izlusceni_podatki.append(podatek.replace("'", "").strip())
				potUrl = "http://voznired.avrigo.si/PotekVoznje.aspx?REG_ISIF={}&OVR_SIF={}&LIS_ZAPZ={}&LIS_ZAPK={}&VVLN_ZL={}".format(izlusceni_podatki[1], izlusceni_podatki[2], izlusceni_podatki[3], izlusceni_podatki[4], izlusceni_podatki[5])
		
			slovarPodatkov = dict(zip(nasloviVrstic, besediloStolpcev))
			slovarPodatkov["_url"] = potUrl
			
			# Ura prihoda in odhoda morata biti v datetime obliki
			uraPrihoda = datetime.datetime.strptime(slovarPodatkov["prihod"], "%H:%M")
			casPrihoda = datum.replace(hour=uraPrihoda.hour, minute=uraPrihoda.minute)

			uraOdhoda = datetime.datetime.strptime(slovarPodatkov["odhod"], "%H:%M")
			casOdhoda = datum.replace(hour=uraOdhoda.hour, minute=uraOdhoda.minute)

			# Preverimo ali je ura prihoda pred uro odhoda, saj je to nemogoce
			# Ce se to zgodi, pristejemo casu prihoda 1 dan
			if uraOdhoda > uraPrihoda:
				casPrihoda = casPrihoda + datetime.timedelta(days = 1)

			slovarPodatkov["odhod"] = casOdhoda
			slovarPodatkov["prihod"] = casPrihoda

			# Spustimo podatke, ki jih ne potrebujemo
			del slovarPodatkov["trajanje"]

			# Popravimo razdaljo in ceno v stevila
			slovarPodatkov["cena"] = slovarPodatkov["cena"].replace("EUR", "").strip().replace(",", ".")
			slovarPodatkov["cena"] = float(slovarPodatkov["cena"])

			slovarPodatkov["razdalja"] = slovarPodatkov["razdalja"].replace("km", "").strip()
			slovarPodatkov["razdalja"] = float(slovarPodatkov["razdalja"])

			prevoziPodatki.append(slovarPodatkov)

		return prevoziPodatki

	def vmesnePostaje(self, prevoz):
		vmesne_postaje = []

		# Url pridobimo iz prevoza
		response = self.seja.get(prevoz["_url"])

		# Avrigo nam vrne json rezultat, v katerem je html, kar je neumno, a deluje
		html = BeautifulSoup(response.json()["html"], "html.parser")

		# Najdemo tabelo in vrstice
		tabela = html.find("table", {"id": "Table1"})
		vrstice = tabela.find_all("tr")
		
		for vrstica in vrstice:
			# Najdemo stolpce v vsaki vrstici
			stolpci = vrstica.find_all("td", {"class": "TabelaPostaje"})
			if len(stolpci) < 4:
				continue

			# Preberemo le besedilo iz stolpcev
			podatki = [stolpec.text for stolpec in stolpci] 

			# Vse ure pripisemo pravemu datumu
			# TODO: ce je avtobus tak, da se vozi dva dni, potem je tukaj malo problematicno
			datumPrihoda = prevoz['odhod']
			try:
				uraPrihoda = datetime.datetime.strptime(podatki[1], "%H:%M")
				datumPrihoda = datumPrihoda.replace(hour=uraPrihoda.hour, minute=uraPrihoda.minute)

				if datumPrihoda < prevoz['odhod']:
					datumPrihoda = datumPrihoda + datetime.timedelta(days = 1)
			except Exception:
				pass

			vmesne_postaje.append({
				"postaja": podatki[0], # ime postaje
				"cas_prihoda": datumPrihoda
			})

		return vmesne_postaje