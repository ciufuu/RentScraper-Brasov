import sqlite3 as sql
import pandas as pd
import schedule , time
from bs4 import BeautifulSoup
import requests 

conn = sql.connect("BazaDate.db")
cursor = conn.cursor()

# Creează tabela dacă nu există
cursor.execute("""
CREATE TABLE IF NOT EXISTS Rezultate (
    NumeAnunt TEXT,
    Pret REAL,
    Moneda TEXT,
    Link TEXT UNIQUE,
    Zona TEXT
)
""")

def detecteaza_zona(titlu):
    zone_brasov = [
    "Centru", "Centrul Vechi", "Centrul Civic", "Schei", "Bartolomeu",
    "Tractorul", "Astra", "Racadau", "Florilor", "Noua", "Calea Bucuresti",
    "Grivitei", "Scriitorilor", "Craiter", "Blumana", "Valea Cetatii",
    "Stupini", "Brasovechi", "Triaj", "Darste", "Avantgarden",
    "Coresi", "Urban Residence", "Poiana Brasov", "Dealul Melcilor",
    "Saturn", "Carpatilor", "Steagu"
]
    for zona in zone_brasov:
        if zona.lower() in titlu.lower():
            return zona
    return 'Necunoscut'

url = f"https://www.olx.ro/imobiliare/apartamente-garsoniere-de-inchiriat/brasov/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0"
}
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")


pagination = soup.select("a[data-testid^='pagination-link']")
pagini = [int(p.get_text()) for p in pagination if p.get_text().isdigit()]
max_pagini = max(pagini) if pagini else 1

pagina = 1
while pagina <= max_pagini:
    
    print(f"Procesare pagina {pagina} din {max_pagini}...")
    
    url = f"https://www.olx.ro/imobiliare/apartamente-garsoniere-de-inchiriat/brasov/?page={pagina}"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    

    # Extrage anunțurile
    anunturi = soup.find_all('div', class_='css-1sw7q4x') 
    anunturi_reale = [a for a in anunturi if a.find('p', {"data-testid": "ad-price"})]
    if not anunturi_reale:
        print("Nu mai sunt anunturi. Oprire.")
        break
    
    for a in anunturi_reale:
        titlu_tag = a.find('h4', class_='css-hzlye5')
        titlu = titlu_tag.get_text(strip=True) if titlu_tag else "Titlu indisponibil"
        pret_el = a.find('p', {"data-testid": "ad-price"})
        if not pret_el:
            continue  
        link_tag = a.find('a', class_='css-1tqlkj0')
        if link_tag and 'href' in link_tag.attrs:
            link = link_tag['href']
        else:
            link = 'Link indisponibil'
        zona = detecteaza_zona(titlu)
        
        pret_principal = ''.join(pret_el.find_all(string=True, recursive=False)).strip() 

        parti = pret_principal.split()  # împarte prețul în părți pentru a separa numărul de monedă
        
        try:
            numar = parti[0].replace('.', '').replace(',', '')  
            pret = int(numar)  
            moneda = next((p for p in parti if p in ['€', 'RON', 'Lei']), 'moneda nu a fost gasita')  
        except Exception :
            continue  

        # Inserare doar dacă nu există deja
        cursor.execute("""
        INSERT OR IGNORE INTO Rezultate (NumeAnunt, Pret, Moneda, Link, Zona)
        VALUES (?, ?, ?, ?, ?)
        """, (titlu, pret, moneda, link, zona))

    pagina += 1
    time.sleep(1.5)


conn.commit()

conn = sql.connect('BazaDate.db')
df=pd.read_sql("SELECT * FROM Rezultate ", conn)
conn.close()

# Funcții pentru afișare și filtrare

def afiseaza_toate_anunturile():
    print(df)
    print("\nDoriti exportarea datelor in excel? (da/nu)")
    raspuns = input().strip().lower()
    if raspuns == 'da':
        df.to_excel("anunturi_olx.xlsx", index=False)
        print("Datele au fost exportate în 'anunturi_olx.xlsx'.")
    elif raspuns == 'nu':
        print("Datele nu au fost exportate.")
    else:
        print("Răspuns invalid. Datele nu au fost exportate.")

def filtreaza_dupa_pret(prag_inf, prag_sup):
    filtrat_df = df[(df['Pret'] >= prag_inf) & (df['Pret'] <= prag_sup)]
    print(f"\nAm găsit {len(filtrat_df)} anunțuri între {prag_inf} și {prag_sup} :\n")
    print(filtrat_df[['NumeAnunt', 'Pret', 'Link']])
    print ("Doriți exportarea datelor filtrate in excel? (da/nu)")
    raspuns = input().strip().lower()
    if raspuns == 'da':
        filtrat_df.to_excel("filtruPret_olx.xlsx", index=False)
        print("Datele au fost exportate în 'filtru_olx.xlsx'.")
    elif raspuns == 'nu':
        print("Datele nu au fost exportate.")
    else:
        print("Răspuns invalid. Datele nu au fost exportate.")

def filtreaza_dupa_zona(zona_cautata):
    filtrat_df = df[df['Zona'].str.lower() == zona_cautata.lower()].reset_index(drop=True)
    print(f"\nAm găsit {len(filtrat_df)} anunțuri în zona '{zona_cautata}':\n")
    print(filtrat_df[['NumeAnunt', 'Zona', 'Link' , 'Pret']])
    print ("Doriți exportarea datelor filtrate in excel? (da/nu)")
    raspuns = input().strip().lower()
    if raspuns == 'da':
        filtrat_df.to_excel("filtruZona_olx.xlsx", index=False)
        print("Datele au fost exportate în 'filtru_olx.xlsx'.")
    elif raspuns == 'nu':
        print("Datele nu au fost exportate.")
    else:
        print("Răspuns invalid. Datele nu au fost exportate.")
        
while True:
    print("""
        ----MENIU----
1. Afișează toate anunțurile
2. Filtrează anunțurile in funcție de preț
3. Filtrează anunțurile in funcție de zonă
4. Iesire""")
    optiune = input("Alege o opțiune (1-4): ")
    if optiune == '1':
        afiseaza_toate_anunturile()
    elif optiune == '2':
        prag_inf = int(input("Introduceți pragul inferior de preț: "))
        prag_sup = int(input("Introduceți pragul superior de preț: "))
        filtreaza_dupa_pret(prag_inf, prag_sup)
    elif optiune == '3':
        zona_cautata = input("Introduceți zona dorită: ")
        filtreaza_dupa_zona(zona_cautata)
    elif optiune == '4':
        print("Ieșire din program.")
        break
    else:
        print("Opțiune invalidă. Încearcă din nou.")