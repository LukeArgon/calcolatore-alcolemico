import streamlit as st
import requests
import re

# --- NUOVA FUNZIONE: RICERCA CIBO CON OPEN FOOD FACTS ---
def cerca_cibo_openfoodfacts(query):
    """Cerca un alimento nel database libero Open Food Facts"""
    # L'URL magico che non richiede chiavi!
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={query}&search_simple=1&action=process&json=1"
    
    # Facciamo finta di essere un browser per non farci bloccare
    headers = {'User-Agent': 'CalcolatoreAlcolemicoApp/1.0'} 
    
    risposta = requests.get(url, headers=headers)
    if risposta.status_code == 200:
        dati = risposta.json()
        # Restituiamo solo i primi 5 prodotti trovati per non intasare lo schermo
        prodotti = dati.get('products', [])
        return prodotti[:5] 
    return []

# --- FUNZIONI DI CALCOLO ALCOL (Invariate) ---
gradazioni_alcoliche = {
    "vodka": 40.0, "gin": 40.0, "rum": 40.0, "tequila": 40.0, "whiskey": 40.0, 
    "bourbon": 40.0, "rye whiskey": 40.0, "scotch": 40.0, "cognac": 40.0, "brandy": 40.0,
    "triple sec": 30.0, "cointreau": 40.0, "grand marnier": 40.0, "amaretto": 28.0,
    "kahlua": 20.0, "baileys": 17.0, "campari": 25.0, "aperol": 11.0, 
    "vermouth": 15.0, "sweet vermouth": 15.0, "dry vermouth": 15.0,
    "champagne": 12.0, "prosecco": 11.0, "wine": 12.0, "red wine": 13.0, "white wine": 12.0,
    "beer": 5.0, "ale": 5.0, "stout": 6.0, "cider": 5.0, "mezcal": 40.0
}

menu_alcolici = {
    "Birra Piccola (330ml, 5%)": {"ml": 330, "abv": 5.0},
    "Birra Media (500ml, 5%)": {"ml": 500, "abv": 5.0},
    "Vino Rosso - Calice (150ml, 13%)": {"ml": 150, "abv": 13.0},
    "Vino Bianco - Calice (150ml, 12%)": {"ml": 150, "abv": 12.0},
    "Prosecco/Spumante (150ml, 11%)": {"ml": 150, "abv": 11.0},
    "Shot (Vodka/Tequila/Rum) (40ml, 40%)": {"ml": 40, "abv": 40.0},
    "Amaro/Digestivo (40ml, 30%)": {"ml": 40, "abv": 30.0},
    "Grappa (40ml, 40%)": {"ml": 40, "abv": 40.0},
    "Spritz (Aperol/Campari) (150ml, ~11%)": {"ml": 150, "abv": 11.0}
}

def calcola_ml_da_misura(misura_str):
    if not misura_str: return 0.0
    misura = misura_str.lower().strip()
    valore = 1.0
    if "1/2" in misura: valore = 0.5
    elif "1/4" in misura: valore = 0.25
    elif "3/4" in misura: valore = 0.75
    elif "1/3" in misura: valore = 0.33
    else:
        match = re.search(r'^[\d\.]+', misura)
        if match:
            valore = float(match.group())
    if "oz" in misura: return valore * 30.0
    if "cl" in misura: return valore * 10.0
    if "ml" in misura: return valore
    if "shot" in misura: return valore * 44.0
    if "part" in misura: return valore * 30.0
    if "dash" in misura or "drop" in misura or "splash" in misura: return 1.0
    return valore * 30.0

