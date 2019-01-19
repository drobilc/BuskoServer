from flask import Flask, request, jsonify, render_template
import datetime, dateutil.parser
import glob, os, importlib, inspect
import sys
from pymongo import MongoClient
from concurrent.futures import ThreadPoolExecutor

# Moji importi
from prevozniki.avrigo import Avrigo
from prevozniki.alpetour import Alpetour
from prevozniki.apms import AvtobusniPrevozMurskaSobota
from prevozniki.apljubljana import APLjubljana
from prevozniki.arriva import Arriva

# Ustvarimo instanco flask razreda
app = Flask(__name__, static_url_path='')

# Povezemo se na bazo podatkov
client = MongoClient('localhost', 27017)
database = client.busko
prevozi = database.prevozi
iskanja = database.iskanja

# Ustvarimo objekte, za prenos podatkov o voznih redih
prevozniki = [Avrigo(), Alpetour(), AvtobusniPrevozMurskaSobota(), Arriva(), APLjubljana()]

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

	# Poiscemo prevoz v mongo podatkovni bazi
	najden_prevoz = prevozi.find_one({
		"vstopna_postaja": vstopna_postaja,
		"izstopna_postaja": izstopna_postaja,
		"datum": pretvorjen_datum
	})

	if najden_prevoz:
		# Prevoz je ze najden, vrnemo rezultat poizvedbe
		# Tukaj pride do problema, ker ima prebran dokument iz mongo baze se id, ki ga je potrebno odstraniti
		najden_prevoz.pop('_id')
		# Drugi problem je cas pri prevozih, imamo ga namrec v datetime objektu, radi bi pa imeli niz "HH:MM"
		for prevoz in najden_prevoz['vozni_red']:
			prevoz['odhod'] = prevoz['odhod'].strftime('%H:%M')
			prevoz['prihod'] = prevoz['prihod'].strftime('%H:%M')
		# V trenutni razlicici se vrnemo seznam voznih redov, v prihodnosti bomo to zamenjali z najden_prevoz
		return jsonify(najden_prevoz['vozni_red'])
	
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
			skupni_vozni_red.extend(rezultat.result())

	# Prenesli smo vse vozne rede prevoznikov, uredimo jih po uri odhoda
	skupni_vozni_red.sort(key=lambda x: x["odhod"])

	# V bazo dodamo rezultat iskanja pod nov objekt
	prevozi.insert_one({
		"vstopna_postaja": vstopna_postaja,
		"izstopna_postaja": izstopna_postaja,
		"datum": pretvorjen_datum,
		"vozni_red": skupni_vozni_red
	})

	for prevoz in skupni_vozni_red:
		prevoz['odhod'] = prevoz['odhod'].strftime('%H:%M')
		prevoz['prihod'] = prevoz['prihod'].strftime('%H:%M')

	return jsonify(skupni_vozni_red)

if __name__ == '__main__':
	port = 7000
	if len(sys.argv) >= 2:
		port = int(sys.argv[1])
	app.run(host="0.0.0.0", port=port, debug=True, threaded=True)
