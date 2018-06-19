from ..plugin import Plugin
from ..models import Iskanje
import datetime

class Iskanja(Plugin):
	
	def __init__(self, database, options={}):
		self.database = database
		self.options = options

	def renderView(self, data):
		iskanja = self.database.session.query(Iskanje).order_by(Iskanje.datum_iskanja.desc())
		template = self.getTemplate("templates/view.html")
		return template.render(iskanja=iskanja)

	def renderCard(self):
		stevilo_iskanj = self.database.session.query(Iskanje).count()
		template = self.getTemplate("templates/card.html")
		return template.render(stevilo_iskanj=stevilo_iskanj)

	def returnJsonData(self, request):
		iskanja = self.database.session.query(Iskanje).order_by(Iskanje.datum_iskanja.desc())
		return [iskanje.toDictionary() for iskanje in iskanja]