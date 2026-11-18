# Obiteljsko stablo

---

## Što je ovo

Program za grafički prikaz obiteljskog stabla kroz više generacija i koljena. Postavi se program, dvoklik na .exe pa se otvori konzola i u browseru stranica. Kad je gotovo korištenje onda se ugasi stranica u browseru te konzola.

## Kako se postavlja

Niz koraka: 1., 2., ..., i koje tehnologije i naredbe treba koristiti

## Koje tehnologije su korištene

| Dio sustava | Tehnologija | Uloga u projektu |
| :--- | :--- | :--- |
| **Backend server** | Python 3.11+, Flask | HTML stranica, REST API, pokreće lokalni server na slobodnom portu. |
| **Baza podataka** | SQLite3 | Pohranjuje osobe, veze i partnerstva u jednu lokalnu datoteku (`obitelj.db`) |
| **Grafički editor** | family-chart (v0.9.0) | Uređivanje osoba i veza (open-source biblioteka) |
| **Prikaz cijele mreže** | D3.js (v7) | Iscrtavanje stabla uz slobodno zumiranje i pomicanje (open-source biblioteka) |
| **Frontend sučelje** | HTML5, CSS3, JavaScript (ES6) | Frontend (korisničko sučelje) i backend povezani te radi potpuno offline |
| **Pakiranje aplikacije** | PyInstaller (`--onedir`) | Pretvara cijelu aplikaciju u Windows `.exe` datoteku |

## Kako se postavlja

### A. Pokretanje iz izvornog koda (za razvoj)

Za lokalno pokretanje potreban je **Python 3.11** (ili noviji).

1. Preuzmite repozitorij lokalno i uđite u mapu projekta

2. Instalirajte Python biblioteku **Flask**:
   ```bash
   pip install flask
   ```

3. Pokrenite aplikaciju:
   ```bash
   python server.py
   ```

Aplikacija će automatski stvoriti praznu bazu podataka `obitelj.db` (ako već ne postoji (napredno: može se postaviti druga postojeća), pronaći slobodan lokalni port i samostalno otvoriti sučelje u browseru.

### B. Sinteza `.exe` aplikacije

Ako aplikaciju želite pokretati dvoklikom ili je prebaciti na drugo računalo bez instalacije Pythona i potrebnih alata:

1. Instalirajte **PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. Pokrenite naredbu za pakiranje aplikacije (`templates` i `static`):
   ```bash
   pyinstaller --onedir --name "ObiteljskoStablo" --add-data "templates;templates" --add-data "static;static" server.py
   ```

3. Otvorite stvorenu mapu `dist\ObiteljskoStablo\` i pokrenite `ObiteljskoStablo.exe`. Baza podataka `obitelj.db` automatski se sprema u istu mapu pokraj `.exe` datoteke (možete prenositi `obitelj.db' bazu podataka s jednog računala na drugo, u toj datoteci se nalazi obiteljsko stablo).
