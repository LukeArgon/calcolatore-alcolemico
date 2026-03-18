import streamlit as st
import pandas as pd
import glob
import os

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="DrinkSafe Pro", page_icon="🍷", layout="centered")

# --- FUNZIONE CARICAMENTO DATI (OTTIMIZZATA) ---
@st.cache_data
def load_all_data():
    # 1. Caricamento Cocktail
    df_cocktails = pd.DataFrame()
    if os.path.exists('data_cocktails.csv'):
        df_cocktails = pd.read_csv('data_cocktails.csv')
    
    # 2. Caricamento Cibo (Unione dei gruppi e rimozione doppioni)
    food_list = []
    # Cerchiamo tutti i file FOOD-DATA e fastfood
    for f in glob.glob('FOOD-DATA-GROUP*.csv'):
        temp_df = pd.read_csv(f, usecols=['food'])
        food_list.append(temp_df.rename(columns={'food': 'item_name'}))
        
    if os.path.exists('fastfood_calories.csv'):
        ff_df = pd.read_csv('fastfood_calories.csv', usecols=['restaurant', 'item'])
        ff_df['item_name'] = ff_df['restaurant'] + " - " + ff_df['item']
        food_list.append(ff_df[['item_name']])
        
    if food_list:
        full_food_df = pd.concat(food_list, ignore_index=True)
        # Pulizia: rimuoviamo spazi, rendiamo minuscolo per trovare doppioni, poi teniamo l'originale
        full_food_df['clean'] = full_food_df['item_name'].str.lower().str.strip()
        full_food_df = full_food_df.drop_duplicates(subset=['clean']).sort_values('clean')
        final_food_list = full_food_df['item_name'].tolist()
    else:
        final_food_list = []
        
    return df_cocktails, final_food_list

# Carichiamo i database
db_cocktails, list_food = load_all_data()

# Dizionario ABV per calcolo automatico
abv_map = {
    "vodka": 40.0, "gin": 40.0, "rum": 40.0, "tequila": 40.0, "whiskey": 40.0, 
    "bourbon": 40.0, "triple sec": 30.0, "cointreau": 40.0, "amaretto": 28.0,
    "campari": 25.0, "aperol": 11.0, "vermouth": 15.0, "wine": 12.0, "beer": 5.0
}

# --- STATO DELLA SESSIONE ---
if 'total_alcohol_g' not in st.session_state: st.session_state.total_alcohol_g = 0.0
if 'log' not in st.session_state: st.session_state.log = []

st.title("🍹 DrinkSafe: Calcolatore Alcolemico")
st.markdown("Database offline caricato con successo da GitHub.")

# --- INPUT UTENTE ---
with st.sidebar:
    st.header("👤 Tuoi Dati")
    weight = st.number_input("Peso (kg)", 40, 150, 70)
    gender = st.selectbox("Sesso", ["Maschio", "Femmina"])
    st.divider()
    if st.button("Svuota Sessione (Reset)"):
        st.session_state.total_alcohol_g = 0.0
        st.session_state.log = []
        st.rerun()

# --- SEZIONE AGGIUNTA CONSUMI ---
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🍸 Drink")
    if not db_cocktails.empty:
        drink_names = sorted(db_cocktails['strDrink'].unique().tolist())
        selected_drink = st.selectbox("Seleziona Cocktail:", [""] + drink_names)
        
        if st.button("Aggiungi Drink") and selected_drink != "":
            # Filtriamo gli ingredienti del cocktail scelto
            ingredients = db_cocktails[db_cocktails['strDrink'] == selected_drink]
            drink_alc_g = 0.0
            
            for _, row in ingredients.iterrows():
                ml = pd.to_numeric(row['Value_ml'], errors='coerce')
                ing_name = str(row['strIngredients']).lower()
                if ml > 0:
                    # Cerchiamo l'ABV nel dizionario
                    abv = 0.0
                    for key, val in abv_map.items():
                        if key in ing_name:
                            abv = val
                            break
                    drink_alc_g += (ml * (abv / 100) * 0.8)
            
            st.session_state.total_alcohol_g += drink_alc_g
            st.session_state.log.append(f"Drink: {selected_drink} ({drink_alc_g:.1f}g alcol)")
            st.toast(f"Aggiunto {selected_drink}!")

with col_b:
    st.subheader("🍔 Cibo")
    if list_food:
        selected_food = st.selectbox("Cerca Alimento:", [""] + list_food)
        if st.button("Aggiungi Cibo") and selected_food != "":
            st.session_state.log.append(f"Cibo: {selected_food}")
            st.toast(f"Registrato: {selected_food}")

# --- CALCOLO FINALE ---
st.divider()
st.subheader("📝 Riepilogo Consumi")
for entry in st.session_state.log:
    st.caption(entry)

hours = st.slider("Ore passate dal primo sorso:", 0.0, 10.0, 1.0)

if st.button("CALCOLA TASSO ALCOLEMICO", type="primary"):
    # Formula di Widmark
    r = 0.68 if gender == "Maschio" else 0.55
    # Bonus cibo
    if any("Cibo:" in entry for entry in st.session_state.log):
        r += 0.1
    
    # BAC = (Alcol_g / (Peso * r)) - (Beta * ore)
    bac = (st.session_state.total_alcohol_g / (weight * r)) - (0.15 * hours)
    bac = max(0.0, bac)
    
    st.header(f"Tasso Stimato: {bac:.2f} g/L")
    
    if bac >= 0.5:
        st.error("⚠️ SEI SOPRA IL LIMITE LEGALE (0.5 g/L). Non guidare!")
    elif bac > 0:
        st.warning("⚖️ Sei sotto il limite, ma la tua attenzione è comunque ridotta.")
    else:
        st.success("✅ Sei a zero. Guida con prudenza!")
