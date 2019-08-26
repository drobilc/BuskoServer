from flask import Flask, request, jsonify, render_template
from flask.json import JSONEncoder
import datetime, dateutil.parser
import glob, os, importlib, inspect
import sys
import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from concurrent.futures import ThreadPoolExecutor

# Moji importi
from prevozniki.avrigo import Avrigo
from prevozniki.apms import AvtobusniPrevozMurskaSobota
from prevozniki.apljubljana import APLjubljana
from prevozniki.arriva import Arriva

class CustomJSONEncoder(JSONEncoder):

	def default(self, obj):

		# Mongo idje pretvorimo v nize
		if isinstance(obj, ObjectId):
			return str(obj)

		# Datume pretvorimo v ISO 8601
		if isinstance(obj, datetime.datetime):
			return obj.isoformat()

		return JSONEncoder.default(self, obj)

# Ustvarimo instanco flask razreda
app = Flask(__name__, static_url_path='')
app.json_encoder = CustomJSONEncoder

# Povezemo se na bazo podatkov
client = MongoClient('localhost', 27017)
database = client.busko

# V tabeli prevozi hranimo vse podatke o prevozih
prevozi = database.prevozi

# V tabeli iskanja hranimo vsako iskanje uporabnikov za analize
iskanja = database.iskanja

# V tabeli obvestila hranimo obvestila za uporabnike
obvestila = database.obvestila

# Ustvarimo objekte, za prenos podatkov o voznih redih
prevozniki = [Avrigo(), AvtobusniPrevozMurskaSobota(), APLjubljana(), Arriva()]

# V slovarju prevoznikov imamo prevoznike shranjene glede na imena razredov
slovar_prevozniki = {}
for prevoznik in prevozniki:
	slovar_prevozniki[type(prevoznik).__name__] = prevoznik

with open("zdruzevanje.json", encoding="utf8") as datoteka:
    preslikovalna_tabela = json.load(datoteka)

def preslikaj(postaja):
    preslikave = {}
    
    if postaja in preslikovalna_tabela:
        
        for preslikava in preslikovalna_tabela[postaja]:
            if preslikava["prevoznik"] not in preslikave:
                preslikave[preslikava["prevoznik"]] = []
            preslikave[preslikava["prevoznik"]].append(preslikava["postaja"])
        
        for prevoznik in slovar_prevozniki:
            if prevoznik not in preslikave:
                preslikave[prevoznik] = [postaja]
        
    else:
        for prevoznik in slovar_prevozniki:
            preslikave[prevoznik] = [postaja]
    return preslikave

def zdruzi_prevoze(prevozi):
	print(f"Zdruzujem {len(prevozi)} prevozov")
	if len(prevozi) == 1:
		return prevozi[0]
	
	nov_prevoz = prevozi[0]

	parametri = ["cena", "odhod", "prihod", "peron", "prevoznik", "razdalja"]
	for parameter in parametri:
		moznosti = [prevoz[parameter] for prevoz in prevozi if parameter in prevoz and prevoz[parameter]]

		if len(moznosti) < 1:
			continue
		
		# Ce je parameter stevilo, vzamemo najvecjo vrednost iz seznama
		if isinstance(moznosti[0], int) or isinstance(moznosti[0], float):
			nov_prevoz[parameter] = max(moznosti)
	
	# Na koncu zdruzimo se imena prevoznikov
	ime_prevoznika = ", ".join([prevoz['_prevoznik'] for prevoz in prevozi if parameter in prevoz and prevoz['prevoznik']])
	if len(ime_prevoznika) >= 30:
		ime_prevoznika = "{}...".format(ime_prevoznika[0:27])
	nov_prevoz['prevoznik'] = ime_prevoznika

	return nov_prevoz

def preveri_enakost(prvi, drugi):
	parametri = ["odhod", "prihod"]
	for parameter in parametri:
		if parameter in prvi and parameter in drugi and str(prvi[parameter]) != str(drugi[parameter]):
			return False
	return True

