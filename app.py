import streamlit as st

# --- IMPOSTAZIONI DELLA PAGINA ---
st.set_page_config(page_title="Calcolatore Tasso Alcolemico", page_icon="🍷")

st.title("Calcolatore Avanzato Tasso Alcolemico")
st.write("Questa app stima il tuo tasso alcolemico basandosi su quello che hai bevuto e mangiato.")

# --- SEZIONE 1: DATI DEL SOGGETTO ---
st.header("1. I tuoi dati")
col1, col2 = st.columns(2) # Creiamo due colonne affiancate per un design più pulito

with col1:
    peso = st.number_input("Inserisci il tuo peso (in kg)", min_value=30, max_value=200, value=70)
with col2:
    sesso = st.selectbox("Seleziona il tuo sesso", ["Maschio", "Femmina"])

# --- SEZIONE 2: INSERIMENTO BEVANDE E CIBO ---
st.header("2. Consumi")
st.write("*(Nelle prossime fasi collegheremo questa sezione alle API per cercare prodotti reali)*")

# Per ora usiamo dei campi numerici base per testare la logica
grammi_alcol = st.number_input("Grammi di alcol puro assunti (es. un drink = ~12g)", min_value=0.0, value=0.0)
ore_trascorse = st.number_input("Ore trascorse dall'inizio della bevuta", min_value=0.0, value=1.0)
cibo_assunto = st.checkbox("Ho mangiato prima o durante il consumo di alcol")
eventi_minzione = st.number_input("Numero di eventi di minzione (opzionale)", min_value=0, value=0)

# --- SEZIONE 3: IL CALCOLO ---
st.header("3. Risultato")

# Funzione base per calcolare il tasso alcolemico (Formula di Widmark semplificata)
def calcola_tasso_alcolemico(peso, sesso, grammi_alcol, ore, ha_mangiato):
    # Il "fattore di distribuzione" varia in base al sesso
    se_maschio = 0.68
    se_femmina = 0.55
    r = se_maschio if sesso == "Maschio" else se_femmina
    
    # Se la persona ha mangiato, l'assorbimento è minore e più lento (semplificazione)
    if ha_mangiato:
        r = r + 0.1 # Aumentando r, si abbassa il picco del tasso calcolato
        
    # Calcolo base: (Alcol in grammi) / (Peso in kg * fattore r)
    if peso > 0 and r > 0:
        bac = grammi_alcol / (peso * r)
    else:
        bac = 0.0
        
    # Sottraiamo l'alcol smaltito nel tempo (in media 0.15 grammi/litro all'ora)
    bac_finale = bac - (0.15 * ore)
    
    # Il tasso non può essere negativo
    return max(0.0, bac_finale)

# Bottone per avviare il calcolo
if st.button("Calcola Tasso Alcolemico"):
    risultato = calcola_tasso_alcolemico(peso, sesso, grammi_alcol, ore_trascorse, cibo_assunto)
    st.success(f"Il tuo tasso alcolemico stimato è: {risultato:.2f} g/L")
    
    # Aggiungiamo un piccolo feedback visivo in base al risultato
    if risultato > 0.5:
        st.warning("Attenzione: Hai superato il limite legale per la guida in Italia (0.5 g/L).")
    elif risultato > 0:
        st.info("Sei sotto il limite legale, ma ricorda che è sempre meglio non guidare se si ha bevuto.")
