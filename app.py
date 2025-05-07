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

# Classe per l'integrazione con Xotelo API
class XoteloAPI:
    def __init__(self):
        self.base_url = "https://data.xotelo.com/api"
    
    def get_rates(self, hotel_key, check_in, check_out):
        """
        Ottieni le tariffe per un hotel specifico
        
        Args:
            hotel_key (str): Chiave TripAdvisor dell'hotel
            check_in (str): Data di check-in formato YYYY-MM-DD
            check_out (str): Data di check-out formato YYYY-MM-DD
            
        Returns:
            dict: Dati tariffari in formato JSON
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
    
    def get_hotel_list(self, location_key, offset=0, limit=30):
        """
        Ottieni un elenco di hotel in base alla posizione
        
        Args:
            location_key (str): Chiave TripAdvisor della località
            offset (int): Offset per la paginazione
            limit (int): Numero massimo di risultati
            
        Returns:
            dict: Elenco di hotel in formato JSON
        """
        endpoint = f"{self.base_url}/list"
        params = {
            "location_key": location_key,
            "offset": offset,
            "limit": limit
        }
        
        try:
            response = requests.get(endpoint, params=params)
            return response.json()
        except Exception as e:
            return {"error": str(e), "timestamp": 0, "result": None}

# Dizionario delle chiavi TripAdvisor per gli hotel competitor
# Queste dovrebbero essere sostituite con le chiavi reali
hotel_keys = {
    "VOI Alimini": "g1234567-d12345678",  # Esempio di chiave (da sostituire con quella reale)
    "Ciaoclub Arco Del Saracino": "g1234567-d12345679",  # Esempio di chiave
    "Hotel Alpiselect Robinson Apulia": "g1234567-d12345680",  # Esempio di chiave
    "Alpiclub Hotel Thalas Club": "g1234567-d12345681"  # Esempio di chiave
}

# Funzione per convertire la risposta API in DataFrame
def process_xotelo_response(response, hotel_name):
    """
    Elabora la risposta dell'API Xotelo e la converte in un DataFrame
    
    Args:
        response (dict): Risposta JSON dell'API
        hotel_name (str): Nome dell'hotel
        
    Returns:
        pd.DataFrame: DataFrame con i dati delle tariffe
    """
    if response["error"] is not None or response["result"] is None:
        return pd.DataFrame()
    
    rates = response["result"].get("rates", [])
    check_in = response["result"].get("chk_in", "")
    check_out = response["result"].get("chk_out", "")
    
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
    
    return pd.DataFrame(data)

# Applicazione Streamlit
def rate_checker_app():
    st.title("Rate Checker VOI Alimini con Xotelo API")
    st.subheader("Confronto tariffe basato su TripAdvisor")
    
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
    
    # Bottone per eseguire la ricerca
    if st.sidebar.button("Cerca tariffe"):
        # Inizializza l'API Xotelo
        xotelo_api = XoteloAPI()
        
        with st.spinner("Recupero tariffe in corso..."):
            # Raccogli i dati per ciascun hotel selezionato
            all_data = []
            
            for hotel in selected_hotels:
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
            
            if all_data:
                # Combina tutti i DataFrame
                combined_df = pd.concat(all_data, ignore_index=True)
                
                # Memorizza i dati nella sessione
                st.session_state.rate_data = combined_df
                
                st.success("Dati tariffari recuperati con successo!")
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
                labels={"price": "Prezzo ($)", "ota": "OTA"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistiche principali
            col1, col2, col3 = st.columns(3)
            
            with col1:
                min_price = hotel_df["price"].min()
                min_ota = hotel_df.loc[hotel_df["price"].idxmin(), "ota"]
                st.metric("Prezzo minimo", f"${min_price:.2f}", f"via {min_ota}")
            
            with col2:
                max_price = hotel_df["price"].max()
                max_ota = hotel_df.loc[hotel_df["price"].idxmax(), "ota"]
                st.metric("Prezzo massimo", f"${max_price:.2f}", f"via {max_ota}")
            
            with col3:
                avg_price = hotel_df["price"].mean()
                price_range = max_price - min_price
                st.metric("Prezzo medio", f"${avg_price:.2f}", f"Range: ${price_range:.2f}")
            
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
            display_df["min_price"] = display_df["min_price"].apply(lambda x: f"${x:.2f}")
            display_df["price_diff"] = display_df["price_diff"].apply(lambda x: f"${x:.2f}")
            display_df["perc_diff"] = display_df["perc_diff"].apply(lambda x: f"{x:.2f}%")
            
            st.dataframe(display_df, use_container_width=True)
    else:
        st.info("Clicca su 'Cerca tariffe' per recuperare i dati tariffari")
    
    # Sezione informativa
    with st.expander("Come trovare la chiave TripAdvisor dell'hotel"):
        st.write("""
        Per utilizzare questa app, è necessario avere la chiave TripAdvisor per ciascun hotel. Ecco come trovarla:
        
        1. Vai alla pagina dell'hotel su TripAdvisor
        2. Osserva l'URL, che sarà simile a: `https://www.tripadvisor.com/Hotel_Review-g1234567-d12345678-Reviews-Hotel_Name.html`
        3. La chiave è la parte `g1234567-d12345678`
        
        Sostituisci le chiavi di esempio nel codice con quelle reali degli hotel che desideri monitorare.
        """)

# Esegui l'app
if __name__ == "__main__":
    rate_checker_app()