def calcola_grammi_drink(drink_data):
    totale_grammi = 0.0
    ingredienti_calcolati = []
    for i in range(1, 16):
        ingrediente = drink_data.get(f'strIngredient{i}')
        misura = drink_data.get(f'strMeasure{i}')
        if ingrediente:
            ingrediente_basso = ingrediente.lower()
            ml_totali = calcola_ml_da_misura(misura)
            abv = 0.0
            for chiave in gradazioni_alcoliche:
                if chiave in ingrediente_basso:
                    abv = gradazioni_alcoliche[chiave]
                    break
            if abv > 0:
                grammi = ml_totali * (abv / 100) * 0.8
                totale_grammi += grammi
                ingredienti_calcolati.append(f"{ingrediente} ({ml_totali:.0f}ml al {abv}%) -> {grammi:.1f}g")
    return totale_grammi, ingredienti_calcolati

# --- IMPOSTAZIONI E MEMORIA DELL'APP ---
st.set_page_config(page_title="Calcolatore Tasso Alcolemico", page_icon="🍷")

# Memoria Drink
if 'lista_drink' not in st.session_state:
    st.session_state.lista_drink = []
if 'totale_alcol_g' not in st.session_state:
    st.session_state.totale_alcol_g = 0.0
if 'risultato_ricerca' not in st.session_state:
    st.session_state.risultato_ricerca = None

# Memoria Cibo
if 'lista_cibo' not in st.session_state:
    st.session_state.lista_cibo = []
if 'risultati_ricerca_cibo' not in st.session_state:
    st.session_state.risultati_ricerca_cibo = None

st.title("Calcolatore Avanzato Tasso Alcolemico")

# --- SEZIONE 1: I TUOI DATI ---
st.header("1. Profilo Utente")
col1, col2 = st.columns(2)
with col1:
    peso = st.number_input("Peso (kg)", min_value=30, max_value=200, value=70)
with col2:
    sesso = st.selectbox("Sesso", ["Maschio", "Femmina"])

st.divider()

# --- SEZIONE 2: INSERIMENTO BEVANDE ---
st.header("2. Cosa hai bevuto?")
tab1, tab2 = st.tabs(["🍺 Selezione Rapida", "🍹 Cerca Cocktail (API)"])

with tab1:
    scelta_rapida = st.selectbox("Seleziona la bevanda:", list(menu_alcolici.keys()))
    if st.button("Aggiungi alla lista", key="btn_rapido"):
        dati_bevanda = menu_alcolici[scelta_rapida]
        grammi_calcolati = dati_bevanda["ml"] * (dati_bevanda["abv"] / 100) * 0.8
        st.session_state.lista_drink.append(scelta_rapida)
        st.session_state.totale_alcol_g += grammi_calcolati
        st.rerun()

with tab2:
    nome_drink = st.text_input("Nome del cocktail (es. Margarita):")
    if st.button("Cerca Cocktail", key="btn_ricerca_drink"):
        if nome_drink:
            url_api = f"https://www.thecocktaildb.com/api/json/v1/1/search.php?s={nome_drink}"
            risposta = requests.get(url_api)
            dati = risposta.json()
            if dati['drinks']:
                drink_trovato = dati['drinks'][0]
                alcol_calcolato, dettagli = calcola_grammi_drink(drink_trovato)
                st.session_state.risultato_ricerca = {
                    "nome": drink_trovato['strDrink'],
                    "alcol": alcol_calcolato,
                    "dettagli": dettagli
                }
            else:
                st.error("Drink non trovato.")
                st.session_state.risultato_ricerca = None

    if st.session_state.risultato_ricerca:
        ricerca = st.session_state.risultato_ricerca
        st.success(f"Trovato: {ricerca['nome']}")
        st.write(f"**Alcol calcolato:** {ricerca['alcol']:.1f} g")
        if st.button(f"Aggiungi {ricerca['nome']} alla lista", key="btn_aggiungi_drink"):
            st.session_state.lista_drink.append(ricerca['nome'])
            st.session_state.totale_alcol_g += ricerca['alcol']
            st.session_state.risultato_ricerca = None
            st.rerun()

# --- SEZIONE 3: CIBO E IDRATAZIONE (Con Open Food Facts!) ---
st.divider()
st.header("3. Cibo e Idratazione 🍔💧")

