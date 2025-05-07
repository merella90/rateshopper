import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import time

# Configurazione pagina
st.set_page_config(
    page_title="Rate Checker VOI Alimini (Xotelo API)",
    page_icon="📊",
    layout="wide"
)

# Abilita modalità debug
DEBUG_MODE = st.sidebar.checkbox("Modalità Debug", value=False)

# Funzione per log condizionale
def debug_log(message):
    if DEBUG_MODE:
        st.text(f"DEBUG: {message}")

# Classe per l'integrazione con Xotelo API
class XoteloAPI:
    def __init__(self):
        self.base_url = "https://data.xotelo.com/api"
        if DEBUG_MODE:
            st.write("🔌 API Xotelo inizializzata")
    
    def get_rates(self, hotel_key, check_in, check_out):
        """
        Ottieni le tariffe per un hotel specifico
        """
        endpoint = f"{self.base_url}/rates"
        params = {
            "hotel_key": hotel_key,
            "chk_in": check_in,
            "chk_out": check_out
        }
        
        if DEBUG_MODE:
            st.write(f"🔍 Richiesta tariffe per: {hotel_key}")
            st.write(f"📅 Check-in: {check_in}, Check-out: {check_out}")
            start_time = time.time()
        
        try:
            response = requests.get(endpoint, params=params)
            if DEBUG_MODE:
                end_time = time.time()
                st.write(f"⏱️ Tempo di risposta API: {end_time - start_time:.2f} secondi")
                st.write(f"📊 Stato risposta: {response.status_code}")
            return response.json()
        except Exception as e:
            if DEBUG_MODE:
                st.error(f"❌ Errore API: {str(e)}")
            return {"error": str(e), "timestamp": 0, "result": None}
    
    def get_hotel_list(self, location_key, offset=0, limit=30):
        """
        Ottieni un elenco di hotel in base alla posizione
        """
        endpoint = f"{self.base_url}/list"
        params = {
            "location_key": location_key,
            "offset": offset,
            "limit": limit
        }
        
        if DEBUG_MODE:
            st.write(f"🔍 Richiesta elenco hotel per località: {location_key}")
            start_time = time.time()
        
        try:
            response = requests.get(endpoint, params=params)
            if DEBUG_MODE:
                end_time = time.time()
                st.write(f"⏱️ Tempo di risposta API: {end_time - start_time:.2f} secondi")
            return response.json()
        except Exception as e:
            if DEBUG_MODE:
                st.error(f"❌ Errore API: {str(e)}")
            return {"error": str(e), "timestamp": 0, "result": None}

# Dizionario delle chiavi TripAdvisor per gli hotel competitor
hotel_keys = {
    "VOI Alimini": "g652004-d1799967",  
    "Ciaoclub Arco Del Saracino": "g946998-d947000", 
    "Hotel Alpiselect Robinson Apulia": "g947837-d949958",  
    "Alpiclub Hotel Thalas Club": "g1179328-d1159227" 
}

# Funzione per convertire la risposta API in DataFrame
def process_xotelo_response(response, hotel_name):
    """
    Elabora la risposta dell'API Xotelo e la converte in un DataFrame
    """
    if DEBUG_MODE:
        st.write(f"🔄 Elaborazione risposta per {hotel_name}")
        if response["error"] is not None:
            st.warning(f"⚠️ API ha restituito un errore: {response['error']}")
    
    if response["error"] is not None or response["result"] is None:
        if DEBUG_MODE:
            st.error(f"❌ Nessun dato disponibile per {hotel_name}")
        return pd.DataFrame()
    
    rates = response["result"].get("rates", [])
    check_in = response["result"].get("chk_in", "")
    check_out = response["result"].get("chk_out", "")
    
    if DEBUG_MODE:
        st.write(f"📈 Trovate {len(rates)} tariffe per {hotel_name}")
        st.write(f"🗓️ Periodo: {check_in} - {check_out}")
    
    data = []
    for rate in rates:
        data.append({
            "hotel": hotel_name,
            "ota": rate.get("name", ""),
            "ota_code": rate.get("code", ""),
            "price": rate.get("rate", 0),
            "check_in": check_in,
            "check_out": check_out,
            "timestamp": response["timestamp"]
        })
    
    df = pd.DataFrame(data)
    
    if DEBUG_MODE:
        if not df.empty:
            st.write(f"✅ DataFrame creato con successo: {df.shape[0]} righe x {df.shape[1]} colonne")
            st.write("Esempio di dati:")
            st.dataframe(df.head(3))
        else:
            st.warning("⚠️ DataFrame vuoto creato")
    
    return df