def zdruzi_enake(vozni_red):
	# Zdruzujemo po dva prevoza naenkrat - trenutnega in naslednjega
	# Zdruzimo prevoza, ki se ujemata v:
	#   * casu odhoda
	#   * casu prihoda

	nov_vozni_red = []

	trenutni_prevozi = []
	for i, prevoz in enumerate(vozni_red):
		# Ce v seznamu trenutnih prevozov se ni prevoza, ga dodamo in nadaljujemo
		if len(trenutni_prevozi) < 1:
			trenutni_prevozi.append(prevoz)
			continue
		
		if preveri_enakost(trenutni_prevozi[-1], prevoz):
			# Enaka sta, prevoz dodamo v trenutni_prevozi
			trenutni_prevozi.append(prevoz)
		else:
			# Prevoz ni enak, najprej zdruzimo vse prevoze v tabeli trenutni_prevozi
			nov_prevoz = zdruzi_prevoze(trenutni_prevozi)
			
			# Prevoz dodamo v nov vozni red
			nov_vozni_red.append(nov_prevoz)

			# Izpraznimo tabelo trenutni_prevozi
			trenutni_prevozi = []
	
	# Na koncu je lahko seznam trenutni_prevozi se vedno polna 
	if len(trenutni_prevozi) > 0:
		nov_prevoz = zdruzi_prevoze(trenutni_prevozi)
		nov_vozni_red.append(nov_prevoz)

	return nov_vozni_red

def error(number, message, icon="/images/default_error.png"):
	return jsonify({
		"error": number,
		"message": message,
		"icon": icon
	})

# Definiramo endpoint za obvestila
@app.route("/api/v2/obvestilo", methods=["GET"])
def najdi_obvestila():
	# Zadnje odprtje ni obvezno, ce ga ni, vrnemo None
	zadnje_odprtje = request.args.get('od')
	
	if not zadnje_odprtje:
		return jsonify(None)

	# Pretvorimo datum zadnjega odprtja v datetime objekt
	pretvorjen_datum = dateutil.parser.parse(zadnje_odprtje)

	# Poiscemo obvestila
	najdena_obvestila = obvestila.find({"datum_objave": {"$gt": pretvorjen_datum}}).sort("datum_objave", -1)

	if najdena_obvestila.count() > 0:
		return jsonify(najdena_obvestila[0])

	# Vrnemo zadnje obvestilo
	return jsonify(None)

def izracunajPrioritetoInIkono(iskanaPostaja, imePostaje):
	prioriteta = 0
	ikona = None
	if imePostaje in preslikovalna_tabela:
		prioriteta = 30
		ikona = "/images/star.png"
	elif "AP" in imePostaje:
		prioriteta = 20
		ikona = "/images/bus.png"
	elif "ŽP" in imePostaje:
		prioriteta = 20
		ikona = "/images/train.png"
	elif "pri" not in imePostaje and "/" not in imePostaje:
		prioriteta = 1
	if len(imePostaje) > 0:
		prioriteta  += int((len(iskanaPostaja) / len(imePostaje)) * 5)
	return {
		"prioriteta": prioriteta,
		"ikona": ikona
	}

# Definiramo endpoint za seznam postaj
@app.route("/api/v2/postaja", methods=["GET"])
def seznam_postaj():
	iskanje = request.args.get('iskanje')
	limit = request.args.get('limit')

	skupne_postaje_prevozniki = {}

	izlocene_postaje = {}
	# Dodamo najprej postaje iz preslikovalne tabele
	for postaja in preslikovalna_tabela:
		if iskanje.lower() in postaja.lower():
			skupne_postaje_prevozniki[postaja] = list(set([podatek['prevoznik'] for podatek in preslikovalna_tabela[postaja]]))
			
			for vnos in preslikovalna_tabela[postaja]:
				if vnos['prevoznik'] not in izlocene_postaje:
					izlocene_postaje[vnos['prevoznik']] = []
				izlocene_postaje[vnos['prevoznik']].append(vnos['postaja'])

	for prevoznik in prevozniki:
		prevoznik_postaje = prevoznik.seznamPostaj()
		if iskanje:
			prevoznik_postaje = filter(lambda ime: iskanje.lower() in ime.lower(), prevoznik_postaje)
			for postaja in prevoznik_postaje:

				# Preverimo ali je postaja izlocena, ce je jo preskocimo
				if prevoznik.__class__.__name__ in izlocene_postaje and postaja in izlocene_postaje[prevoznik.__class__.__name__]:
					continue
				
				if postaja not in skupne_postaje_prevozniki:
					skupne_postaje_prevozniki[postaja] = []
				
				skupne_postaje_prevozniki[postaja].append(prevoznik.__class__.__name__)

	imena_postaj = skupne_postaje_prevozniki.keys()
	vse_postaje = [{
		"ime": postaja,
		"prevozniki": skupne_postaje_prevozniki[postaja],
		"prioriteta": izracunajPrioritetoInIkono(iskanje, postaja)["prioriteta"],
		"ikona": izracunajPrioritetoInIkono(iskanje, postaja)["ikona"]
	} for postaja in imena_postaj]

	vse_postaje.sort(key=lambda postaja: postaja["prioriteta"], reverse=True)

	try:
		praviLimit = int(limit)
		vse_postaje = vse_postaje[0:praviLimit]
	except Exception:
		pass

	return jsonify(vse_postaje)

