# RentScraper-Brasov
![Last Commit](https://img.shields.io/github/last-commit/ciufuu/Scraper_Chirii)


Scopul acestui script este de a extrage date de pe mai multe site-uri ce prezintă anunțuri de chirii ci să filtreze rezultatele in funcție de dorința utilizatorului.

Programul extrage anunțurile legate de chirii si le salvează într-o bază de date , unde pot fi vizualizate și accesate ci de unde pot fi folosite pentru filtrare.

Urmeaza a se adauga si posibilitatea de a filtra preturile in functie de valuta (RON/EURO) . 
(La momentul actual functia de filtrare a pretului nu tine cont de valuta !)

*Cu timpul vor fi adăugate mai multe site-uri de pe care se vor extrage date si vor fi implementate noi funcții in program!*
Momentan programul preia date de pe urmatoarele site-uri : 
 - https://www.olx.ro/imobiliare/apartamente-garsoniere-de-inchiriat/brasov/ 
 - https://www.publi24.ro/anunturi/brasov/?q=chirie

! Pentru a rula acest script este necesară instalarea următoarelor module : 

*pandas
*beautifulsoup
*requests
*schedule (_momentan nu este folosit dar urmează a fi implementat pentru automatizarea script-ului_)

Comenzile pentru instalare : 

pip install pandas,
pip install beautifulsoup4,
pip install requests,
pip install schedule
