# Prevoznik
Za dodajanje novega prevoznika je potrebno ustvariti novo datoteko v mapi `prevozniki`.
Datoteka naj vsebuje razred z imenom prevoznika, ta pa naj deduje od razreda `prevoznik.Prevoznik`.

Potrebno je napisati tri funkcije in sicer:
* `seznamPostaj` - vrne seznam (list) postaj ki jih ta prevoznik ponuja
* `obstajaPostaja(imePostaje)` - vrne `True` v primeru da postaja obstaja, sicer `False`
* `prenesiVozniRed(vstopnaPostaja, izstopnaPostaja, datum)` - vrne seznam slovarjev, pri katerem vsak slovar vsebuje ključe `prihod`, `odhod`, `trajanje`, `peron`, `prevoznik`, `cena`, `razdalja`. Vsebuje lahko še poljubno število dodatnih atributov.
Vstopna in izstopna postaja sta niza, datum pa je objekt tipa `datetime`. `odhod` in `prihod` morata biti obvezno objekta tipa `datetime`.