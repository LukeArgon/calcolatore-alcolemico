import streamlit as st
import requests
import re

# --- FUNZIONI DI CALCOLO ALCOL ---
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

# Inizializziamo tutte le variabili di memoria necessarie
if 'lista_drink' not in st.session_state:
    st.session_state.lista_drink = []
if 'totale_alcol_g' not in st.session_state:
    st.session_state.totale_alcol_g = 0.0
# NUOVO: Una memoria temporanea per la ricerca del cocktail
if 'risultato_ricerca' not in st.session_state:
    st.session_state.risultato_ricerca = None

st.title("Calcolatore Avanzato Tasso Alcolemico")

# --- SEZIONE 1: I TUOI DATI ---
st.header("1. Profilo Utente")
col1, col2 = st.columns(2)
with col1:
    peso = st.number_input("Peso (kg)", min_value=30, max_value=200, value=70)
with col2:
    sesso = st.selectbox("Sesso", ["Maschio", "Femmina"])

st.divider()

# --- SEZIONE 2: INSERIMENTO BEVANDE CON TABS ---
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
    
    # Bottone 1: Cerca e Salva in Memoria
    if st.button("Cerca Cocktail", key="btn_ricerca"):
        if nome_drink:
            url_api = f"https://www.thecocktaildb.com/api/json/v1/1/search.php?s={nome_drink}"
            risposta = requests.get(url_api)
            dati = risposta.json()
            
            if dati['drinks']:
                drink_trovato = dati['drinks'][0]
                nome = drink_trovato['strDrink']
                alcol_calcolato, dettagli = calcola_grammi_drink(drink_trovato)
                
                # Salviamo i risultati nella memoria temporanea
                st.session_state.risultato_ricerca = {
                    "nome": nome,
                    "alcol": alcol_calcolato,
                    "dettagli": dettagli
                }
            else:
                st.error("Drink non trovato.")
                st.session_state.risultato_ricerca = None

    # Se c'è una ricerca salvata in memoria, mostriamo i dati e il Bottone 2
    if st.session_state.risultato_ricerca:
        ricerca = st.session_state.risultato_ricerca
        st.success(f"Trovato: {ricerca['nome']}")
        st.write(f"**Alcol calcolato:** {ricerca['alcol']:.1f} g")
        
        with st.expander("Vedi i dettagli del calcolo"):
            if ricerca['dettagli']:
                for det in ricerca['dettagli']:
                    st.write(f"- {det}")
            else:
                st.write("Nessun ingrediente alcolico riconosciuto.")
        
        # Bottone 2: Aggiunge alla lista e pulisce la ricerca
        if st.button(f"Aggiungi {ricerca['nome']} alla lista", key="btn_aggiungi_ricerca"):
            st.session_state.lista_drink.append(ricerca['nome'])
            st.session_state.totale_alcol_g += ricerca['alcol']
            st.session_state.risultato_ricerca = None # Svuotiamo la ricerca temporanea
            st.rerun()

# --- NUOVA SEZIONE: RIEPILOGO METRICHE ---
st.write("---")
st.header("📊 Riepilogo Consumi")

if st.session_state.lista_drink:
    col_met1, col_met2 = st.columns(2)
    numero_drink_totali = len(st.session_state.lista_drink)
    
    with col_met1:
        st.metric(label="🍹 Numero di Drink Assunti", value=numero_drink_totali)
    with col_met2:
        st.metric(label="⚖️ Totale Alcol Assunto", value=f"{st.session_state.totale_alcol_g:.1f} g")
    
    with st.expander("Vedi i nomi dei drink bevuti"):
        for drink in st.session_state.lista_drink:
            st.write(f"- {drink}")
            
    if st.button("🗑️ Svuota memoria drink"):
        st.session_state.lista_drink = []
        st.session_state.totale_alcol_g = 0.0
        st.session_state.risultato_ricerca = None
        st.rerun()
else:
    st.info("Non hai ancora aggiunto nessun drink. Usa la selezione qui sopra per iniziare!")

st.divider()

# --- SEZIONE 3: CIBO E IDRATAZIONE ---
st.header("3. Cibo e Idratazione")
ha_mangiato = st.checkbox("Ho fatto un pasto completo")
bicchieri_acqua = st.number_input("Bicchieri d'acqua o analcolici bevuti", min_value=0, value=0)
eventi_minzione = st.number_input("Quante volte sei andato/a in bagno?", min_value=0, value=0)

st.divider()

# --- SEZIONE 4: IL CALCOLO FINALE ---
st.header("4. Risultato")
ore_trascorse = st.number_input("Ore trascorse dal primo drink", min_value=0.0, value=1.0, step=0.5)

if st.button("Calcola Tasso Alcolemico e Idratazione", type="primary"):
    r = 0.68 if sesso == "Maschio" else 0.55
    if ha_mangiato:
        r += 0.1
        
    if peso > 0 and st.session_state.totale_alcol_g > 0:
        bac_iniziale = st.session_state.totale_alcol_g / (peso * r)
        bac_finale = max(0.0, bac_iniziale - (0.15 * ore_trascorse))
    else:
        bac_finale = 0.0
        
    st.subheader(f"Tasso alcolemico stimato: {bac_finale:.2f} g/L")
