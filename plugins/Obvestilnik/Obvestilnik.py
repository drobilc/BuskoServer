from ..plugin import Plugin
from ..models import Obvestilo
import datetime

class Obvestilnik(Plugin):
	
	def __init__(self, database, options={}):
		self.database = database
		self.options = options

	def renderView(self, data):
		if "naslov" in data and "besedilo" in data:
			naslov = data["naslov"]
			besedilo = data["besedilo"]

			obvestilo = Obvestilo(naslov=naslov, besedilo=besedilo, datum_objave=datetime.datetime.utcnow())
			self.database.session.add(obvestilo)
			self.database.session.commit()

		template = self.getTemplate("templates/view.html")
		return template.render()

	def renderCard(self):
		zadnjeObvestilo = self.database.session.query(Obvestilo).order_by(Obvestilo.datum_objave.desc()).first()
		template = self.getTemplate("templates/card.html")
		return template.render(obvestilo=zadnjeObvestilo)

	def returnJsonData(self, request):
		return None