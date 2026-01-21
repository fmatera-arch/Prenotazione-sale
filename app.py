import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, timedelta

# --- CONFIGURAZIONE ---
SALE = ["Sala Blu", "Sala Verde"]
ORARIO_APERTURA = 9
ORARIO_CHIUSURA = 18

# --- CONNESSIONE GOOGLE SHEETS ---
def get_google_sheet():
    # Usa le credenziali salvate nei "Secrets" di Streamlit
    credentials = dict(st.secrets["gcp_service_account"])
    
    # Autenticazione
    gc = gspread.service_account_from_dict(credentials)
    
    # Apre il foglio (assicurati che il nome sia corretto o usa l'URL)
    # Sostituisci 'Prenotazioni Sale' con il NOME ESATTO del tuo file su Google Drive
    sh = gc.open("Prenotazione Sale") 
    return sh.sheet1

# --- FUNZIONI DI GESTIONE DATI ---
def carica_dati():
    worksheet = get_google_sheet()
    data = worksheet.get_all_records()
    return data

def aggiungi_prenotazione(nuova_prenotazione):
    worksheet = get_google_sheet()
    # Aggiunge una riga al foglio
    worksheet.append_row([
        nuova_prenotazione["nome"],
        nuova_prenotazione["sala"],
        nuova_prenotazione["data"],
        nuova_prenotazione["inizio"],
        nuova_prenotazione["fine"]
    ])

def controlla_sovrapposizione(nuova, esistenti):
    fmt = "%d-%m-%Y %H:%M"
    inizio_nuovo = datetime.strptime(f"{nuova['data']} {nuova['inizio']}", fmt)
    fine_nuovo = datetime.strptime(f"{nuova['data']} {nuova['fine']}", fmt)

    for p in esistenti:
        if p['sala'] == nuova['sala']:
            # Verifica che i campi non siano vuoti (sicurezza per righe sporche nel foglio)
            if not p['data'] or not p['inizio']: continue
            
            inizio_p = datetime.strptime(f"{p['data']} {p['inizio']}", fmt)
            fine_p = datetime.strptime(f"{p['data']} {p['fine']}", fmt)
            
            if inizio_nuovo < fine_p and fine_nuovo > inizio_p:
                return True
    return False

# --- INTERFACCIA UTENTE ---
st.set_page_config(page_title="Gestione Sale - Google Sheets", layout="wide")
st.title("☁️ Prenotazioni Sale (Cloud)")

# Caricamento dati (con gestione errori)
try:
    prenotazioni = carica_dati()
except Exception as e:
    st.error(f"Errore di connessione a Google Sheets: {e}")
    st.stop()

# --- SIDEBAR ---
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

    if st.button("Conferma Prenotazione", type="primary"):
        if ora_inizio >= ora_fine:
            st.error("L'ora di fine deve essere dopo l'ora di inizio.")
        else:
            nuova = {
                "nome": nome,
                "sala": sala,
                "data": str(data),
                "inizio": str(ora_inizio)[:5],
                "fine": str(ora_fine)[:5]
            }
            
            if controlla_sovrapposizione(nuova, prenotazioni):
                st.error(f"❌ La {sala} è già occupata!")
            else:
                with st.spinner('Salvataggio su Google Sheets in corso...'):
                    aggiungi_prenotazione(nuova)
                st.success("✅ Salvato su Google Sheets!")
                st.rerun()

# --- VISUALIZZAZIONE ---
col_sx, col_dx = st.columns([2, 1])

with col_sx:
    st.subheader(f"📅 Disponibilità: {data.strftime('%d/%m/%Y')}")
    df_schedule = pd.DataFrame(index=range(ORARIO_APERTURA, ORARIO_CHIUSURA + 1), columns=SALE).fillna("✅ Libera")

    prenotazioni_giorno = [p for p in prenotazioni if str(p['data']) == str(data)]
    
    for p in prenotazioni_giorno:
        try:
            h_start = int(str(p['inizio']).split(':')[0])
            h_end = int(str(p['fine']).split(':')[0])
            for h in range(h_start, h_end):
                if h in df_schedule.index:
                    df_schedule.at[h, p['sala']] = f"🔴 {p['nome']}"
        except:
            pass # Ignora errori di formato nel foglio

    st.dataframe(df_schedule, use_container_width=True, height=400)

with col_dx:
    st.subheader("📋 Lista Completa (da Sheets)")
    if prenotazioni:
        st.dataframe(pd.DataFrame(prenotazioni), hide_index=True, use_container_width=True)