# Definiramo endpoint za vozne rede
@app.route("/api/v2/vozni_red", methods=["GET"])
def vozni_red():
	vstopna_postaja = request.args.get('vstopna_postaja', None)
	izstopna_postaja = request.args.get('izstopna_postaja', None)

	if vstopna_postaja is None or izstopna_postaja is None:
		return error(405, "Vstopna ali izstopna postaja je prazna")

	# Ce datuma ni, vstavimo danasnji datum, sicer ga pretvorimo
	datum = request.args.get('datum', None)

	pretvorjen_datum = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
	if datum != None:
		pretvorjen_datum = datetime.datetime.strptime(datum, "%d.%m.%Y")
	else:
		datum = pretvorjen_datum.strftime("%d.%m.%Y")

	# Iskanje poteka po naslednjem postopku:
	#   * najprej dodamo iskanje v bazo podatkov, skupaj s trenutnim casom
	#   * ce vozni red na dolocen dan ze obstaja, ga neposredno vrnemo
	#   * ce vozni red se ne obstaja, ga najprej prenesemo, dodamo v bazo in rezultat vrnemo

	# V tabelo iskanj vstavimo trenutno iskanje, to potrebujemo zaradi statistike
	iskanja.insert_one({
		"vstopna_postaja": vstopna_postaja,
		"izstopna_postaja": izstopna_postaja,
		"datum": pretvorjen_datum,
		"datum_iskanja": datetime.datetime.now()
	})

	# Poiscemo konec dneva
	konec_dneva = pretvorjen_datum + datetime.timedelta(days=1)
	konec_dneva.replace(hour=0, minute=0, second=0, microsecond=0) 
	
	# V bazi podatkov poiscemo vse prevoze ki so med datumom in koncem dneva
	najdeni_prevozi = prevozi.find({
		"$and": [
			{"vstopna_postaja": vstopna_postaja},
			{"izstopna_postaja": izstopna_postaja},
			{"odhod": {"$gt": pretvorjen_datum}},
			{"odhod": {"$lt": konec_dneva}}
		]
	})

	if najdeni_prevozi.count() > 0:
		najdeni_prevozi = list(najdeni_prevozi)
		# Prevoz je ze najden, vrnemo rezultat poizvedbe
		# Drugi problem je cas pri prevozih, imamo ga namrec v datetime objektu, radi bi pa imeli niz "HH:MM"
		rezultat = {
			"vstopna_postaja": vstopna_postaja,
			"izstopna_postaja": izstopna_postaja,
			"datum": datum,
			"prevozniki": list(set([prevoz['_prevoznik'] for prevoz in najdeni_prevozi])),
			"prevozi": zdruzi_enake(najdeni_prevozi)
		}
		return jsonify(rezultat)
	
	# Prevoza nismo se nasli v bazi, poiscemo ga
	skupni_vozni_red = []

	# Preslikava nam vrne za vsakega prevoznika seznam imen postaj, ki ustrezajo izbiri
	vstopna_preslikava = preslikaj(vstopna_postaja)
	izstopna_preslikava = preslikaj(izstopna_postaja)

	ustrezni_prevozniki = []

	for prevoznik in prevozniki:
		
		# Najdemo ustrezne vstopne in izstopne postaje za prevoznika
		vstopne_postaje = vstopna_preslikava[type(prevoznik).__name__]
		izstopne_postaje = izstopna_preslikava[type(prevoznik).__name__]
		
		# Preverimo, ali ima ta prevoznik sploh te postaje
		prave_vstopne_postaje = list(filter(lambda postaja: prevoznik.obstajaPostaja(postaja), vstopne_postaje))
		prave_izstopne_postaje = list(filter(lambda postaja: prevoznik.obstajaPostaja(postaja), vstopne_postaje))

		if len(prave_vstopne_postaje) > 0 and len(prave_izstopne_postaje) > 0:
			ustrezni_prevozniki.append({
				"prevoznik": prevoznik,
				"vstopne_postaje": prave_vstopne_postaje,
				"izstopne_postaje": izstopne_postaje
			})

	if len(ustrezni_prevozniki) <= 0:
		return error(406, "Med izbranimi postajami ne vozi noben izmed prevoznikov")

	# Nad vsemi objekti skupaj izvedemo iskanje, tako pohitrimo izvajanje
	with ThreadPoolExecutor(max_workers=8) as pool:
		for prevoznik in ustrezni_prevozniki:

			for najdena_vstopna_postaja in prevoznik['vstopne_postaje']:
				for najdena_izstopna_postaja in prevoznik['izstopne_postaje']:
			
					rezultat = pool.submit(prevoznik['prevoznik'].prenesiVozniRed, najdena_vstopna_postaja, najdena_izstopna_postaja, pretvorjen_datum)
					try:
						najdeni_prevozi = rezultat.result()
						# Vsakemo prevozu dodamo se ime internega razreda za pretvorbo nazaj ce bo potrebno
						for prevoz in najdeni_prevozi:
							prevoz["_prevoznik"] = type(prevoznik['prevoznik']).__name__
							prevoz["vstopna_postaja"] = vstopna_postaja
							prevoz["izstopna_postaja"] = izstopna_postaja
						
						skupni_vozni_red.extend(najdeni_prevozi)
					except Exception:
						pass

	# Prenesli smo vse vozne rede prevoznikov, uredimo jih po uri odhoda
	skupni_vozni_red.sort(key=lambda x: x["odhod"])

	if len(skupni_vozni_red) > 0:
		prevozi.insert_many(skupni_vozni_red)
	
	skupni_vozni_red = zdruzi_enake(skupni_vozni_red)

	rezultat = {
		"vstopna_postaja": vstopna_postaja,
		"izstopna_postaja": izstopna_postaja,
		"datum": datum,
		"prevozniki": [type(prevoznik['prevoznik']).__name__ for prevoznik in ustrezni_prevozniki],
		"prevozi": skupni_vozni_red
	}
	return jsonify(rezultat)

