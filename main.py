from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import datetime, dateutil.parser
import glob, os, importlib, inspect

from concurrent.futures import ThreadPoolExecutor

import sys

# Moji importi
from plugins.models import Base, Obvestilo, Iskanje, Prevoz
from prevozniki.avrigo import Avrigo
from prevozniki.alpetour import Alpetour
from prevozniki.apms import AvtobusniPrevozMurskaSobota
from prevozniki.apljubljana import APLjubljana
from prevozniki.arriva import Arriva

# Ustvarimo instanco flask razreda
app = Flask(__name__, static_url_path='')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
database = SQLAlchemy(app)

# Objekt, ki bo hranil stara iskanja, v prihodnosti POPRAVI
iskanja = {}

# Ustvarimo objekte, za prenos podatkov o voznih redih
prevozniki = [Avrigo(), Alpetour(), AvtobusniPrevozMurskaSobota(), Arriva(), APLjubljana()]

@app.before_first_request
def setup():
	#Base.metadata.drop_all(bind=database.engine)
	Base.metadata.create_all(bind=database.engine)
	database.session.commit()

# PLUGIN SISTEM BORIS!
availablePlugins = glob.glob("plugins/**/*.py")
enabledPlugins = {}

def getPluginName(pluginPath):
	pluginName = os.path.basename(pluginPath)
	if ".py" in pluginName:
		pluginName = pluginName.replace(".py", "")
	return pluginName

def getMainClass(plugin, pluginName):
	allClasses = inspect.getmembers(plugin, inspect.isclass)
	if len(allClasses) > 0:
		mainClass = None
		for className in allClasses:
			if className[0] == pluginName:
				mainClass = className[1]
				return mainClass

def importPlugin(pluginPath):
	# Get plugin name and print debug info
	pluginName = getPluginName(pluginPath)
	absolutePath, filename = os.path.split(pluginPath)

	print(" - Importing plugin {}".format(pluginName))

	# Import plugin from path
	importedPlugin = importlib.import_module("plugins.{}.{}".format(pluginName, pluginName))

	# Get main class from plugin
	mainClass = getMainClass(importedPlugin, pluginName)
	if mainClass:
		# Create object from class
		pluginObject = mainClass(database)
		pluginObject.absolutePath = absolutePath
		return pluginObject

# Import plugins
"""print("Importing plugins")
for pluginPath in availablePlugins:
	pluginName = getPluginName(pluginPath)
	# Create plugin object
	importedPlugin = importPlugin(pluginPath)
	enabledPlugins[pluginName] = importedPlugin

# Tukaj dodamo se lastno kodo za plugine
@app.route("/admin")
def sendAdminDashboard():
	return render_template('admin_dashboard.html', plugins=[enabledPlugins[p] for p in enabledPlugins])

@app.route("/admin/plugin/<pluginName>", methods=["GET", "POST"])
def sendPluginPage(pluginName):
	if pluginName in enabledPlugins:
		plugin = enabledPlugins[pluginName]
		html = plugin.renderView(request.values)
		return render_template('admin_plugin.html', plugin=plugin, pluginView=html, plugins=[enabledPlugins[p] for p in enabledPlugins])
	return redirect(url_for('sendAdminDashboard'))

@app.route("/admin/plugin/<pluginName>/data", methods=["GET", "POST"])
def sentPluginData(pluginName):
	if pluginName in enabledPlugins:
		plugin = enabledPlugins[pluginName]
		data = plugin.returnJsonData(request.values)
		return jsonify(data)
	return jsonify({})
"""

# ENDPOINTI PO DEFINICIJI V DATOTEKI README.md

