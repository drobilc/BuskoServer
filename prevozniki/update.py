from .prevoznik import Prevoznik
from datetime import datetime, timedelta

class Update(Prevoznik):

    obvestilo = "Prosimo da si posodobite aplikacijo"
	
    def seznamPostaj(self):
        return []
    
    def obstajaPostaja(self, imePostaje):
        return True
    
    def prenesiVozniRed(self, vstopnaPostaja, izstopnaPostaja, datum):
        prevozi = []

        besede = self.obvestilo.split(" ")

        zacetek = datum.replace(hour=23, minute=59, second=0, microsecond=0) - timedelta(minutes=len(besede))

        for indeks, beseda in enumerate(besede):
            uraOdhoda = zacetek + timedelta(minutes=indeks+1)
            uraPrihoda = uraOdhoda + timedelta(minutes=1)

            prevoz = {
				"prihod": uraPrihoda,
				"odhod": uraOdhoda,
				"peron": "!",
				"prevoznik": beseda,
				"cena": 0,
				"razdalja": 0
			}

            prevozi.append(prevoz)

        return prevozi
    
    def vmesnePostaje(self, prevoz):
        relacije = []

        zacetek = prevoz['odhod'].replace(hour=0, minute=0, second=0, microsecond=0)

        besede = self.obvestilo.split(" ")
        for indeks, beseda in enumerate(besede):
            cas = zacetek + timedelta(minutes=indeks+1)
            relacije.append({
				"postaja": beseda,
				"cas_prihoda": cas
			})

        return relacije
	

if __name__ == "__main__":
    p = Update()
    print(p.prenesiVozniRed("Nova Gorica", "Ljubljana", datetime.now()))