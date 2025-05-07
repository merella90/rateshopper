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

# Classe per conversione di valuta
class CurrencyConverter:
    def __init__(self):
        self.base_url = "https://api.frankfurter.dev/v1"
        self.cache = {}
        
    def get_exchange_rate(self, from_currency, to_currency):
        """
        Ottieni il tasso di cambio tra due valute
        """
        # Verifica se il tasso è già in cache
        cache_key = f"{from_currency}_{to_currency}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            url = f"{self.base_url}/latest?from={from_currency}&to={to_currency}"
            response = requests.get(url)
            data = response.json()
            
            rate = data["rates"][to_currency]
            
            # Memorizza in cache
            self.cache[cache_key] = rate
            
            return rate
        except Exception as e:
            st.warning(f"Errore nel recupero del tasso di cambio: {str(e)}")
            # Valori di fallback approssimativi USD->EUR
            fallback_rates = {"USD_EUR": 0.92}
            return fallback_rates.get(cache_key, 1.0)
    
    def convert(self, amount, from_currency, to_currency):
        """
        Converti un importo da una valuta a un'altra
        """
        if from_currency == to_currency:
            return amount
        
        rate = self.get_exchange_rate(from_currency, to_currency)
        return amount * rate

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
# Queste possono essere da TripAdvisor.it o TripAdvisor.com - la chiave è lo stesso formato
hotel_keys = {
    "VOI Alimini": "g652004-d1799967",  
    "Ciaoclub Arco Del Saracino": "g946998-d947000", 
    "Hotel Alpiselect Robinson Apulia": "g947837-d949958",  
    "Alpiclub Hotel Thalas Club": "g1179328-d1159227" 
}