# Definiramo endpoint za obvestila
@app.route("/obvestilo", methods=["GET"])
def najdi_obvestila():
	# Preberemo zadnji datum obvestila
	zadnji_datum = request.args.get('od')

	# Ce zadnjega datuma ni, potem vrnemo kar zadnje obvestilo
	if zadnji_datum == None:
		obvestilo = database.session.query(Obvestilo).order_by(Obvestilo.datum_objave.desc()).first()
		return jsonify(obvestilo.toDictionary())

	# Sicer pretvorimo datum iz oblike isoformat v datetime objekt
	datum = dateutil.parser.parse(zadnji_datum)

	# Sicer najdemo zadnje obvestilo po dolocenem datumu
	obvestila = database.session.query(Obvestilo).filter(Obvestilo.datum_objave > datum)
	obvestilo = obvestila.order_by(Obvestilo.datum_objave.desc()).first()
	if obvestilo:
		return jsonify(obvestilo.toDictionary())

	# Vrnemo prazen objekt, obvestila ni
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
	# Ce datuma ni, vstavimo danasnji datum, sicer ga pretvorimo
	vstopna_postaja = request.args.get('vstopna_postaja', None)
	izstopna_postaja = request.args.get('izstopna_postaja', None)
	datum = request.args.get('datum', None)

	print("Request data: vstopna_postaja: {}, izstopna_postaja: {}, datum: {}".format(vstopna_postaja, izstopna_postaja, datum))

	pretvorjen_datum = datetime.datetime.now()
	if datum != None:
		pretvorjen_datum = datetime.datetime.strptime(datum, "%d.%m.%Y")
	else:
		datum = pretvorjen_datum.strftime("%d.%m.%Y")

	print("Search from {}: {} -> {}".format(request.remote_addr, vstopna_postaja, izstopna_postaja))

	# Preverimo, ali je to iskanje ze v tabeli iskanj
	zadetek = database.session.query(Iskanje).filter_by(vstopna_postaja=vstopna_postaja, izstopna_postaja=izstopna_postaja, datum=pretvorjen_datum.date()).first()
	# Ce je zadetek ze v tabeli, ne prenasamo voznega reda temvec kar vrnemo te podatke
	if zadetek != None:
		print("Vozni red je ze najden")
		vozni_red = [zadetek.toDictionary() for zadetek in zadetek.prevozi]
		for prevoz in vozni_red:
			prevoz["odhod"] = prevoz["odhod"].strftime("%H:%M")
			prevoz["prihod"] = prevoz["prihod"].strftime("%H:%M")
		return jsonify(vozni_red)

	iskanje = Iskanje(vstopna_postaja=vstopna_postaja, izstopna_postaja=izstopna_postaja, datum=pretvorjen_datum, datum_iskanja=datetime.datetime.utcnow())

	skupni_vozni_red = []
	with ThreadPoolExecutor(max_workers=len(prevozniki)) as pool:
		for prevoznik in prevozniki:
			if prevoznik.obstajaPostaja(vstopna_postaja) and prevoznik.obstajaPostaja(izstopna_postaja):
				rezultat = pool.submit(prevoznik.prenesiVozniRed, vstopna_postaja, izstopna_postaja, pretvorjen_datum)
				skupni_vozni_red.extend(rezultat.result())

	# Uredimo vozni red po datumih
	skupni_vozni_red.sort(key=lambda x: x["odhod"])

	# Dodamo prevoze pod iskanje v bazo podatkov
	for prevoz in skupni_vozni_red:
		prevozTabela = Prevoz(
			prihod=prevoz["prihod"],
			odhod=prevoz["odhod"],
			peron=prevoz["peron"],
			prevoznik=prevoz["prevoznik"],
			cena=prevoz["cena"],
			razdalja=prevoz["razdalja"]
		)
		iskanje.prevozi.append(prevozTabela)

	database.session.add(iskanje)
	database.session.commit()

	# Spremenimo ure nazaj v normalno obliko
	for prevoz in skupni_vozni_red:
		prevoz["odhod"] = prevoz["odhod"].strftime("%H:%M")
		prevoz["prihod"] = prevoz["prihod"].strftime("%H:%M")

	return jsonify(skupni_vozni_red)

if __name__ == '__main__':
	port = 7000
	if len(sys.argv) >= 2:
		port = int(sys.argv[1])
	app.run(host="0.0.0.0", port=port, debug=True, threaded=True)
