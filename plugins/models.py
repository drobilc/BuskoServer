from sqlalchemy import Column, Integer, String, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Obvestilo(Base):

	__tablename__ = 'obvestilo'
	
	id = Column(Integer, primary_key=True)
	naslov = Column(String)
	besedilo = Column(String)
	datum_objave = Column(DateTime)

	def toDictionary(self):
		return {
			"id": self.id,
			"naslov": self.naslov,
			"besedilo": self.besedilo,
			"datum_objave": self.datum_objave.isoformat()
		}

	def __repr__(self):
		return "<Obvestilo(naslov='{}', besedilo='{}')>".format(self.naslov, self.besedilo)

class Iskanje(Base):

	__tablename__ = 'iskanje'

	id = Column(Integer, primary_key=True)

	# Osnovni podatki o iskanju (od kod, kam, kdaj)
	vstopna_postaja = Column(String)
	izstopna_postaja = Column(String)
	datum = Column(Date)

	# Dodatne informacije o iskanju (datum iskanja)
	datum_iskanja = Column(DateTime)

	def toDictionary(self):
		return {
			"vstopna_postaja": self.vstopna_postaja,
			"izstopna_postaja": self.izstopna_postaja,
			"datum": self.datum,
			"datum_iskanja": self.datum_iskanja
		}

	def __repr__(self):
		return "<Iskanje(vstopna_postaja='{}', izstopna_postaja='{}')>".format(self.vstopna_postaja, self.izstopna_postaja)