@app.route("/api/v2/prevoz", methods=["GET"])
def prevoz():
	# Preberemo id prevoza, ki ga uporabnik isce
	prevoz_id = request.args.get('id', None)

	# V podatkovni bazi poiscemo objekt prevoza glede na id
	najden_prevoz = prevozi.find_one({"_id": ObjectId(prevoz_id)})

	if not najden_prevoz:
		return error(404, "Prevoz z vpisanim identifikatorjem ne obstaja")

	# Preverimo ali obstaja prevoznik v slovarju prevoznikov
	if najden_prevoz['_prevoznik'] not in slovar_prevozniki:
		return error(502, "Prevoznik ne obstaja")

	# V primeru, da smo postaje ze prenesli, lahko objekt kar vrnemo
	if 'vmesne_postaje' in najden_prevoz:
		return jsonify(najden_prevoz)

	# Ce prevoznik obstaja, najdemo vmesne postaje
	vmesne_postaje = slovar_prevozniki[najden_prevoz['_prevoznik']].vmesnePostaje(najden_prevoz)

	# Objektu dodamo seznam vmesnih postaj
	najden_prevoz['vmesne_postaje'] = vmesne_postaje
	
	# Objekt shranimo nazaj v podatkovno bazo
	prevozi.save(najden_prevoz)

	return jsonify(najden_prevoz)

if __name__ == '__main__':
	port = 7000
	if len(sys.argv) >= 2:
		port = int(sys.argv[1])
	app.run(host="0.0.0.0", port=port, debug=True, threaded=True)
