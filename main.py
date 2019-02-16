from flask import Flask, request, jsonify, render_template
from flask.json import JSONEncoder
import datetime, dateutil.parser
import glob, os, importlib, inspect
import sys
from pymongo import MongoClient
from bson.objectid import ObjectId
from concurrent.futures import ThreadPoolExecutor

# Moji importi
from prevozniki.avrigo import Avrigo
from prevozniki.alpetour import Alpetour
from prevozniki.apms import AvtobusniPrevozMurskaSobota
from prevozniki.apljubljana import APLjubljana
from prevozniki.arriva import Arriva

class CustomJSONEncoder(JSONEncoder):

	def default(self, obj):
		if isinstance(obj, ObjectId):
			return str(obj)
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

# Ustvarimo objekte, za prenos podatkov o voznih redih
prevozniki = [Avrigo(), Alpetour(), AvtobusniPrevozMurskaSobota(), APLjubljana(), Arriva()]

# V slovarju prevoznikov imamo prevoznike shranjene glede na imena razredov
slovar_prevozniki = {}
for prevoznik in prevozniki:
	slovar_prevozniki[type(prevoznik).__name__] = prevoznik

def error(number, message, icon="/images/default_error.png"):
	return jsonify({
		"error": number,
		"message": message,
		"icon": icon
	})

# Definiramo endpoint za obvestila
@app.route("/obvestilo", methods=["GET"])
def najdi_obvestila():
	return jsonify(None)

def izracunajPrioritetoInIkono(iskanaPostaja, imePostaje):
	prioriteta = 0
	ikona = None
	if "AP" in imePostaje:
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
@app.route("/postaja", methods=["GET"])
def seznam_postaj():
	iskanje = request.args.get('iskanje')
	limit = request.args.get('limit')

	skupne_postaje_prevozniki = {}
	for prevoznik in prevozniki:
		prevoznik_postaje = prevoznik.seznamPostaj()
		if iskanje:
			prevoznik_postaje = filter(lambda ime: iskanje.lower() in ime.lower(), prevoznik_postaje)
		for postaja in prevoznik_postaje:
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
@app.route("/vozni_red", methods=["GET"])
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
		for prevoz in najdeni_prevozi:
			prevoz['odhod'] = prevoz['odhod'].strftime('%H:%M')
			prevoz['prihod'] = prevoz['prihod'].strftime('%H:%M')
		return jsonify(najdeni_prevozi)
	
	# Prevoza nismo se nasli v bazi, poiscemo ga
	skupni_vozni_red = []

	ustrezni_prevozniki = []
	for prevoznik in prevozniki:
		if prevoznik.obstajaPostaja(vstopna_postaja) and prevoznik.obstajaPostaja(izstopna_postaja):
			ustrezni_prevozniki.append(prevoznik)

	if len(ustrezni_prevozniki) <= 0:
		return error(406, "Med izbranimi postajami ne vozi noben izmed prevoznikov")

	# Nad vsemi objekti skupaj izvedemo iskanje, tako pohitrimo izvajanje
	with ThreadPoolExecutor(max_workers=len(ustrezni_prevozniki)) as pool:
		for prevoznik in ustrezni_prevozniki:
			rezultat = pool.submit(prevoznik.prenesiVozniRed, vstopna_postaja, izstopna_postaja, pretvorjen_datum)
			najdeni_prevozi = rezultat.result()

			# Vsakemo prevozu dodamo se ime internega razreda za pretvorbo nazaj ce bo potrebno
			for prevoz in najdeni_prevozi:
				prevoz["_prevoznik"] = type(prevoznik).__name__
				prevoz["_id"] = ObjectId()
			
			skupni_vozni_red.extend(najdeni_prevozi)

	# Prenesli smo vse vozne rede prevoznikov, uredimo jih po uri odhoda
	skupni_vozni_red.sort(key=lambda x: x["odhod"])

	for prevoz in skupni_vozni_red:
		prevoz["vstopna_postaja"] = vstopna_postaja
		prevoz["izstopna_postaja"] = izstopna_postaja

	prevozi.insert_many(skupni_vozni_red)

	for prevoz in skupni_vozni_red:
		prevoz['odhod'] = prevoz['odhod'].strftime('%H:%M')
		prevoz['prihod'] = prevoz['prihod'].strftime('%H:%M')

	return jsonify(skupni_vozni_red)

@app.route("/prevoz", methods=["GET"])
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

	# Case pretvorimo iz datetime objekta v niz
	for postaja in vmesne_postaje:
		postaja['cas_prihoda'] = postaja['cas_prihoda'].strftime('%H:%M')

	najden_prevoz['odhod'] = najden_prevoz['odhod'].strftime('%H:%M')
	najden_prevoz['prihod'] = najden_prevoz['prihod'].strftime('%H:%M')

	return jsonify(najden_prevoz)

if __name__ == '__main__':
	port = 7000
	if len(sys.argv) >= 2:
		port = int(sys.argv[1])
	app.run(host="0.0.0.0", port=port, debug=True, threaded=True)
