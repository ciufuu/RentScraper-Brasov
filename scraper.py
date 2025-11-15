import sqlite3 as sql
import pandas as pd
from bs4 import BeautifulSoup
import requests
import schedule , time

DB_NAME = "BazaDate.db"


# ===================== SETUP BAZĂ DE DATE =====================

def setup_db():
    conn = sql.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Rezultate (
        NumeAnunt TEXT,
        Pret REAL,
        Moneda TEXT,
        Link TEXT UNIQUE,
        Zona TEXT
    )
    """)
    conn.commit()
    conn.close()


# ===================== FUNCTII UTILE =====================

def get_dataframe():
    """Încarcă toate anunțurile din DB într-un DataFrame."""
    conn = sql.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM Rezultate", conn)
    conn.close()
    return df

def obtine_curs_eur_ron():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/EUR", timeout=10)
        data = r.json()
        return data["rates"]["RON"]
    except:
        return 5.0


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


# ===================== SCRAPER OLX =====================

def scrape_olx():
    print("\n=== Pornire scraper OLX ===")

    conn = sql.connect(DB_NAME)
    cursor = conn.cursor()

    url = "https://www.olx.ro/imobiliare/apartamente-garsoniere-de-inchiriat/brasov/?currency=RON"
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

        print(f"[OLX] Procesare pagina {pagina} din {max_pagini}...")

        url_pagina = f"https://www.olx.ro/imobiliare/apartamente-garsoniere-de-inchiriat/brasov/?currency=RON&page={pagina}"
        r = requests.get(url_pagina, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")

        # Extrage anunțurile
        anunturi = soup.find_all('div', class_='css-1sw7q4x')
        anunturi_reale = [a for a in anunturi if a.find('p', {"data-testid": "ad-price"})]
        if not anunturi_reale:
            print("[OLX] Nu mai sunt anunțuri. Oprire.")
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
            parti = pret_principal.split()
            
            try:
                numar, moneda = pret_principal.rsplit(" ", 1)
                moneda = 'RON' 
                numar = numar.replace('.', '').replace(',', '').replace(" ","")
                pret = int(numar)
                
            except Exception:
                continue
            
            cursor.execute("""
            INSERT OR IGNORE INTO Rezultate (NumeAnunt, Pret, Moneda, Link, Zona)
            VALUES (?, ?, ?, ?, ?)
            """, (titlu, pret, moneda, link, zona))

        conn.commit()
        pagina += 1
        
    
    conn.close()
    print("=== Scraper OLX terminat ===\n")


# ===================== SCRAPER PUBLI24 =====================

def scrape_publi24():
    print("\n=== Pornire scraper Publi24 ===")

    conn = sql.connect(DB_NAME)
    cursor = conn.cursor()

    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0",
    "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
    "Referer": "https://www.google.ro/"
 }
    url = "https://www.publi24.ro/anunturi/brasov/?q=chirie&pag={pagina}"
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, "html.parser")

    pagination = soup.select('li' , class_ = 'current')
    pagini = [int(p.get_text()) for p in pagination if p.get_text().isdigit()]
    max_pagini = max(pagini) if pagini else 1

    pagina = 1
    while pagina <= max_pagini:
        
        print(f"Procesare pagina {pagina} din {max_pagini}...")
        
        url = f"https://www.publi24.ro/anunturi/brasov/?q=chirie&pag={pagina}"
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        

            # Extrage anunțurile

        anunturi = soup.find_all('div', class_='article-item') 
        if not anunturi:
            print ("Nu mai sunt anunturi de procesat.")
            
        for a in anunturi:
            titlu_tag = a.find('h2', class_='article-title')
            titlu = titlu_tag.get_text(strip=True) if titlu_tag else "Titlu indisponibil"
            if titlu_tag:
                a_tag = titlu_tag.find('a')
            if a_tag:
                link = a_tag.get('href')
            else:
                link = 'Link indisponibil'
            pret_el = a.find('span', class_='article-price')
            zona = a.find('p', class_='article-location').get_text(strip=True) if a.find('p', class_='article-location') else 'Zona indisponibila'
            if not pret_el:
                continue  
            
            pret_principal = ''.join(pret_el.find_all(string=True, recursive=False)).strip() 
            
            parti = pret_principal.split()  # împarte prețul în părți pentru a separa numărul de monedă
            
            try:
                numar, moneda = pret_principal.rsplit(" ", 1)
                numar = numar.replace('.', '').replace(',', '').replace(" ","")
                pret = int(numar)
                
            except Exception:
                continue

            # Inserare doar dacă nu există deja
            cursor.execute("""
            INSERT OR IGNORE INTO Rezultate (NumeAnunt, Pret, Moneda, Link, Zona)
            VALUES (?, ?, ?, ?, ?)
            """, (titlu, pret, moneda, link, zona))
        
        conn.commit()
        pagina += 1
        
    
    conn.close()
    print("=== Scraper Publi24 terminat ===\n")


# ===================== FUNCTII PENTRU AFISARE / FILTRARE =====================

def afiseaza_toate_anunturile():
    df = get_dataframe()
    if df.empty:
        print("\nNu există anunțuri în baza de date.\n")
        return

    print(df)
    print("\nDoriți exportarea datelor în Excel? (da/nu)")
    raspuns = input().strip().lower()
    if raspuns == 'da':
        df.to_excel("anunturi_total.xlsx", index=False)
        print("Datele au fost exportate în 'anunturi_total.xlsx'.")
    else:
        print("Datele nu au fost exportate.")


def filtreaza_dupa_pret(prag_inf, prag_sup):
    df = get_dataframe()
    filtrat_df = df[(df['Pret'] >= prag_inf) & (df['Pret'] <= prag_sup)].reset_index(drop=True)

    print(f"\nAm găsit {len(filtrat_df)} anunțuri între {prag_inf} și {prag_sup}:\n")
    print(filtrat_df[['NumeAnunt', 'Pret', 'Link']])

    print("\nDoriți exportarea datelor filtrate în Excel? (da/nu)")
    raspuns = input().strip().lower()
    if raspuns == 'da':
        filtrat_df.to_excel("filtru_pret.xlsx", index=False)
        print("Datele au fost exportate în 'filtru_pret.xlsx'.")
    else:
        print("Datele nu au fost exportate.")


def filtreaza_dupa_zona(zona_cautata):
    df = get_dataframe()
    filtrat_df = df[df['Zona'].str.lower().str.contains(zona_cautata.lower(), na=False)].reset_index(drop=True)

    print(f"\nAm găsit {len(filtrat_df)} anunțuri în zona '{zona_cautata}':\n")
    print(filtrat_df[['NumeAnunt', 'Zona', 'Pret', 'Link']])

    print("\nDoriți exportarea datelor filtrate în Excel? (da/nu)")
    raspuns = input().strip().lower()
    if raspuns == 'da':
        filtrat_df.to_excel("filtru_zona.xlsx", index=False)
        print("Datele au fost exportate în 'filtru_zona.xlsx'.")
    else:
        print("Datele nu au fost exportate.")


def filtreaza_dupa_pret_si_zona(prag_inf, prag_sup, zona_cautata):
    df = get_dataframe()
    filtrat_df = df[
        (df['Pret'] >= prag_inf) &
        (df['Pret'] <= prag_sup) &
        (df['Zona'].str.lower().str.contains(zona_cautata.lower(), na=False))
    ].reset_index(drop=True)

    print(f"\nAm găsit {len(filtrat_df)} anunțuri între {prag_inf} și {prag_sup} în zona '{zona_cautata}':\n")
    print(filtrat_df[['NumeAnunt', 'Pret', 'Zona', 'Link']])

    print("\nDoriți exportarea datelor filtrate în Excel? (da/nu)")
    raspuns = input().strip().lower()
    if raspuns == 'da':
        filtrat_df.to_excel("filtru_pret_zona.xlsx", index=False)
        print("Datele au fost exportate în 'filtru_pret_zona.xlsx'.")
    else:
        print("Datele nu au fost exportate.")


# ===================== MENIU PRINCIPAL =====================

def main():
    setup_db()

    while True:
        print("""