# Applicazione Streamlit
def rate_checker_app():
    st.title("Rate Checker VOI Alimini con Xotelo API")
    st.subheader("Confronto tariffe basato su TripAdvisor")
    
    # Mostra stato attuale
    if DEBUG_MODE:
        st.write("🔧 MODALITÀ DEBUG ATTIVA")
        st.write("📋 Stato della sessione:")
        st.write(f"- Dati tariffari presenti: {'rate_data' in st.session_state}")
        if 'rate_data' in st.session_state:
            st.write(f"- Numero di record: {len(st.session_state.rate_data)}")
            st.write(f"- Hotel disponibili: {list(st.session_state.rate_data['hotel'].unique())}")
    
    # Sidebar per i controlli
    st.sidebar.header("Parametri di ricerca")
    
    # Lista degli hotel
    competitors = list(hotel_keys.keys())
    selected_hotels = st.sidebar.multiselect(
        "Hotel da confrontare",
        competitors,
        default=competitors
    )
    
    # Date di check-in e check-out
    col1, col2 = st.sidebar.columns(2)
    with col1:
        check_in_date = st.date_input("Check-in", datetime.now())
    with col2:
        check_out_date = st.date_input("Check-out", datetime.now() + timedelta(days=3))
    
    # Log delle selezioni in modalità debug
    if DEBUG_MODE:
        st.sidebar.write("📋 Parametri selezionati:")
        st.sidebar.write(f"- Hotel: {selected_hotels}")
        st.sidebar.write(f"- Check-in: {check_in_date}")
        st.sidebar.write(f"- Check-out: {check_out_date}")
        st.sidebar.write(f"- Durata soggiorno: {(check_out_date - check_in_date).days} giorni")
    
    # Bottone per eseguire la ricerca
    if st.sidebar.button("Cerca tariffe"):
        # Inizializza l'API Xotelo
        xotelo_api = XoteloAPI()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with st.spinner("Recupero tariffe in corso..."):
            # Raccogli i dati per ciascun hotel selezionato
            all_data = []
            
            for i, hotel in enumerate(selected_hotels):
                progress = int(100 * i / len(selected_hotels))
                progress_bar.progress(progress)
                status_text.text(f"Elaborazione {hotel}... ({i+1}/{len(selected_hotels)})")
                
                hotel_key = hotel_keys.get(hotel, "")
                if hotel_key:
                    # Ottieni le tariffe dall'API
                    response = xotelo_api.get_rates(
                        hotel_key,
                        check_in_date.strftime("%Y-%m-%d"),
                        check_out_date.strftime("%Y-%m-%d")
                    )
                    
                    # Processa la risposta
                    df = process_xotelo_response(response, hotel)
                    
                    if not df.empty:
                        all_data.append(df)
                else:
                    if DEBUG_MODE:
                        st.warning(f"⚠️ Chiave TripAdvisor non trovata per {hotel}")
            
            progress_bar.progress(100)
            status_text.text("Elaborazione completata!")
            
            if all_data:
                # Combina tutti i DataFrame
                combined_df = pd.concat(all_data, ignore_index=True)
                
                # Memorizza i dati nella sessione
                st.session_state.rate_data = combined_df
                
                st.success(f"✅ Dati tariffari recuperati con successo! Trovate {len(combined_df)} tariffe per {len(selected_hotels)} hotel.")
                
                if DEBUG_MODE:
                    st.write("📊 Struttura dati:")
                    st.write(combined_df.info())
                    st.write("📈 Statistiche:")
                    st.write(combined_df.describe())
            else:
                st.error("❌ Nessun dato recuperato. Verifica le chiavi degli hotel e riprova.")
    
    # Visualizza i dati se disponibili
    if "rate_data" in st.session_state:
        # Ottieni il DataFrame
        df = st.session_state.rate_data
        
        # Visualizza la scheda principale
        st.header("Confronto tariffe tra OTA")
        
        # Seleziona l'hotel da analizzare
        selected_hotel = st.selectbox(
            "Seleziona hotel da analizzare",
            df["hotel"].unique()
        )
        
        # Filtra per l'hotel selezionato
        hotel_df = df[df["hotel"] == selected_hotel]
        
        if DEBUG_MODE:
            st.write(f"🔍 Analisi per {selected_hotel}")
            st.write(f"📋 Dati disponibili: {len(hotel_df)} tariffe da {len(hotel_df['ota'].unique())} OTA")
        
        if not hotel_df.empty:
            # Grafico delle tariffe per OTA
            fig = px.bar(
                hotel_df,
                x="ota",
                y="price",
                title=f"Tariffe per {selected_hotel} ({check_in_date.strftime('%d/%m/%Y')} - {check_out_date.strftime('%d/%m/%Y')})",
                color="ota",
                labels={"price": "Prezzo ($)", "ota": "OTA"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistiche principali
            col1, col2, col3 = st.columns(3)
            
            with col1:
                min_price = hotel_df["price"].min()
                min_ota = hotel_df.loc[hotel_df["price"].idxmin(), "ota"]
                st.metric("Prezzo minimo", f"${min_price:.2f}", f"via {min_ota}")
                if DEBUG_MODE:
                    st.write(f"🔍 Dettaglio: {min_ota} offre il prezzo più basso")
            
            with col2:
                max_price = hotel_df["price"].max()
                max_ota = hotel_df.loc[hotel_df["price"].idxmax(), "ota"]
                st.metric("Prezzo massimo", f"${max_price:.2f}", f"via {max_ota}")
                if DEBUG_MODE:
                    st.write(f"🔍 Dettaglio: {max_ota} ha il prezzo più alto")
            
            with col3:
                avg_price = hotel_df["price"].mean()
                price_range = max_price - min_price
                st.metric("Prezzo medio", f"${avg_price:.2f}", f"Range: ${price_range:.2f}")
                if DEBUG_MODE:
                    st.write(f"🔍 La variazione di prezzo è ${price_range:.2f} (±{(price_range/avg_price*100):.1f}%)")
            
            # Tabella completa dei dati
            st.subheader("Dettaglio tariffe per OTA")
            st.dataframe(
                hotel_df[["ota", "price"]].sort_values(by="price"),
                use_container_width=True
            )
        
        # Confronto tra hotel
        st.header("Confronto tra hotel")
        
        # Trova il prezzo minimo per ciascun hotel
        min_prices = df.groupby("hotel")["price"].min().reset_index()
        
        if DEBUG_MODE:
            st.write("📊 Analisi comparativa:")
            st.write(f"- Hotel più economico: {min_prices.loc[min_prices['price'].idxmin(), 'hotel']} (${min_prices['price'].min():.2f})")
            st.write(f"- Hotel più costoso: {min_prices.loc[min_prices['price'].idxmax(), 'hotel']} (${min_prices['price'].max():.2f})")
            st.write(f"- Differenza min-max: ${min_prices['price'].max() - min_prices['price'].min():.2f}")
        
        # Grafico di confronto
        fig = px.bar(
            min_prices,
            x="hotel",
            y="price",
            title=f"Prezzo minimo disponibile per hotel ({check_in_date.strftime('%d/%m/%Y')} - {check_out_date.strftime('%d/%m/%Y')})",
            color="hotel",
            labels={"price": "Prezzo minimo ($)", "hotel": "Hotel"}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabella di confronto
        st.subheader("Confronto prezzi minimi tra hotel")
        st.dataframe(min_prices.sort_values(by="price"), use_container_width=True)
        
        # Analisi parità tariffaria
        st.header("Analisi parità tariffaria")
        
        # Seleziona l'hotel di riferimento (default: VOI Alimini)
        reference_hotel = "VOI Alimini" if "VOI Alimini" in df["hotel"].unique() else df["hotel"].iloc[0]
        
        if DEBUG_MODE:
            st.write(f"🏨 Hotel di riferimento: {reference_hotel}")
        
        # Trova il prezzo minimo per l'hotel di riferimento
        ref_min_price = df[df["hotel"] == reference_hotel]["price"].min()
        
        if DEBUG_MODE:
            st.write(f"💰 Prezzo minimo di riferimento: ${ref_min_price:.2f}")
        
        # Confronta con gli altri hotel
        parity_data = []
        
        for hotel in df["hotel"].unique():
            if hotel != reference_hotel:
                min_price = df[df["hotel"] == hotel]["price"].min()
                price_diff = ref_min_price - min_price
                perc_diff = (price_diff / min_price) * 100 if min_price > 0 else 0
                
                if DEBUG_MODE:
                    st.write(f"🔄 Confronto con {hotel}: ${min_price:.2f} (diff: ${price_diff:.2f}, {perc_diff:.2f}%)")
                
                parity_data.append({
                    "hotel": hotel,
                    "min_price": min_price,
                    "price_diff": price_diff,
                    "perc_diff": perc_diff
                })
        
        parity_df = pd.DataFrame(parity_data)
        
        if not parity_df.empty:
            # Grafico della differenza percentuale
            fig = px.bar(
                parity_df,
                x="hotel",
                y="perc_diff",
                title=f"Differenza percentuale rispetto a {reference_hotel}",
                labels={"perc_diff": "Differenza (%)", "hotel": "Hotel"},
                color="perc_diff",
                color_continuous_scale=px.colors.diverging.RdBu_r
            )
            
            fig.update_layout(yaxis_tickformat=".2f")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabella di analisi
            st.subheader("Dettaglio analisi parità tariffaria")
            
            # Formatta i dati per la visualizzazione
            display_df = parity_df.copy()
            display_df["min_price"] = display_df["min_price"].apply(lambda x: f"${x:.2f}")
            display_df["price_diff"] = display_df["price_diff"].apply(lambda x: f"${x:.2f}")
            display_df["perc_diff"] = display_df["perc_diff"].apply(lambda x: f"{x:.2f}%")
            
            st.dataframe(display_df, use_container_width=True)
            
            if DEBUG_MODE:
                # Aggiungi un sommario dell'analisi
                st.write("📊 Sommario dell'analisi:")
                if all(parity_df["price_diff"] > 0):
                    st.write("✅ VOI Alimini ha prezzi più alti di tutti i competitor")
                elif all(parity_df["price_diff"] < 0):
                    st.write("⚠️ VOI Alimini ha prezzi più bassi di tutti i competitor")
                else:
                    higher = parity_df[parity_df["price_diff"] > 0]["hotel"].tolist()
                    lower = parity_df[parity_df["price_diff"] < 0]["hotel"].tolist()
                    st.write(f"ℹ️ VOI Alimini ha prezzi più alti di: {', '.join(higher) if higher else 'nessuno'}")
                    st.write(f"ℹ️ VOI Alimini ha prezzi più bassi di: {', '.join(lower) if lower else 'nessuno'}")
    else:
        st.info("ℹ️ Clicca su 'Cerca tariffe' per recuperare i dati tariffari")
    
    # Sezione informativa
    with st.expander("Come trovare la chiave TripAdvisor dell'hotel"):
        st.write("""
        Per utilizzare questa app, è necessario avere la chiave TripAdvisor per ciascun hotel. Ecco come trovarla:
        
        1. Vai alla pagina dell'hotel su TripAdvisor
        2. Osserva l'URL, che sarà simile a: `https://www.tripadvisor.com/Hotel_Review-g1234567-d12345678-Reviews-Hotel_Name.html`
        3. La chiave è la parte `g1234567-d12345678`
        
        Sostituisci le chiavi di esempio nel codice con quelle reali degli hotel che desideri monitorare.
        """)
    
    # Footer con informazioni di sessione in modalità debug
    if DEBUG_MODE:
        st.divider()
        st.write("### 📋 Informazioni di sessione")
        st.write(f"- Timestamp corrente: {datetime.now()}")
        st.write(f"- Chiavi in session_state: {list(st.session_state.keys())}")
        memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024 if 'rate_data' in st.session_state else 0
        st.write(f"- Utilizzo memoria DataFrame: {memory_usage:.2f} MB")

# Esegui l'app
if __name__ == "__main__":
    rate_checker_app()
