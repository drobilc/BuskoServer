from sqlalchemy import Table, Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

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

# Vmesna tabela med iskanjem in prevozom
vmesnaTabela = Table('association', Base.metadata,
	Column('iskanje_id', Integer, ForeignKey('iskanje.id')),
	Column('prevoz_id', Integer, ForeignKey('prevoz.id'))
)

class Iskanje(Base):

	__tablename__ = 'iskanje'

	id = Column(Integer, primary_key=True)

	# Osnovni podatki o iskanju (od kod, kam, kdaj)
	vstopna_postaja = Column(String)
	izstopna_postaja = Column(String)
	datum = Column(Date)

	# Dodatne informacije o iskanju (datum iskanja)
	datum_iskanja = Column(DateTime)

	# Povezava na tabelo prevozov
	prevozi = relationship("Prevoz", secondary=vmesnaTabela)

	def toDictionary(self):
		return {
			"vstopna_postaja": self.vstopna_postaja,
			"izstopna_postaja": self.izstopna_postaja,
			"datum": self.datum,
			"datum_iskanja": self.datum_iskanja
		}

	def __repr__(self):
		return "<Iskanje(vstopna_postaja='{}', izstopna_postaja='{}')>".format(self.vstopna_postaja, self.izstopna_postaja)

class Prevoz(Base):

	__tablename__ = 'prevoz'
	
	id = Column(Integer, primary_key=True)
	prihod = Column(DateTime)
	odhod = Column(DateTime)
	peron = Column(String)
	prevoznik = Column(String)
	cena = Column(String) # Popravi v prihodnosti
	razdalja = Column(String)

	def toDictionary(self):
		return {
			"prihod": self.prihod,
			"odhod": self.odhod,
			"peron": self.peron,
			"prevoznik": self.prevoznik,
			"cena": self.cena,
			"razdalja": self.razdalja,
			"trajanje": str(self.prihod - self.odhod),
			"url": ""
		}

	def __repr__(self):
		return "<Prevoz(prihod='{}', odhod='{}')>".format(self.prihod, self.odhod)