import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta

# --- CONFIGURAZIONE ---
FILE_DATI = 'prenotazioni.json'
SALE = ["Sala Blu", "Sala Verde"]
ORARIO_APERTURA = 9
ORARIO_CHIUSURA = 18

# --- FUNZIONI DI GESTIONE DATI ---
def carica_dati():
    if not os.path.exists(FILE_DATI):
        return []
    with open(FILE_DATI, 'r') as f:
        return json.load(f)

def salva_dati(dati):
    with open(FILE_DATI, 'w') as f:
        json.dump(dati, f, indent=4)

def controlla_sovrapposizione(nuova_prenotazione, prenotazioni_esistenti):
    # Converte stringhe orario in oggetti datetime per il confronto
    fmt = "%Y-%m-%d %H:%M"
    inizio_nuovo = datetime.strptime(f"{nuova_prenotazione['data']} {nuova_prenotazione['inizio']}", fmt)
    fine_nuovo = datetime.strptime(f"{nuova_prenotazione['data']} {nuova_prenotazione['fine']}", fmt)

    for p in prenotazioni_esistenti:
        if p['sala'] == nuova_prenotazione['sala']:
            inizio_p = datetime.strptime(f"{p['data']} {p['inizio']}", fmt)
            fine_p = datetime.strptime(f"{p['data']} {p['fine']}", fmt)
            
            # Logica di sovrapposizione
            if inizio_nuovo < fine_p and fine_nuovo > inizio_p:
                return True # C'è sovrapposizione
    return False

# --- INTERFACCIA UTENTE (STREAMLIT) ---
st.set_page_config(page_title="Gestione Sale Meeting", layout="wide")

st.title("📅 Gestione Prenotazioni Sale Meeting")
st.markdown("Sistema di prenotazione per **Sala Blu** e **Sala Verde**")

# Carica i dati
prenotazioni = carica_dati()

# --- SIDEBAR: NUOVA PRENOTAZIONE ---
with st.sidebar:
    st.header("➕ Nuova Prenotazione")
    nome = st.text_input("Nome Prenotante")
    sala = st.selectbox("Seleziona Sala", SALE)
    data = st.date_input("Data", datetime.today())
    
    col1, col2 = st.columns(2)
    with col1:
        ora_inizio = st.time_input("Ora Inizio", datetime.now().replace(minute=0, second=0))
    with col2:
        ora_fine = st.time_input("Ora Fine", (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0))

    btn_prenota = st.button("Conferma Prenotazione", type="primary")

    if btn_prenota:
        if ora_inizio >= ora_fine:
            st.error("Errore: L'ora di fine deve essere dopo l'ora di inizio.")
        else:
            nuova = {
                "nome": nome,
                "sala": sala,
                "data": str(data),
                "inizio": str(ora_inizio)[:5], # Prende solo HH:MM
                "fine": str(ora_fine)[:5]
            }
            
            if controlla_sovrapposizione(nuova, prenotazioni):
                st.error(f"❌ La {sala} è già occupata in questo orario!")
            else:
                prenotazioni.append(nuova)
                salva_dati(prenotazioni)
                st.success(f"✅ Prenotazione confermata per {nome}!")
                st.rerun() # Ricarica la pagina per aggiornare la tabella

# --- AREA PRINCIPALE: VISUALIZZAZIONE ---

col_sx, col_dx = st.columns([2, 1])

with col_sx:
    st.subheader(f"📅 Disponibilità del giorno: {data.strftime('%d/%m/%Y')}")
    
    # Creiamo un DataFrame per visualizzare la giornata
    df_schedule = pd.DataFrame(index=range(ORARIO_APERTURA, ORARIO_CHIUSURA + 1), columns=SALE)
    df_schedule = df_schedule.fillna("✅ Libera") # Riempiamo tutto come libero

    # Riempiamo il tabellone con le prenotazioni del giorno selezionato
    prenotazioni_giorno = [p for p in prenotazioni if p['data'] == str(data)]
    
    for p in prenotazioni_giorno:
        h_start = int(p['inizio'].split(':')[0])
        h_end = int(p['fine'].split(':')[0])
        # Se l'orario non è "tondo" (es 10:30), arrotondiamo per semplicità visiva in questa demo
        
        for h in range(h_start, h_end):
            if h in df_schedule.index:
                df_schedule.at[h, p['sala']] = f"🔴 {p['nome']} ({p['inizio']}-{p['fine']})"

    # Mostriamo la tabella colorata
    st.dataframe(df_schedule, use_container_width=True, height=400)

with col_dx:
    st.subheader("📋 Tutte le prenotazioni future")
    if prenotazioni:
        df_tutti = pd.DataFrame(prenotazioni)
        # Ordiniamo per data e ora
        df_tutti = df_tutti.sort_values(by=["data", "inizio"])
        st.dataframe(
            df_tutti[["data", "sala", "inizio", "fine", "nome"]], 
            hide_index=True, 
            use_container_width=True
        )
        
        # Pulsante per cancellare tutto (Opzionale per test)
        if st.button("Reset Database (Cancella Tutto)"):
            salva_dati([])
            st.warning("Database resettato!")
            st.rerun()
    else:
        st.info("Nessuna prenotazione futura.")