========== MENIU ==========
1. Rulează scrapers (OLX + Publi24)
2. Afișează toate anunțurile
3. Filtrează anunțurile în funcție de preț
4. Filtrează anunțurile în funcție de zonă
5. Filtrează anunțurile în funcție de preț și zonă
6. Ieșire
===========================
""")
        optiune = input("Alege o opțiune (1-6): ").strip()

        if optiune == '1':
            scrape_olx()
            scrape_publi24()
        elif optiune == '2':
            afiseaza_toate_anunturile()
        elif optiune == '3':
            try:
                print("Doriti sa filtrati in RON sau EUR? (introduceti RON sau EUR)")
                moneda = input().strip().upper()
                if moneda == 'EUR':
                    curs = obtine_curs_eur_ron()
                    prag_inf_eur = float(input("Introduceți pragul inferior de preț în EUR: "))
                    prag_sup_eur = float(input("Introduceți pragul superior de preț în EUR: "))
                    prag_inf = int(prag_inf_eur * curs)
                    prag_sup = int(prag_sup_eur * curs)
                    filtreaza_dupa_pret(prag_inf, prag_sup)
                else:
                    prag_inf = int(input("Introduceți pragul inferior de preț (RON): "))
                    prag_sup = int(input("Introduceți pragul superior de preț (RON): "))
                    filtreaza_dupa_pret(prag_inf, prag_sup)
            except ValueError:
                print("Trebuie să introduceți valori numerice pentru preț.")
        elif optiune == '4':
            zona_cautata = input("Introduceți zona dorită: ")
            filtreaza_dupa_zona(zona_cautata)
        elif optiune == '5':
            try:
                print ("Doriti sa filtrati in RON sau EUR? (introduceti RON sau EUR)")
                moneda = input().strip().upper()
                if moneda == 'EUR':
                    curs = obtine_curs_eur_ron()
                    prag_inf_eur = float(input("Pragul inferior de preț în EUR: "))
                    prag_sup_eur = float(input("Pragul superior de preț în EUR: "))
                    prag_inf = int(prag_inf_eur * curs)
                    prag_sup = int(prag_sup_eur * curs)
                else:
                    prag_inf = int(input("Pragul inferior de preț (RON): "))
                    prag_sup = int(input("Pragul superior de preț (RON): "))
                    zona_cautata = input("Zona dorită: ")
                    filtreaza_dupa_pret_si_zona(prag_inf, prag_sup, zona_cautata)
            except ValueError:
                print("Trebuie să introduceți valori numerice pentru preț.")
        elif optiune == '6':
            print("Ieșire din program.")
            break
        else:
            print("Opțiune invalidă. Încearcă din nou.")


if __name__ == "__main__":
    main()