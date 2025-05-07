import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json

# Configurazione pagina
st.set_page_config(
    page_title="Rate Checker VOI Alimini (Xotelo API)",
    page_icon="📊",
    layout="wide"
)

# Definisci un tasso di cambio fisso (aggiornarlo manualmente se necessario)
USD_TO_EUR = 0.92  # Tasso di cambio fisso USD a EUR

# Classe per l'integrazione con Xotelo API
class XoteloAPI:
    def __init__(self):
        self.base_url = "https://data.xotelo.com/api"
    
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
        
        try:
            response = requests.get(endpoint, params=params)
            return response.json()
        except Exception as e:
            return {"error": str(e), "timestamp": 0, "result": None}

# Dizionario delle chiavi TripAdvisor per gli hotel competitor
hotel_keys = {
    "VOI Alimini": "g652004-d1799967",  
    "Ciaoclub Arco Del Saracino": "g946998-d947000", 
    "Hotel Alpiselect Robinson Apulia": "g947837-d949958",  
    "Alpiclub Hotel Thalas Club": "g1179328-d1159227" 
}

# Funzione per convertire la risposta API in DataFrame
def process_xotelo_response(response, hotel_name, show_in_eur=True):
    """
    Elabora la risposta dell'API Xotelo e la converte in un DataFrame
    """
    if response["error"] is not None or response["result"] is None:
        return pd.DataFrame()
    
    rates = response["result"].get("rates", [])
    check_in = response["result"].get("chk_in", "")
    check_out = response["result"].get("chk_out", "")
    
    data = []
    for rate in rates:
        # Conversione diretta da USD a EUR
        usd_price = rate.get("rate", 0)
        eur_price = usd_price * USD_TO_EUR if show_in_eur else usd_price
        
        data.append({
            "hotel": hotel_name,
            "ota": rate.get("name", ""),
            "ota_code": rate.get("code", ""),
            "price": eur_price,      # Il prezzo già convertito in EUR
            "currency": "EUR" if show_in_eur else "USD",
            "check_in": check_in,
            "check_out": check_out,
            "timestamp": response["timestamp"]
        })
    
    return pd.DataFrame(data)

