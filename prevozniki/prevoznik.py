class Prevoznik(object):
	"""Razred Prevoznik je stars vseh razredov za prenos
	voznih redov s spletnih strani prevoznikov"""

	def seznamPostaj(self):
		"""Vrne seznam imen postaj"""
		return []

	def obstajaPostaja(self, imePostaje):
		"""Preveri, ali ta prevoznik prevaza iz postaje z imenom imePostaje"""
		return False

	def prenesiVozniRed(self, vstopnaPostaja, izstopnaPostaja, datum):
		"""Vrne vozni red med izbranima postajama za datum datum"""
		return []