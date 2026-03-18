import streamlit as st
import pandas as pd
import glob
import os

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="SafeNight: Alcol & Idratazione", page_icon="🛡️", layout="wide")

# --- CARICAMENTO DATI ---
@st.cache_data
def load_all_data():
    # Cocktail
    df_cocktails = pd.read_csv('data_cocktails.csv') if os.path.exists('data_cocktails.csv') else pd.DataFrame()
    # Cibo
    food_list = []
    for f in glob.glob('FOOD-DATA-GROUP*.csv'):
        temp_df = pd.read_csv(f, usecols=['food'])
        food_list.append(temp_df.rename(columns={'food': 'item_name'}))
    if os.path.exists('fastfood_calories.csv'):
        ff_df = pd.read_csv('fastfood_calories.csv', usecols=['restaurant', 'item'])
        ff_df['item_name'] = ff_df['restaurant'] + " - " + ff_df['item']
        food_list.append(ff_df[['item_name']])
    
    if food_list:
        full_food_df = pd.concat(food_list, ignore_index=True)
        full_food_df['clean'] = full_food_df['item_name'].str.lower().str.strip()
        full_food_df = full_food_df.drop_duplicates(subset=['clean']).sort_values('clean')
        final_food_list = full_food_df['item_name'].tolist()
    else:
        final_food_list = []
    return df_cocktails, final_food_list

db_cocktails, list_food = load_all_data()

# --- STATO DELLA SESSIONE (MEMORIA) ---
if 'total_alc_g' not in st.session_state: st.session_state.total_alc_g = 0.0
if 'num_drinks' not in st.session_state: st.session_state.num_drinks = 0
if 'water_glasses' not in st.session_state: st.session_state.water_glasses = 0
if 'pee_events' not in st.session_state: st.session_state.pee_events = 0
if 'log' not in st.session_state: st.session_state.log = []

# --- SIDEBAR: PROFILO & RESET ---
with st.sidebar:
    st.header("👤 Profilo Utente")
    weight = st.number_input("Peso (kg)", 40, 150, 70)
    gender = st.selectbox("Sesso", ["Maschio", "Femmina"])
    st.divider()
    if st.button("🗑️ Reset Totale Sessione"):
        st.session_state.total_alc_g = 0.0
        st.session_state.num_drinks = 0
        st.session_state.water_glasses = 0
        st.session_state.pee_events = 0
        st.session_state.log = []
        st.rerun()

# --- HEADER: METRICHE IN TEMPO REALE ---
st.title("🛡️ SafeNight Tracker")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("🍷 Drink Assunti", st.session_state.num_drinks)
col_m2.metric("⚖️ Alcol Totale (g)", f"{st.session_state.total_alc_g:.1f}")
col_m3.metric("💧 Acqua (Bicchieri)", st.session_state.water_glasses)
col_m4.metric("🚽 Minzione", st.session_state.pee_events)

st.divider()

# --- SEZIONE INPUT ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📥 Registra Consumi")
    
    # Cocktail dal Database
    if not db_cocktails.empty:
        drink_names = sorted(db_cocktails['strDrink'].unique().tolist())
        selected_drink = st.selectbox("Seleziona Cocktail (Database):", [""] + drink_names)
        if st.button("➕ Aggiungi Cocktail"):
            if selected_drink != "":
                ingredients = db_cocktails[db_cocktails['strDrink'] == selected_drink]
                calc_g = (pd.to_numeric(ingredients['Value_ml'], errors='coerce').sum()) * 0.12 * 0.8 # Stima media
                st.session_state.total_alc_g += calc_g
                st.session_state.num_drinks += 1
                st.session_state.log.append(f"Drink: {selected_drink} (+{calc_g:.1f}g)")
                st.rerun()

    # Cibo dal Database
    st.write("---")
    if list_food:
        selected_food = st.selectbox("Seleziona Cibo (Database):", [""] + list_food)
        if st.button("🍞 Aggiungi Cibo"):
            if selected_food != "":
                st.session_state.log.append(f"Cibo: {selected_food}")
                st.rerun()

with col_right:
    st.subheader("💧 Idratazione & Salute")
    
    # Acqua e Analcolici
    c_water1, c_water2 = st.columns([3, 1])
    with c_water1:
        st.write("Bicchiere d'acqua o analcolico (200ml)")
    with c_water2:
        if st.button("💧 +1"):
            st.session_state.water_glasses += 1
            st.session_state.log.append("Idratazione: +1 bicchiere acqua")
            st.rerun()
            
    # Minzione
    c_pee1, c_pee2 = st.columns([3, 1])
    with c_pee1:
        st.write("Evento di minzione (Bagno)")
    with c_pee2:
        if st.button("🚽 +1"):
            st.session_state.pee_events += 1
            st.session_state.log.append("Evento: Minzione")
            st.rerun()

# --- CALCOLO FINALE ---
st.divider()
st.subheader("📊 Calcolo Tasso Alcolemico (Widmark)")

col_res1, col_res2 = st.columns(2)
with col_res1:
    hours = st.slider("Ore passate dal primo drink:", 0.0, 12.0, 1.0)
    if st.button("🚀 CALCOLA RISULTATO", type="primary"):
        r = 0.68 if gender == "Maschio" else 0.55
        # Bonus cibo
        if any("Cibo:" in entry for entry in st.session_state.log):
            r += 0.1
        
        bac = (st.session_state.total_alc_g / (weight * r)) - (0.15 * hours)
        bac = max(0.0, bac)
        
        st.session_state.current_bac = bac
        
with col_res2:
    if 'current_bac' in st.session_state:
        bac = st.session_state.current_bac
        st.header(f"Tasso: {bac:.2f} g/L")
        if bac >= 0.5:
            st.error("🚨 SOPRA IL LIMITE LEGALE. Non guidare!")
        elif bac > 0:
            st.warning("⚠️ Sotto il limite, ma riflessi alterati.")
        else:
            st.success("✅ Tasso zero.")
            
        # Suggerimento Idratazione
        if st.session_state.water_glasses < st.session_state.num_drinks:
            st.info("💡 Consiglio: Bevi almeno un bicchiere d'acqua per ogni drink per evitare la disidratazione.")

# Registro attività
with st.expander("📝 Vedi Cronologia Attività"):
    for entry in reversed(st.session_state.log):
        st.write(entry)
