# Busko server
Busko server je strežnik, ki ga aplikacija [Busko](https://play.google.com/store/apps/details?id=com.drobilc.busko) uporablja za komunikacijo s spletno stranjo prevoznika [Nomago](https://www.avrigo.si/sl/).

## Namestitev
Za namestitev strežnika poženite naslednje ukaze:
```
git clone https://github.com/drobilc/BuskoServer.git
cd BuskoServer
pip install -r requirements.txt
```
Če želite pognati server lahko to storite z naslednjim ukazom
```
python main.py
```

## Server
Server podatke pošilja v obliki *JSON*.
Spodaj bodo opisani vsi endpointi, do katerih lahko uporabniki dostopajo.

### Obvestila uporabnikom
Url: `/obvestilo`

Vsako obvestilo ima svoj `naslov`, `besedilo` in `datum_objave`.

Od strežnika zahteva zadnje obvestilo, ki je bilo objavljeno po datumu navedenem v parametru `od`.
Parameter ni obvezen, strežnik v primeru, da ta ni podan vrne zadnje objavljeno obvestilo.

#### Parametri
**GET** parametri:
* `od` - datum zadnjega odprtja aplikacije v UTC obliki (ni obvezno)

#### Format rezultata
Rezultat je *JSON objekt*, ki ima vedno naslednja polja:
* `id` - identifikacijska številka obvestila (celoštevilska vrednost)
* `naslov` - naslov obvestila
* `besedilo` - besedilo obvestila
* `datum_objave` - datum podan v UTC obliki

Primer:
```json
{
	"id": 1,
	"naslov": "Naslov obvestila",
	"besedilo": "Besedilo obvestila",
	"datum_objave": "2018-06-18T07:37:18.601105"
}
```

#### Primer zahtevka
[`http://gobo.si:7000/obvestilo?od=2018-06-15T10:00:00.000000`](http://gobo.si:7000/obvestilo?od=2018-06-15T10:00:00.000000)


### Avtobusni prevoz na določen dan
Url: `/vozni_red`

#### Parametri
**GET** parametri:
* `vstopna_postaja` - vstopna postaja 
* `izstopna_postaja` - izstopna postaja
* `datum` - datum voznega reda, oblika `DD.MM.YYYY`

#### Format rezultata
Vrne *JSON array* objektov, ki imajo na voljo naslednja polja:
* `prihod` - ura prihoda na postajo, oblika `HH:MM`
* `odhod` - ura odhoda iz postaje, oblika `HH:MM`
* `trajanje` - trajanje vožnje, oblika `HH:MM`
* `peron` - številka perona, lahko tudi prazen niz
* `prevoznik` - ime prevoznika
* `cena` - cena vožnje
* `razdalja` - razdalja med postajama
* `url` - URL naslov do seznama vmesnih postaj

Primer enega objekta iz seznama:
```json
{
	"prihod": "05:15",
	"odhod": "04:40",
	"trajanje": "00:35",
	"peron": "2",
	"prevoznik": "NOMAGO",
	"cena": "3,10 EUR",
	"razdalja": "24 km",
	"url": "http://voznired.avrigo.si/PotekVoznje.aspx?REG_ISIF=008297&OVR_SIF=0050&LIS_ZAPZ=10&LIS_ZAPK=170&VVLN_ZL=0"
}
```

#### Primer zahtevka
[`http://gobo.si:7000/vozni_red?vstopna_postaja=Nova Gorica AP&izstopna_postaja=Ajdovščina&datum=15.06.2018`](http://gobo.si:7000/vozni_red?vstopna_postaja=Nova%20Gorica%20AP&izstopna_postaja=Ajdov%C5%A1%C4%8Dina&datum=15.06.2018)