st.write("Cerca un alimento (es. Pizza, Burger, Pasta):")
query_cibo = st.text_input("Nome alimento:")

if st.button("Cerca Alimento", key="btn_ricerca_cibo"):
    if query_cibo:
        with st.spinner("Ricerca nel database Open Food Facts..."):
            risultati = cerca_cibo_openfoodfacts(query_cibo)
            if risultati:
                st.session_state.risultati_ricerca_cibo = risultati
            else:
                st.error("Nessun alimento trovato. Prova un altro termine (magari in inglese).")
                st.session_state.risultati_ricerca_cibo = None

if st.session_state.risultati_ricerca_cibo:
    st.write("**Risultati trovati (seleziona per aggiungere):**")
    for cibo in st.session_state.risultati_ricerca_cibo:
        # Open Food Facts ha campi diversi rispetto a FatSecret
        nome_cibo = cibo.get('product_name', 'Prodotto senza nome')
        marca = cibo.get('brands', 'Marca ignota')
        
        # Saltiamo i prodotti che non hanno un nome valido
        if nome_cibo and nome_cibo != 'Prodotto senza nome':
            col_testo, col_btn = st.columns([3, 1])
            with col_testo:
                st.write(f"**{nome_cibo}** (*{marca}*)")
            with col_btn:
                # Usiamo l'ID univoco del prodotto per il bottone
                if st.button("➕ Aggiungi", key=f"add_cibo_{cibo.get('_id', nome_cibo)}"):
                    st.session_state.lista_cibo.append(f"{nome_cibo} ({marca})")
                    st.session_state.risultati_ricerca_cibo = None
                    st.rerun()

# Riepilogo cibo mangiato
if st.session_state.lista_cibo:
    st.success("🍕 Cibo consumato registrato:")
    for pasto in st.session_state.lista_cibo:
        st.write(f"- {pasto}")
    if st.button("🗑️ Svuota cibo"):
        st.session_state.lista_cibo = []
        st.rerun()

st.write("---")
col_idra1, col_idra2 = st.columns(2)
with col_idra1:
    bicchieri_acqua = st.number_input("Bicchieri d'acqua/analcolici bevuti", min_value=0, value=0)
with col_idra2:
    eventi_minzione = st.number_input("Quante volte sei andato/a in bagno?", min_value=0, value=0)

# --- SEZIONE 4 E RIEPILOGO FINALE ---
st.divider()
st.header("📊 Riepilogo e Calcolo Finale")

if st.session_state.lista_drink:
    col_met1, col_met2 = st.columns(2)
    with col_met1:
        st.metric(label="🍹 Numero di Drink", value=len(st.session_state.lista_drink))
    with col_met2:
        st.metric(label="⚖️ Totale Alcol", value=f"{st.session_state.totale_alcol_g:.1f} g")
    
    if st.button("🗑️ Svuota memoria drink", key="svuota_drink_basso"):
        st.session_state.lista_drink = []
        st.session_state.totale_alcol_g = 0.0
        st.rerun()

ore_trascorse = st.number_input("Ore trascorse dal primo drink", min_value=0.0, value=1.0, step=0.5)

if st.button("Calcola Tasso Alcolemico", type="primary"):
    r = 0.68 if sesso == "Maschio" else 0.55
    
    ha_mangiato = len(st.session_state.lista_cibo) > 0
    if ha_mangiato:
        r += 0.1
        st.info("💡 Noto che hai mangiato! Ho adeguato il calcolo: il cibo rallenta l'assorbimento dell'alcol.")
        
    if peso > 0 and st.session_state.totale_alcol_g > 0:
        bac_iniziale = st.session_state.totale_alcol_g / (peso * r)
        bac_finale = max(0.0, bac_iniziale - (0.15 * ore_trascorse))
    else:
        bac_finale = 0.0
        
    st.subheader(f"Tasso alcolemico stimato: {bac_finale:.2f} g/L")