# Applicazione Streamlit
def rate_checker_app():
    st.title("Rate Checker VOI Alimini con Xotelo API")
    st.subheader("Confronto tariffe basato su TripAdvisor")
    
    # Sidebar per i controlli
    st.sidebar.header("Parametri di ricerca")
    
    # Selezione della valuta (sempre impostata su EUR)
    currency = "EUR"
    st.sidebar.text(f"Valuta: {currency}")
    
    # Debug mode
    debug_mode = st.sidebar.checkbox("Modalità Debug", value=False)
    
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
    
    # Bottone per eseguire la ricerca
    if st.sidebar.button("Cerca tariffe"):
        # Inizializza l'API Xotelo
        xotelo_api = XoteloAPI()
        
        with st.spinner("Recupero tariffe in corso..."):
            # Raccogli i dati per ciascun hotel selezionato
            all_data = []
            
            # Mostra stato debug se abilitato
            progress_bar = st.progress(0)
            status_text = st.empty()
            
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
                    
                    if debug_mode:
                        st.write(f"Risposta per {hotel}:")
                        st.json(response)
                    
                    # Processa la risposta (sempre in EUR)
                    df = process_xotelo_response(response, hotel, show_in_eur=True)
                    
                    if not df.empty:
                        if debug_mode:
                            st.write(f"DataFrame per {hotel}:")
                            st.write(df)
                        
                        all_data.append(df)
                    else:
                        st.warning(f"Nessun dato trovato per {hotel}")
            
            progress_bar.progress(100)
            status_text.text("Elaborazione completata!")
            
            if all_data:
                # Combina tutti i DataFrame
                combined_df = pd.concat(all_data, ignore_index=True)
                
                if debug_mode:
                    st.write("DataFrame combinato:")
                    st.write(combined_df)
                
                # Memorizza i dati nella sessione
                st.session_state.rate_data = combined_df
                
                st.success(f"Dati tariffari recuperati con successo per {len(all_data)} hotel!")
            else:
                st.error("Nessun dato recuperato. Verifica le chiavi degli hotel e riprova.")
    
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
        
        if not hotel_df.empty:
            # Grafico delle tariffe per OTA
            fig = px.bar(
                hotel_df,
                x="ota",
                y="price",
                title=f"Tariffe per {selected_hotel} ({check_in_date.strftime('%d/%m/%Y')} - {check_out_date.strftime('%d/%m/%Y')})",
                color="ota",
                labels={"price": f"Prezzo (€)", "ota": "OTA"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistiche principali
            col1, col2, col3 = st.columns(3)
            
            with col1:
                min_price = hotel_df["price"].min()
                min_ota = hotel_df.loc[hotel_df["price"].idxmin(), "ota"]
                st.metric("Prezzo minimo", f"€{min_price:.2f}", f"via {min_ota}")
            
            with col2:
                max_price = hotel_df["price"].max()
                max_ota = hotel_df.loc[hotel_df["price"].idxmax(), "ota"]
                st.metric("Prezzo massimo", f"€{max_price:.2f}", f"via {max_ota}")
            
            with col3:
                avg_price = hotel_df["price"].mean()
                price_range = max_price - min_price
                st.metric("Prezzo medio", f"€{avg_price:.2f}", f"Range: €{price_range:.2f}")
            
            # Tabella completa dei dati
            st.subheader("Dettaglio tariffe per OTA")
            # Creiamo una copia del dataframe per la visualizzazione
            display_df = hotel_df[["ota", "price"]].sort_values(by="price").copy()
            # Formatta i prezzi come euro
            display_df["price"] = display_df["price"].apply(lambda x: f"€{x:.2f}")
            st.dataframe(display_df, use_container_width=True)
        
        # Confronto tra hotel
        st.header("Confronto tra hotel")
        
        # Trova il prezzo minimo per ciascun hotel
        min_prices = df.groupby("hotel")["price"].min().reset_index()
        
        # Grafico di confronto
        fig = px.bar(
            min_prices,
            x="hotel",
            y="price",
            title=f"Prezzo minimo disponibile per hotel ({check_in_date.strftime('%d/%m/%Y')} - {check_out_date.strftime('%d/%m/%Y')})",
            color="hotel",
            labels={"price": f"Prezzo minimo (€)", "hotel": "Hotel"}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabella di confronto
        st.subheader("Confronto prezzi minimi tra hotel")
        display_min_prices = min_prices.copy()
        display_min_prices["price"] = display_min_prices["price"].apply(lambda x: f"€{x:.2f}")
        st.dataframe(display_min_prices.sort_values(by="price"), use_container_width=True)
        
        # Analisi parità tariffaria
        st.header("Analisi parità tariffaria")
        
        # Seleziona l'hotel di riferimento (default: VOI Alimini)
        reference_hotel = "VOI Alimini" if "VOI Alimini" in df["hotel"].unique() else df["hotel"].iloc[0]
        
        # Trova il prezzo minimo per l'hotel di riferimento
        ref_min_price = df[df["hotel"] == reference_hotel]["price"].min()
        
        # Confronta con gli altri hotel
        parity_data = []
        
        for hotel in df["hotel"].unique():
            if hotel != reference_hotel:
                min_price = df[df["hotel"] == hotel]["price"].min()
                price_diff = ref_min_price - min_price
                perc_diff = (price_diff / min_price) * 100 if min_price > 0 else 0
                
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
            display_df["min_price"] = display_df["min_price"].apply(lambda x: f"€{x:.2f}")
            display_df["price_diff"] = display_df["price_diff"].apply(lambda x: f"€{x:.2f}")
            display_df["perc_diff"] = display_df["perc_diff"].apply(lambda x: f"{x:.2f}%")
            
            st.dataframe(display_df, use_container_width=True)
    else:
        st.info("Clicca su 'Cerca tariffe' per recuperare i dati tariffari")
    
    # Sezione informativa
    with st.expander("Informazioni"):
        st.write("""
        Questa applicazione utilizza l'API Xotelo per recuperare i prezzi degli hotel da TripAdvisor.
        
        I prezzi originali sono in USD e vengono convertiti in EUR utilizzando un tasso di cambio fisso di 1 USD = 0.92 EUR.
        
        Le chiavi degli hotel sono universali e funzionano sia con TripAdvisor.it che con TripAdvisor.com.
        """)

# Esegui l'app
if __name__ == "__main__":
    rate_checker_app()
