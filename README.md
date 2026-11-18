# Obiteljsko stablo

---

Želim napraviti aplikaciju koja grafički prikazuje obiteljsko stablo (7, 8 generacija u nazad, raznorazni rođaci, vrlo široko, itd.). Glavni cilj je da bude jednostavno za koristiti i najvažnije, a to je da bude pregledno i jasno (može se zumirati, sve jasno sažeto piše, itd.)

Planiram raditi ovo isključivo u Python + SQLite. Bila bi onda desktop .exe aplikacija s .db databazom (ukupno 2 file-a). Tvoje misli, što preporučaš ili postoji li neki bolji način? Postoji li već ovo?

SQLite: svaka osoba ima svoj ID (za razlikovanje istih imena, a različite osobe, nije vidljivo korisniku, jedini integer ovdje), ime (zasad samo jedna stavka), godina rođenja, godina smrti; oca, majku, djecu (optional svo troje, ali nisu tekst nego povezani su crtom vizualno)

Napomene: mora se moći postaviti, ili kroz jedan .exe ili neki drugi način da ja mogu napraviti za jedan folder u kojem se ovo nalazi, nakon što se sredi sve, copy paste na laptop druge osobe, ona dvoklik "negdje", i to radi sve savršeno (easy to use poslije izvršenog setupa, ne želim instaliravati ništa na tuđe računalo).

Pitanja? Misli? Osvrti? Napomene? Pitaj i ti slobodno apsolutno sve što misliš, zasad samo razglabamo o ovome.

---

Moje misli: htio bih da se grafički može jednostavno dodavati, editati, uklanjati svaka osoba grafički. Za browser mi ne smeta i nije ključno da bude .exe, ključ je u jednostavnosti. Poanta mi je da se može lokalno bez interneta pokrenuti, ne treba izvoditi gluposti za spremanje promjena, i da se može "pokrenuti dvoklikom".

Odgovori na pitanja:
1) može i partnerstvo bez djece, ali ako je vrlo komplicirano onda ne još
2) koristit će je članovi obitelji na svojim računalima. Zato želim da bude "copy paste" i "dvoklik" i sve grafički.
3) ne znam točno, ali sigurno barem 100, to je apsolutni minimum. Radit ćemo stablo za 7, 8 generacija unazad, a svi su tada imali 5, 6 djece, neki 12, neki 20, a neki 2. Moguće je da prijeđe 250+ bez problema.
4) zasad samo windows. Ako se na išta bude prebacivalo, to ćemo tada misliti. (jedino možda android, ali to je još vrlo daleko i ne znam koliko vjerojatno)




GUI sa spremištem

Dodavanje, editanje, uklanjanje elemenata

Cijeli sustav je praktički:
-nodes -> ljudi
--ima: svojstva: ID, ime, prezime
--ima: vezu s node-ovima: otac, majka, potomak (optional: 0, 1, 2, 3, itd.)
-edges -> tko je kome roditelj i/ili sin i/ili sibling
--određuju se kroz node-ove
Sve se radi kroz node-ove, edges sami nastaju kao reakcija na to (to je ideja za korisničko iskustvo, kako radi ispod haube ćemo vidjeti)

Cilj: napraviti easy to use sučelje za gledati ogromno obiteljsko stablo, s mnogo pokoljenja i generacija

---

# Nodes

Svaki node će biti objekt. Varijable za svaki objekt:
1) id (ako njih više ima isto ime i prezime da ih možemo razlikovati)
2) ime
3) prezime
4) father_node
5) mother_node
6) children node (minimum 0, maximum beskonačno)

Zanimljivo pitanje: je li bolje modelirati ovo u SQLite-u?

Sva pitanja, ako imaš iti jedno, pitaj odmah prije izgradnje file-ova.

Radiš primarno u Python-u, ali ako treba nešto drugo, tipa SQLite, onda napomeni.