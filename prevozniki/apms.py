# -*- coding: utf-8 -*-
from .prevoznik import Prevoznik
import requests
from bs4 import BeautifulSoup
import datetime

class AvtobusniPrevozMurskaSobota(Prevoznik):
	
	def __init__(self):
		self.seja = requests.Session()
		self.postaje = ["Murska Sobota BTC /Hofer", "Adrijanci", "Andrejci GD", "Andrejci st.š.", "Andrejci Trokšarov breg K", "Ankaran K", "Baby center", "Bakovci", "Bakovci center", "Bakovci K Gost.Rajh", "Bakovci Mladinska ul.", "Bakovci ul.ob Muri ", "Banovci", "Beli Potok Laznik", "Beltinci", "Beltinci K", "Beltinci pok.", "Beltinci Š", "Benedikt v Sl.G.", "Berkovci", "Berkovci GD", "Beznovci GD", "Beznovci K", "Biserjane", "Blagovica", "Bodislavci K", "Bodonci breg", "Bodonci cerkev", "Bodonci gost.JASA", "Bodonci sp.", "Bogojina", "Bogojina Š", "Bohova", "Bolehnečici", "Bolk", "Boračeva", "Boračeva breg", "Boreča K", "Boreča križarka", "Borejci", "Branoslavci", "Bratonci K", "Bratonci kapela", "Brezovci", "Brezovica K/Lendavi", "BTC", "Bučečovci", "Budinci", "Cankova", "Celje AP", "Cezanjevci", "Cven", "Cven Kuplen", "Cven novi", "Čakova", "Čentiba K ( Mlin )", "Čepinci Djapkini", "Čepinci GD", "Čepinci Krapati", "Čepinci Špic breg karavl", "Čepinci špic breg Vožarn", "Černelavci", "Černelavci Liškova", "Černelavci Titan", "Čikečka vas", "Črenšovci", "Črenšovci Sabo", "Črni Kal sp.", "Črni Kal zg.", "Črni les", "Dankovci GD", "Dankovci most", "D.Bistrica K", "D.Bistrica pok.", "Dekani", "Divača", "D.Lakoš", "Dob/Domžalah", "Dobrovnik", "Dobrovnik G", "Dokležovje", "Dokležovje K", "Dolenci", "Dolenci 41", "Dolga vas/Lendavi", "Dolič g/Goričkem", "Dolič/Goričkem", "Dolina K/Lendavi", "Dolina pok./Lendavi", "Dol.Slaveči mlin", "Dol.Slaveči Sijarto", "Dol.Slaveči VD", "Domajinci GD", "Domajinci jez K", "Domajinci pokop.", "Domanjševci garaža", "Domanjševci K", "Domžale K", "Dragotinci", "Dragučova", "D.Slaveči g.Forjanič", "Fikšinci", "Fikšinci 3", "Filovci", "Fokovci Gaj", "Fokovci Š", "Fokovci trg.", "Fram K", "Frankolovo", "Gaberje Š./Lendavi", "Gaberje/Lendavi", "Gančani", "Gančani Hraščica", "Gančani pokop.", "Garaža(Bakovska 29A,)", "G.Bistrica", "G.Črnci", "G.Črnci K", "Gederovci", "Genterovci", "Gerlinci ", "Gerlinci 1", "Gibina", "G.Lakoš", "Godemarci kapela", "Gomilica", "Gomilica K Lipa", "Gomilica trafo.šv", "Gomilica trgovina", "Gomilsko", "Gorica zg./Puconcih", "Gorica/Puconcih", "Gor.Slaveči g.Sabo", "Gor.Slaveči most", "G.Petrovci K", "G.Petrovci K Adrijanci", "G.Petrovci meja", "G.Petrovci Š", "Grabe pri Ljutomeru K", "Grabonoš", "Grad sp./Goričkem", "Grad zg./Goričkem", "G.Radgona", "G.Radgona Arcont", "Gradišče K/M.Sob.", "Gradišče/M.Sob.", "Grlava", "Hodoš", "Hotiza", "Hotiza Grede", "Hotiza K", "Hrastje-Mota", "Hrastje-Mota K", "Hrastovec v Sl.G.", "Hrašče", "Hruševje", "Ihova", "Iljaševci", "Ivanci GD", "Ivanovci K", "Ivenca", "Izola", "Ižakovci", "Ižakovci kapela", "Jamna", "Jamna Kocbek", "Janžev Vrh GD", "Jelševica", "Kamovci", "Kančevci", "Kapca", "Kapela", "Kapela Kocjan", "Kapela pokop.", "Kastelec K", "Ključarovci pri Ljut.", "Ključarovci pri Ljut.K", "Klopce/Sl.Bist.", "Kobilje ", "Kobilje logarnica", "Kobilje meja", "Kobilščak", "Kokoriči", "Koper", "Korovci kapela", "Košaki Kos", "Kovačevci Lapcovi", "Kovačevci Vinšček", "Kozina", "Krajna", "Kramarovci K", "Krapje", "Krapje K", "Krašči", "Krašči jezero", "Krašči žaga", "Krašči 64", "Krašnja", "Krištanci", "Križevci cerkev", "Križevci nog.igr.", "Križevci pri Ljut.", "Križevci 166", "Krog", "Krog g.Weindorfer", "Kroška ulica", "Kruplivnik", "Kruplivnik Beli križ", "Kukeč 50", "Kupšinci K", "Kupšinci most", "Kupšinci zvonik", "Kuzma", "Kuzma K Trdkova", "Latkova vas", "Laže K", "Lemerje", "Lenart v Sl.G.", "Lendava", "Lendava H.Lipa", "Lendava mlin", "Lendava naselje", "Lendava ŽP", "Lendavska ul.1", "Lendavska ul.2/VAGA", "Lendavska ul.3/trg.LIDL", "Lipa/Beltincih", "Lipovci K", "Lipovci križ", "Ljubljana AP", "Ljubljana Hajdrihova", "Ljubljana stad.", "Ljubljana Tobačna", "Ljutomer", "Ljutomer Tehnostroj", "Ljutomer ŽP", "Ločica pri Vranskem", "Logarovci kapela", "Logarovci 6", "Lomanoše bistro", "Lomanoše 5", "Lormanje K", "Lukavci", "Lukovica pri Domžalah", "Mačkovci", "Mačkovci most", "Maribor AP", "Maribor Fontana", "Maribor Prim.ul.", "Maribor STŠ", "Maribor tov.Himo", "Maribor trans.Lening.ul.", "Markišavci", "Markovci breg/Goričkem", "Markovci cerkev/Goričkem", "Markovci K/Goričkem", "Martinje", "Martinje Čerpnjak", "Martjanci", "Matjaševci", "Mele", "Melinci", "Melinci zg.kunec", "Mercator cent/Plese 1 M.Sobota", "Mlajtinci", "Močna", "Moravci toplice/Sl.G.K", "Moravske Toplice ", "Moravske toplice K", "Morje", "Mostje Banuta/Lendavi", "Mostje staro/Lendavi", "Mostje/Lendavi", "Moščanci", "Mota", "M.Otok", "Motovilci GD", "Motovilci K", "Motvarjevci K.Čik.vas", "Motvarjevci poses.", "M.Šalovci", "Murska Sobota Agroservis", "Murska Sobota AP", "Murska Sobota Bakša", "Murska Sobota CPŠ", "Murska Sobota Ekonom. Š ", "Murska Sobota Gaj", "Murska Sobota Gregorčič.", "Murska Sobota Gregorčič I.", "Murska Sobota Gregorčičeva I", "Murska Sobota Indus.", "Murska Sobota Maximus ", "Murska Sobota Mura", "Murska Sobota OŠ I", "Murska Sobota OŠ III", "Murska Sobota Polanič", "Murska Sobota Polanič trg.", "Murska Sobota TUŠ", "Murska Sobota ZD", "Murski Črnci", "Murski Črnci K", "Murski Petrovci", "Nedelica", "Nedelica Farkašovci", "Nedelica Ginjoc", "Nedelica hiš.št.50", "Nedelica I šv", "Nedelica most", "Nedelica pokop.", "Nemčavci", "Nemščak", "Neradnovci", "Noršinci pri Ljut.", "Noršinci/M.Sob.", "Nuskova", "Odranci", "Odranci cerkev", "Okoslavci", "Okoslavci breg", "Otovci GD", "Panovci VD", "Pečarovci GD", "Pernica", "Pernica jezero", "Pertoča", "Pertoča cerkev", "Pertoča Halb K", "Pertoča 85", "Peskovci Kompas", "Pesniški Dvor", "Petanjci G", "Petanjci GD", "Petanjci kapela", "Petišovci", "Petišovci kolonija", "Petišovci 13", "Petrinje", "Petrovče", "Pince", "Pince Marof", "Piran", "Plitvički Vrh", "Podgrad/G.Radgoni", "Podmilj", "Polana/M.Sob.", "Pordašinci", "Portorož", "Postojna", "Postojna LIV", "Poznanovci", "Predanovci", "Prekopa/Vranskem", "Preloge/Sl.Konj.", "Prevoje", "Prežihova ul.", "Prihova K", "Prosečka vas", "Prosenjakovci", "Prosenjakovci dol", "Prosenjakovci K", "Prosenjakovci Š", "Puconci cerkev", "Puconci K", "Puconci most", "Puconci Š", "Puževci", "Puževci GD", "Puževci gor.", "Radenci", "Radenski Vrh", "Radizel", "Radizel 63", "Radmožanci", "Radoslavci kapela", "Radoslavci Vogričevci K", "Radovci Ficko", "Radovci Kralešček", "Rakičan", "Rakičan bol.", "Rankovci", "Ratkovci K", "Ratkovci trg.", "Razdrto K", "Razdrto tri hiše", "Razkrižje", "Renkovci Križ šv", "Renkovci most", "Renkovci trg.", "Renkovci vas K šv", "Rihtarovci", "Rižana", "Rogašovci Rajse", "Rogašovci Š", "Ropoča", "Ropoča K", "Ropoča kapela", "Rožički Vrh", "Rožički Vrh GD", "Ruperče", "Ruperče Ložane", "Ruše Š", "Satahovci", "Satahovci pokop.", "Sebeborci K Ivanovci", "Sebeborci VD", "Selo cerkev/M.Sob.", "Selo Rotunda", "Selo Vršič/M.Sob.", "Senožeče", "Serdica", "Skakovci", "Sl.Bistrica", "Slivnica pri Mar.", "Sl.Konjice", "Slovenska ul.1/Blagovnica", "Slovenska ul.2/Mestna občina", "Sodišinci", "Sotina ", "Sotina 1", "Sp.Hoče K", "Sp.Loke/Blagovici", "Sp.Ložnica/Sl.Bist.K", "Sp.Ščavnica", "Sp.Žerjavci", "Sr.Bistrica", "Stanjevci", "St.Nova vas", "Stranice K", "Strehovci", "Stročja vas", "Strukovci G", "Strukovci gor.", "Strunjan", "Sv.Jurij ob Ščavnici", "Sv.Jurij/Goričkem", "Šafarsko", "Šalamenci bife", "Šalamenci Bor", "Šalamenci g.Gumilar", "Šalinci", "Šalovci K", "Šalovci Kutuš", "Šalovci pokop.", "Šalovci zvo.", "Šempeter v Savinj.d.SIP", "Šentožbolt", "Šentrupert/Savinj.d.", "Šratovci", "Šulinci GD", "Šulinci K", "Tabor/Vranskem K", "Tepanje", "Tešanovci Dajč", "Tešanovci dol.", "Tešanovci kapela", "Tišina", "Tomšičeva ul.1", "Tomšičeva ul.2/dijaški dom", "Topolovci", "Trdkova", "Trimlini", "Trnje K/Lendavi", "Trnje trg./Lendavi", "Trojane", "Tropovci", "Trstenik/Sl.G.", "Trstenjakova ul.1/trgovina", "Trstenjakova ul.2/OŠIII", "Turjanci", "Turjanski Vrh", "Turnišče cerkev", "Turnišče Š", "Turnišče šola", "Ul.Mikloša Kuzmiča I", "Ul.Mikloša Kuzmiča II", "Ul.Štefana Kuzmiča", "Ul.Zorana Velnarja", "Vadarci", "Vadarci Drvarčov breg", "Vanča vas Jaušovo", "Vaneča", "Vaneča g.Beznec", "Vaneča most", "Večeslavci", "Večeslavci Baraš", "Večeslavci K", "Večeslavci Rompovci", "Večeslavci 29(Vratošov breg)", "Veržej", "Veržej Bobnjar", "Veščica Novak/Ljut.", "Veščica Redič/M.Soboti", "Veščica/Ljut.", "Veščica/M.Soboti", "Vidonci", "Vidonci K Kovačevci", "Vir/Domžalah", "Višnja vas", "Vogričevci", "Vojnik", "Vosek", "V.Polana", "Vransko", "Vrhole pri Sl.Konj.", "Vučja Gomila K", "Vučja Gomila 150", "Vučja Gomila 8", "Vučja vas", "Zenkovci", "Zg.Polskava", "Zreče K", "Žalec", "Ženavlje", "Ženjak", "Žihlava", "Žihlava trg.", "Žitkovci", "Žižki GD"]
		
	def seznamPostaj(self):
		return self.postaje

	def obstajaPostaja(self, imePostaje):
		return imePostaje in self.postaje

	def prenesiSurovePodatke(self, vstopnaPostaja, izstopnaPostaja, datum):
		if type(datum) is datetime.datetime:
			datum = datum.strftime("%d.%m.%Y")
		
		vozniRedUrl = "https://www.apms.si/response.ajax.php?com=voznired&task=get"

		podatki = {
			"datum": datum,
			"postaja_od": vstopnaPostaja,
			"postaja_do": izstopnaPostaja
		}
		response = self.seja.post(vozniRedUrl, data=podatki)
		return response.json()

	def prenesiVozniRed(self, vstopnaPostaja, izstopnaPostaja, datum):
		podatki = self.prenesiSurovePodatke(vstopnaPostaja, izstopnaPostaja, datum)
		prevoziPodatki = []
		
		if podatki == None:
			return prevoziPodatki

		for vrstica in podatki:

			uraPrihoda = datetime.datetime.strptime(vrstica["prihod"], "%H:%M")
			uraOdhoda = datetime.datetime.strptime(vrstica["odhod"], "%H:%M")

			# Cas prihoda in odhoda izracunamo glede na trenutni datum in vrnjeno uro
			casPrihoda = datum.replace(hour=uraPrihoda.hour, minute=uraPrihoda.minute)
			casOdhoda = datum.replace(hour=uraOdhoda.hour, minute=uraOdhoda.minute)
			
			# Ceno prevoza in razdaljo vrnemo kot decimalno stevilo
			cena = float(vrstica["cena"].strip())
			razdalja = float(vrstica["km"])

			prevoz = {
				"prihod": casPrihoda,
				"odhod": casOdhoda,
				"peron": "",
				"prevoznik": vrstica["prevoznik"],
				"cena": cena,
				"razdalja": razdalja
			}

			prevoziPodatki.append(prevoz)

		return prevoziPodatki