import streamlit as st
import requests  # <-- NUOVA LIBRERIA: Serve per scaricare i dati da internet

# --- IMPOSTAZIONI DELLA PAGINA ---
st.set_page_config(page_title="Calcolatore Tasso Alcolemico", page_icon="🍷")
st.title("Calcolatore Avanzato Tasso Alcolemico")
st.write("Questa app stima il tuo tasso alcolemico basandosi su quello che hai bevuto e mangiato.")

# --- NUOVA SEZIONE: RICERCA DRINK (TheCocktailDB) ---
st.header("🍹 Cerca il tuo Drink")
st.write("Cerca un cocktail nel database globale per aggiungerlo al calcolo.")

# Creiamo una casella di testo per l'utente
nome_drink = st.text_input("Inserisci il nome del drink (es. Margarita, Mojito):")

# Quando l'utente preme il bottone, eseguiamo la ricerca
if st.button("Cerca Drink"):
    if nome_drink:
        # 1. Prepariamo l'indirizzo (URL) dell'API con il nome del drink
        url_api = f"https://www.thecocktaildb.com/api/json/v1/1/search.php?s={nome_drink}"
        
        # 2. Facciamo la "telefonata" all'API
        risposta = requests.get(url_api)
        dati = risposta.json() # Traduciamo la risposta in un formato leggibile da Python
        
        # 3. Controlliamo se abbiamo trovato qualcosa
        if dati['drinks']:
            # Prendiamo il primo drink dalla lista dei risultati
            drink_trovato = dati['drinks'][0]
            nome = drink_trovato['strDrink']
            bicchiere = drink_trovato['strGlass']
            
            st.success(f"Trovato: {nome}!")
            st.write(f"**Tipo di bicchiere:** {bicchiere}")
            st.write("**Ingredienti principali:**")
            
            # Mostriamo i primi 3 ingredienti (se esistono) per capire cosa c'è dentro
            for i in range(1, 4):
                ingrediente = drink_trovato.get(f'strIngredient{i}')
                misura = drink_trovato.get(f'strMeasure{i}')
                if ingrediente:
                    st.write(f"- {misura if misura else ''} {ingrediente}")
                    
            st.info("💡 Prossimo step per l'app: calcoleremo i grammi di alcol esatti basandoci su questi ingredienti!")
            
        else:
            st.error("Nessun drink trovato con questo nome. Prova a scriverlo in inglese o cerca un altro drink!")
    else:
        st.warning("Per favore, scrivi il nome di un drink prima di cercare.")

st.divider() # Linea di separazione visiva

# --- SEZIONE 1 E 2: DATI E CALCOLO BASE (Come prima) ---
st.header("1. I tuoi dati")
col1, col2 = st.columns(2)

with col1:
    peso = st.number_input("Inserisci il tuo peso (in kg)", min_value=30, max_value=200, value=70)
with col2:
    sesso = st.selectbox("Seleziona il tuo sesso", ["Maschio", "Femmina"])

st.header("2. Consumo manuale e Calcolo")
grammi_alcol = st.number_input("Grammi di alcol puro assunti temporanei", min_value=0.0, value=12.0)
ore_trascorse = st.number_input("Ore trascorse", min_value=0.0, value=1.0)
cibo_assunto = st.checkbox("Ho mangiato")

if st.button("Calcola Tasso Alcolemico"):
    r = 0.68 if sesso == "Maschio" else 0.55
    if cibo_assunto:
        r += 0.1
    bac = grammi_alcol / (peso * r) if peso > 0 else 0.0
    bac_finale = max(0.0, bac - (0.15 * ore_trascorse))
    
    st.success(f"Tasso alcolemico stimato: {bac_finale:.2f} g/L")
