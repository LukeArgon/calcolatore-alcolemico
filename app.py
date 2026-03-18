import streamlit as st
import requests

# --- IMPOSTAZIONI E MEMORIA DELL'APP ---
st.set_page_config(page_title="Calcolatore Tasso Alcolemico", page_icon="🍷")

# Inizializziamo la "memoria" dell'app per ricordare cosa abbiamo bevuto e mangiato
if 'lista_drink' not in st.session_state:
    st.session_state.lista_drink = []
if 'totale_alcol_g' not in st.session_state:
    st.session_state.totale_alcol_g = 0.0

st.title("Calcolatore Avanzato Tasso Alcolemico")

# --- SEZIONE 1: I TUOI DATI ---
st.header("1. Profilo Utente")
col1, col2 = st.columns(2)
with col1:
    peso = st.number_input("Peso (kg)", min_value=30, max_value=200, value=70)
with col2:
    sesso = st.selectbox("Sesso", ["Maschio", "Femmina"])

st.divider()

# --- SEZIONE 2: RICERCA E AGGIUNTA DRINK (TheCocktailDB) ---
st.header("2. Cosa hai bevuto?")
nome_drink = st.text_input("Cerca un cocktail (es. Margarita, Mojito):")

if st.button("Cerca e Mostra Dettagli"):
    if nome_drink:
        url_api = f"https://www.thecocktaildb.com/api/json/v1/1/search.php?s={nome_drink}"
        risposta = requests.get(url_api)
        dati = risposta.json()
        
        if dati['drinks']:
            drink_trovato = dati['drinks'][0]
            nome = drink_trovato['strDrink']
            st.success(f"Trovato: {nome}")
            
            # Un cocktail medio contiene circa 14-18 grammi di alcol puro. 
            # In futuro miglioreremo questo calcolo analizzando ogni singolo ingrediente!
            alcol_stimato = st.slider("Conferma i grammi di alcol per questo drink (Media: 14g)", 0, 50, 14)
            
            # Bottone per salvare il drink nella memoria
            if st.button(f"Aggiungi {nome} alla tua lista"):
                st.session_state.lista_drink.append(nome)
                st.session_state.totale_alcol_g += alcol_stimato
                st.rerun() # Ricarica la pagina per aggiornare i dati mostrati
        else:
            st.error("Drink non trovato. Riprova con il nome in inglese!")

# Mostra cosa c'è in memoria
if st.session_state.lista_drink:
    st.write("**I tuoi drink consumati finora:**")
    for drink in st.session_state.lista_drink:
        st.write(f"- 🍹 {drink}")
    st.write(f"**Totale alcol assunto:** {st.session_state.totale_alcol_g} g")
    
    # Bottone per svuotare la memoria
    if st.button("Svuota lista drink"):
        st.session_state.lista_drink = []
        st.session_state.totale_alcol_g = 0.0
        st.rerun()

st.divider()

# --- SEZIONE 3: CIBO, ANALCOLICI E MINZIONE ---
st.header("3. Cibo, Acqua e Idratazione")
st.write("*(Presto collegheremo il database USDA/FatSecret qui)*")
ha_mangiato = st.checkbox("Ho fatto un pasto completo (Rallenta l'assorbimento dell'alcol)")
bicchieri_acqua = st.number_input("Bicchieri d'acqua o analcolici bevuti", min_value=0, value=0)
eventi_minzione = st.number_input("Quante volte sei andato/a in bagno? (Aiuta a capire l'idratazione)", min_value=0, value=0)

st.divider()

# --- SEZIONE 4: IL CALCOLO ---
st.header("4. Risultato")
ore_trascorse = st.number_input("Ore trascorse dal primo drink", min_value=0.0, value=1.0, step=0.5)

if st.button("Calcola Tasso Alcolemico e Idratazione", type="primary"):
    # 1. Calcolo Tasso Alcolemico (Widmark)
    r = 0.68 if sesso == "Maschio" else 0.55
    if ha_mangiato:
        r += 0.1 # Il cibo aumenta il fattore r, abbassando il picco di alcol nel sangue
        
    if peso > 0 and st.session_state.totale_alcol_g > 0:
        bac_iniziale = st.session_state.totale_alcol_g / (peso * r)
        bac_finale = max(0.0, bac_iniziale - (0.15 * ore_trascorse))
    else:
        bac_finale = 0.0
        
    st.subheader(f"Tasso alcolemico stimato: {bac_finale:.2f} g/L")
    
    if bac_finale > 0.5:
        st.error("🚨 Hai superato il limite legale per guidare in Italia (0.5 g/L). Non metterti alla guida.")
    elif bac_finale > 0:
        st.warning("⚠️ Sei sotto il limite, ma i tuoi riflessi potrebbero essere alterati.")
    else:
        st.success("✅ Tasso alcolemico a zero.")

    # 2. Feedback sull'idratazione
    st.write("---")
    st.write("### Status Idratazione 💧")
    if bicchieri_acqua < len(st.session_state.lista_drink):
        st.warning("Attenzione: Stai bevendo meno acqua rispetto all'alcol. L'alcol disidrata! Bevi un bicchiere d'acqua per evitare i postumi.")
    else:
        st.success("Ottimo lavoro! Stai bevendo abbastanza acqua per mantenerti idratato.")