# Funzione per convertire la risposta API in DataFrame
def process_xotelo_response(response, hotel_name, currency_converter, target_currency="EUR"):
    """
    Elabora la risposta dell'API Xotelo e la converte in un DataFrame
    
    Args:
        response (dict): Risposta JSON dell'API
        hotel_name (str): Nome dell'hotel
        currency_converter (CurrencyConverter): Convertitore di valuta
        target_currency (str): Valuta target (default: EUR)
        
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
        # L'API Xotelo fornisce i prezzi in USD, convertiamo in EUR
        usd_price = rate.get("rate", 0)
        eur_price = currency_converter.convert(usd_price, "USD", target_currency)
        
        data.append({
            "hotel": hotel_name,
            "ota": rate.get("name", ""),
            "ota_code": rate.get("code", ""),
            "price_usd": usd_price,  # Conserviamo anche il prezzo in USD
            "price": eur_price,      # Il prezzo in EUR sarà quello principale
            "currency": target_currency,
            "check_in": check_in,
            "check_out": check_out,
            "timestamp": response["timestamp"]
        })
    
    return pd.DataFrame(data)

# Applicazione Streamlit
def rate_checker_app():
    st.title("Rate Checker VOI Alimini con Xotelo API")
    st.subheader("Confronto tariffe basato su TripAdvisor")
    
    # Inizializza il convertitore di valuta
    currency_converter = CurrencyConverter()
    
    # Sidebar per i controlli
    st.sidebar.header("Parametri di ricerca")
    
    # Selezione della valuta
    currency = st.sidebar.selectbox(
        "Valuta",
        ["EUR", "USD"],
        index=0
    )
    
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
                    df = process_xotelo_response(response, hotel, currency_converter, currency)
                    
                    if not df.empty:
                        all_data.append(df)
            
            if all_data:
                # Combina tutti i DataFrame
                combined_df = pd.concat(all_data, ignore_index=True)
                
                # Memorizza i dati nella sessione
                st.session_state.rate_data = combined_df
                st.session_state.currency = currency
                
                st.success("Dati tariffari recuperati con successo!")
            else:
                st.error("Nessun dato recuperato. Verifica le chiavi degli hotel e riprova.")
    
    # Visualizza i dati se disponibili
    if "rate_data" in st.session_state:
        # Ottieni il DataFrame e la valuta
        df = st.session_state.rate_data
        current_currency = st.session_state.currency
        
        # Se l'utente ha cambiato la valuta, aggiorna i prezzi
        if current_currency != currency:
            # Converti i prezzi alla nuova valuta
            if currency == "USD" and current_currency == "EUR":
                df["price"] = df["price_usd"]
            elif currency == "EUR" and current_currency == "USD":
                # I prezzi in USD sono già memorizzati in price_usd
                df["price"] = df.apply(
                    lambda row: currency_converter.convert(row["price_usd"], "USD", "EUR"), 
                    axis=1
                )
            
            # Aggiorna la valuta nella sessione
            st.session_state.currency = currency
            st.session_state.rate_data = df
            
            st.success(f"Prezzi convertiti in {currency}")
        
        # Simbolo della valuta
        currency_symbol = "€" if currency == "EUR" else "$"
        
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
                labels={"price": f"Prezzo ({currency_symbol})", "ota": "OTA"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistiche principali
            col1, col2, col3 = st.columns(3)
            
            with col1:
                min_price = hotel_df["price"].min()
                min_ota = hotel_df.loc[hotel_df["price"].idxmin(), "ota"]
                st.metric("Prezzo minimo", f"{currency_symbol}{min_price:.2f}", f"via {min_ota}")
            
            with col2:
                max_price = hotel_df["price"].max()
                max_ota = hotel_df.loc[hotel_df["price"].idxmax(), "ota"]
                st.metric("Prezzo massimo", f"{currency_symbol}{max_price:.2f}", f"via {max_ota}")
            
            with col3:
                avg_price = hotel_df["price"].mean()
                price_range = max_price - min_price
                st.metric("Prezzo medio", f"{currency_symbol}{avg_price:.2f}", f"Range: {currency_symbol}{price_range:.2f}")
            
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
            labels={"price": f"Prezzo minimo ({currency_symbol})", "hotel": "Hotel"}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabella di confronto
        st.subheader("Confronto prezzi minimi tra hotel")
        display_min_prices = min_prices.copy()
        display_min_prices["price"] = display_min_prices["price"].apply(lambda x: f"{currency_symbol}{x:.2f}")
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
            display_df["min_price"] = display_df["min_price"].apply(lambda x: f"{currency_symbol}{x:.2f}")
            display_df["price_diff"] = display_df["price_diff"].apply(lambda x: f"{currency_symbol}{x:.2f}")
            display_df["perc_diff"] = display_df["perc_diff"].apply(lambda x: f"{x:.2f}%")
            
            st.dataframe(display_df, use_container_width=True)
    else:
        st.info("Clicca su 'Cerca tariffe' per recuperare i dati tariffari")
    
    # Sezione informativa
    with st.expander("Come trovare la chiave TripAdvisor dell'hotel"):
        st.write("""
        Per utilizzare questa app, è necessario avere la chiave TripAdvisor per ciascun hotel. Ecco come trovarla:
        
        1. Vai alla pagina dell'hotel su TripAdvisor.it o TripAdvisor.com
        2. Osserva l'URL, che sarà simile a: `https://www.tripadvisor.it/Hotel_Review-g1234567-d12345678-Reviews-Hotel_Name.html`
        3. La chiave è la parte `g1234567-d12345678`
        
        Le chiavi sono universali e funzionano sia con TripAdvisor.it che con TripAdvisor.com.
        """)

    # Sezione sulla conversione di valuta    
    with st.expander("Informazioni sulla conversione di valuta"):
        st.write("""
        L'API Xotelo fornisce i prezzi in USD per impostazione predefinita. 
        
        Questa applicazione utilizza l'API gratuita di Frankfurter per convertire i prezzi da USD a EUR. I tassi di cambio sono aggiornati quotidianamente.
        
        È possibile selezionare la valuta preferita nella barra laterale.
        """)

# Esegui l'app
if __name__ == "__main__":
    rate_checker_app()
