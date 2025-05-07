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

# Classe per conversione di valuta utilizzando API reali
class CurrencyConverter:
    def __init__(self):
        # Utilizzo dell'API Frankfurter della BCE (European Central Bank)
        self.base_url = "https://api.frankfurter.app"
        self.cache = {}
        self.last_update = None
        self.update_interval = timedelta(hours=1)  # Aggiorna ogni ora
    
    def get_exchange_rate(self, from_currency, to_currency):
        """
        Ottieni il tasso di cambio da una valuta a un'altra utilizzando fonti ufficiali
        """
        # Se le valute sono uguali, il tasso è 1
        if from_currency == to_currency:
            return 1.0
        
        # Verifica se è necessario aggiornare il tasso di cambio
        now = datetime.now()
        update_needed = (
            self.last_update is None or 
            (now - self.last_update) > self.update_interval or
            f"{from_currency}_{to_currency}" not in self.cache
        )
        
        if update_needed:
            try:
                # Frankfurter API (basata sui dati ufficiali della BCE)
                url = f"{self.base_url}/latest?from={from_currency}&to={to_currency}"
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    rate = data["rates"][to_currency]
                    
                    # Salva in cache
                    self.cache[f"{from_currency}_{to_currency}"] = rate
                    self.last_update = now
                    
                    # Debug info
                    st.sidebar.info(f"Tasso di cambio aggiornato: 1 {from_currency} = {rate} {to_currency}")
                    
                    return rate
                else:
                    # Fallback su exchangerate.host (altra fonte affidabile)
                    url = f"https://api.exchangerate.host/convert?from={from_currency}&to={to_currency}"
                    response = requests.get(url)
                    
                    if response.status_code == 200:
                        data = response.json()
                        rate = data["result"]
                        
                        # Salva in cache
                        self.cache[f"{from_currency}_{to_currency}"] = rate
                        self.last_update = now
                        
                        # Debug info
                        st.sidebar.info(f"Tasso di cambio aggiornato (alternativo): 1 {from_currency} = {rate} {to_currency}")
                        
                        return rate
            except Exception as e:
                st.sidebar.warning(f"Errore nel recupero del tasso di cambio: {str(e)}")
        
        # Usa il valore in cache se disponibile
        if f"{from_currency}_{to_currency}" in self.cache:
            return self.cache[f"{from_currency}_{to_currency}"]
        
        # Valori di fallback approssimativi (da fonti ufficiali BCE)
        fallback_rates = {"USD_EUR": 0.92, "EUR_USD": 1.09}
        key = f"{from_currency}_{to_currency}"
        
        if key in fallback_rates:
            st.sidebar.warning("Usando tasso di cambio di fallback")
            return fallback_rates[key]
        else:
            # Usa un tasso generico se tutto fallisce
            st.sidebar.warning("Tasso di cambio non disponibile. Usando approssimazione.")
            return 0.92 if from_currency == "USD" and to_currency == "EUR" else 1.09
    
    def convert(self, amount, from_currency, to_currency):
        """
        Converti un importo da una valuta a un'altra
        """
        rate = self.get_exchange_rate(from_currency, to_currency)
        return amount * rate

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
def process_xotelo_response(response, hotel_name, currency_converter, target_currency="EUR", num_nights=1):
    """
    Elabora la risposta dell'API Xotelo e la converte in un DataFrame
    
    Args:
        response (dict): Risposta JSON dell'API
        hotel_name (str): Nome dell'hotel
        currency_converter (CurrencyConverter): Convertitore di valuta
        target_currency (str): Valuta target (default: EUR)
        num_nights (int): Numero di notti del soggiorno
        
    Returns:
        pd.DataFrame: DataFrame con i dati delle tariffe
    """
    # Verifica se la risposta contiene un errore o non ha risultati
    if response.get("error") is not None or response.get("result") is None:
        # Creiamo un DataFrame "vuoto" con un messaggio per hotel non disponibili
        return pd.DataFrame([{
            "hotel": hotel_name,
            "ota": "N/A",
            "ota_code": "N/A",
            "price": 0,  # Prezzo unitario
            "price_total": 0,  # Prezzo totale per il soggiorno
            "currency": target_currency,
            "check_in": "",
            "check_out": "",
            "timestamp": 0,
            "available": False,  # Usare "available" per maggiore compatibilità
            "message": "Dati non disponibili/sold out"
        }])
    
    rates = response.get("result", {}).get("rates", [])
    check_in = response.get("result", {}).get("chk_in", "")
    check_out = response.get("result", {}).get("chk_out", "")
    
    # Se non ci sono tariffe, consideriamolo come non disponibile
    if not rates:
        return pd.DataFrame([{
            "hotel": hotel_name,
            "ota": "N/A",
            "ota_code": "N/A",
            "price": 0,
            "price_total": 0,
            "currency": target_currency,
            "check_in": check_in,
            "check_out": check_out,
            "timestamp": response.get("timestamp", 0),
            "available": False,
            "message": "Dati non disponibili/sold out"
        }])
    
    data = []
    for rate in rates:
        # L'API Xotelo fornisce i prezzi in USD, convertiamo in EUR
        usd_price = rate.get("rate", 0)
        price_per_night = currency_converter.convert(usd_price, "USD", target_currency)
        total_price = price_per_night * num_nights
        
        data.append({
            "hotel": hotel_name,
            "ota": rate.get("name", ""),
            "ota_code": rate.get("code", ""),
            "price": price_per_night,  # Prezzo unitario/per notte
            "price_total": total_price,  # Prezzo totale per il soggiorno
            "currency": target_currency,
            "check_in": check_in,
            "check_out": check_out,
            "timestamp": response.get("timestamp", 0),
            "available": True,
            "message": ""
        })
    
    return pd.DataFrame(data)

# Funzione per normalizzare il DataFrame
def normalize_dataframe(df, num_nights):
    """
    Assicura che il DataFrame abbia la struttura corretta, migrando vecchi formati se necessario
    """
    normalized_df = df.copy()
    
    # Verifica quali colonne sono presenti e migra se necessario
    columns = df.columns.tolist()
    
    # Gestisci diverse varianti possibili
    if "price" in columns and "price_night" not in columns:
        normalized_df["price_night"] = normalized_df["price"]
    elif "price_night" in columns and "price" not in columns:
        normalized_df["price"] = normalized_df["price_night"]
    elif "price" not in columns and "price_night" not in columns:
        # Se nessuna delle due è presente, ma c'è price_total
        if "price_total" in columns:
            normalized_df["price"] = normalized_df["price_total"] / num_nights
            normalized_df["price_night"] = normalized_df["price"]
        else:
            # Caso estremo: non ci sono colonne di prezzo
            normalized_df["price"] = 0
            normalized_df["price_night"] = 0
            normalized_df["price_total"] = 0
    
    # Assicurati che sia presente price_total
    if "price_total" not in columns:
        if "price" in columns:
            normalized_df["price_total"] = normalized_df["price"] * num_nights
        elif "price_night" in columns:
            normalized_df["price_total"] = normalized_df["price_night"] * num_nights
        else:
            normalized_df["price_total"] = 0
    
    # Gestisci la colonna "available"/"is_available"
    if "is_available" in columns and "available" not in columns:
        normalized_df["available"] = normalized_df["is_available"]
    elif "available" in columns and "is_available" not in columns:
        normalized_df["is_available"] = normalized_df["available"]
    elif "available" not in columns and "is_available" not in columns:
        # Assume che tutte le righe sono disponibili a meno che non abbiano un prezzo pari a 0
        normalized_df["available"] = normalized_df["price"] > 0
        normalized_df["is_available"] = normalized_df["available"]
    
    # Assicurati che sia presente la colonna message
    if "message" not in columns:
        normalized_df["message"] = ""
        # Aggiungi un messaggio per le righe non disponibili
        if "available" in columns:
            normalized_df.loc[~normalized_df["available"], "message"] = "Dati non disponibili/sold out"
        elif "is_available" in columns:
            normalized_df.loc[~normalized_df["is_available"], "message"] = "Dati non disponibili/sold out"
    
    return normalized_df

# Applicazione Streamlit
def rate_checker_app():
    st.title("Rate Checker VOI Alimini con Xotelo API")
    st.subheader("Confronto tariffe basato su TripAdvisor")
    
    # Inizializza il convertitore di valuta
    if "currency_converter" not in st.session_state:
        st.session_state.currency_converter = CurrencyConverter()
    
    currency_converter = st.session_state.currency_converter
    
    # Assicuriamoci che la valuta predefinita sia impostata
    if "currency" not in st.session_state:
        st.session_state.currency = "EUR"
    
    # Sidebar per i controlli
    st.sidebar.header("Parametri di ricerca")
    
    # Selezione della valuta
    currency = st.sidebar.selectbox(
        "Valuta",
        ["EUR", "USD"],
        index=0 if st.session_state.currency == "EUR" else 1
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
        check_out_date = st.date_input("Check-out", datetime.now() + timedelta(days=7))
    
    # Calcola il numero di notti
    num_nights = (check_out_date - check_in_date).days
    if num_nights <= 0:
        st.sidebar.error("La data di check-out deve essere successiva alla data di check-in!")
        num_nights = 1
    else:
        st.sidebar.info(f"Durata soggiorno: {num_nights} {'notte' if num_nights == 1 else 'notti'}")
    
    # Visualizzazione dei prezzi
    price_view = st.sidebar.radio(
        "Visualizza prezzi",
        ["Totali", "Per notte"],
        index=0,  # Default: prezzi totali
        help="Scegli se visualizzare i prezzi totali per tutto il soggiorno o i prezzi per notte"
    )
    
    # Reset dei dati
    if st.sidebar.button("Cancella dati salvati"):
        if "rate_data" in st.session_state:
            del st.session_state["rate_data"]
        st.sidebar.success("Dati cancellati con successo.")
        st.rerun()
    
    # Determina quale colonna di prezzo usare
    use_total_price = (price_view == "Totali")
    price_column = "price_total" if use_total_price else "price"
    price_description = f"{'totali per ' + str(num_nights) + ' notti' if use_total_price else 'per notte'}"
    
    # Bottone per eseguire la ricerca
    if st.sidebar.button("Cerca tariffe"):
        # Inizializza l'API Xotelo
        xotelo_api = XoteloAPI()
        
        with st.spinner("Recupero tariffe in corso..."):
            # Raccogli i dati per ciascun hotel selezionato
            all_data = []
            
            # Mostra stato debug
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
                    
                    # Processa la risposta, considerando il numero di notti
                    df = process_xotelo_response(
                        response, 
                        hotel, 
                        currency_converter, 
                        currency,
                        num_nights
                    )
                    
                    all_data.append(df)
            
            progress_bar.progress(100)
            status_text.text("Elaborazione completata!")
            
            if all_data:
                # Combina tutti i DataFrame
                combined_df = pd.concat(all_data, ignore_index=True)
                
                # Normalizza il DataFrame per garantire che abbia tutte le colonne necessarie
                normalized_df = normalize_dataframe(combined_df, num_nights)
                
                # Memorizza i dati nella sessione
                st.session_state.rate_data = normalized_df
                st.session_state.currency = currency
                st.session_state.num_nights = num_nights
                
                # Conteggia gli hotel disponibili e non disponibili
                available_hotels = normalized_df[normalized_df["available"]]["hotel"].unique()
                unavailable_hotels = normalized_df[~normalized_df["available"]]["hotel"].unique()
                
                if len(unavailable_hotels) > 0:
                    st.warning(f"Hotel non disponibili: {', '.join(unavailable_hotels)}")
                
                st.success(f"Dati tariffari recuperati con successo per {len(available_hotels)} hotel!")
            else:
                st.error("Nessun dato recuperato. Verifica le chiavi degli hotel e riprova.")
    
    # Visualizza i dati se disponibili
    if "rate_data" in st.session_state:
        # Ottieni il DataFrame
        df = st.session_state.rate_data
        
        # Normalizza il DataFrame per assicurarsi che abbia la struttura corretta
        df = normalize_dataframe(df, num_nights)
        st.session_state.rate_data = df  # Aggiorna il DataFrame in session_state
        
        current_currency = st.session_state.currency
        
        # Aggiorna il conteggio delle notti se è cambiato
        if "num_nights" in st.session_state and st.session_state.num_nights != num_nights:
            # Ricalcola i prezzi totali con il nuovo numero di notti
            df["price_total"] = df["price"] * num_nights
            st.session_state.num_nights = num_nights
            st.session_state.rate_data = df
            st.info(f"Prezzi totali aggiornati per {num_nights} notti")
        
        # Se l'utente ha cambiato la valuta, aggiorna i prezzi
        if current_currency != currency:
            # Converti i prezzi alla nuova valuta
            if currency == "USD" and current_currency == "EUR":
                df["price"] = df.apply(
                    lambda row: currency_converter.convert(row["price"], "EUR", "USD") if row["available"] else 0, 
                    axis=1
                )
                df["price_total"] = df["price"] * num_nights
            elif currency == "EUR" and current_currency == "USD":
                df["price"] = df.apply(
                    lambda row: currency_converter.convert(row["price"], "USD", "EUR") if row["available"] else 0, 
                    axis=1
                )
                df["price_total"] = df["price"] * num_nights
            
            # Aggiorna la valuta nella sessione
            st.session_state.currency = currency
            st.session_state.rate_data = df
            
            st.success(f"Prezzi convertiti in {currency}")
        
        # Simbolo della valuta
        currency_symbol = "€" if currency == "EUR" else "$"
        
        # Visualizza la scheda principale
        st.header(f"Confronto tariffe tra OTA (Prezzi {price_description})")
        
        # Filtra solo hotel disponibili per la selezione
        available_hotels = df[df["available"]]["hotel"].unique()
        
        if len(available_hotels) > 0:
            # Seleziona l'hotel da analizzare
            selected_hotel = st.selectbox(
                "Seleziona hotel da analizzare",
                available_hotels
            )
            
            # Filtra per l'hotel selezionato
            hotel_df = df[(df["hotel"] == selected_hotel) & df["available"]]
            
            if not hotel_df.empty:
                # Conteggio OTA disponibili
                ota_count = len(hotel_df["ota"].unique())
                st.info(f"Trovate {ota_count} OTA per {selected_hotel}")
                
                # Grafico delle tariffe per OTA
                fig = px.bar(
                    hotel_df,
                    x="ota",
                    y=price_column,
                    title=f"Tariffe per {selected_hotel} ({check_in_date.strftime('%d/%m/%Y')} - {check_out_date.strftime('%d/%m/%Y')})",
                    color="ota",
                    labels={price_column: f"Prezzo {price_description} ({currency_symbol})", "ota": "OTA"}
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistiche principali
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    min_price = hotel_df[price_column].min()
                    min_ota = hotel_df.loc[hotel_df[price_column].idxmin(), "ota"]
                    st.metric("Prezzo minimo", f"{currency_symbol}{min_price:.2f}", f"via {min_ota}")
                
                with col2:
                    max_price = hotel_df[price_column].max()
                    max_ota = hotel_df.loc[hotel_df[price_column].idxmax(), "ota"]
                    st.metric("Prezzo massimo", f"{currency_symbol}{max_price:.2f}", f"via {max_ota}")
                
                with col3:
                    avg_price = hotel_df[price_column].mean()
                    price_range = max_price - min_price
                    st.metric("Prezzo medio", f"{currency_symbol}{avg_price:.2f}", f"Range: {currency_symbol}{price_range:.2f}")
                
                # Dettagli prezzo per notte vs totale
                col1, col2 = st.columns(2)
                with col1:
                    # Prezzo per notte
                    min_price_night = hotel_df["price"].min()
                    min_ota_night = hotel_df.loc[hotel_df["price"].idxmin(), "ota"]
                    st.info(f"Prezzo minimo per notte: {currency_symbol}{min_price_night:.2f} via {min_ota_night}")
                
                with col2:
                    # Prezzo totale
                    min_price_total = hotel_df["price_total"].min()
                    min_ota_total = hotel_df.loc[hotel_df["price_total"].idxmin(), "ota"]
                    st.info(f"Prezzo totale per {num_nights} notti: {currency_symbol}{min_price_total:.2f} via {min_ota_total}")
                
                # Tabella completa dei dati
                st.subheader("Dettaglio tariffe per tutte le OTA")
                # Creiamo una copia del dataframe per la visualizzazione
                columns_to_show = ["ota", "price", "price_total"]
                display_df = hotel_df[columns_to_show].sort_values(by=price_column).copy()
                # Formatta i prezzi
                display_df["price"] = display_df["price"].apply(lambda x: f"{currency_symbol}{x:.2f}")
                display_df["price_total"] = display_df["price_total"].apply(lambda x: f"{currency_symbol}{x:.2f}")
                # Rinomina le colonne per la visualizzazione
                display_df.columns = ["OTA", f"Prezzo per notte ({currency_symbol})", f"Prezzo totale per {num_nights} notti ({currency_symbol})"]
                st.dataframe(display_df, use_container_width=True)
            
            # Confronto tra hotel
            st.header(f"Confronto tra hotel (Prezzi {price_description})")
            
            # Filtra solo hotel disponibili
            available_df = df[df["available"]]
            
            if not available_df.empty:
                # Trova il prezzo minimo e quali OTA offrono il prezzo minimo per ciascun hotel
                min_prices_data = []
                for hotel in available_df["hotel"].unique():
                    hotel_data = available_df[available_df["hotel"] == hotel]
                    min_price_idx = hotel_data[price_column].idxmin()
                    min_price_row = hotel_data.loc[min_price_idx]
                    
                    min_prices_data.append({
                        "hotel": hotel,
                        "min_price": min_price_row[price_column],
                        "min_ota": min_price_row["ota"],
                        "ota_count": len(hotel_data["ota"].unique())
                    })
                
                min_prices_df = pd.DataFrame(min_prices_data)
                
                # Grafico di confronto
                fig = px.bar(
                    min_prices_df,
                    x="hotel",
                    y="min_price",
                    title=f"Prezzo minimo disponibile per hotel ({check_in_date.strftime('%d/%m/%Y')} - {check_out_date.strftime('%d/%m/%Y')})",
                    color="hotel",
                    labels={"min_price": f"Prezzo minimo {price_description} ({currency_symbol})", "hotel": "Hotel"}
                )
                
                # Aggiungi annotazioni con la OTA
                for i, row in min_prices_df.iterrows():
                    fig.add_annotation(
                        x=row["hotel"],
                        y=row["min_price"],
                        text=f"via {row['min_ota']}",
                        showarrow=False,
                        yshift=10,
                        font=dict(size=10)
                    )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabella di confronto
                st.subheader(f"Confronto prezzi minimi tra hotel ({price_description})")
                display_min_prices = min_prices_df.copy()
                display_min_prices["min_price"] = display_min_prices["min_price"].apply(lambda x: f"{currency_symbol}{x:.2f}")
                display_min_prices.columns = ["Hotel", "Prezzo minimo", "OTA", "Numero OTA disponibili"]
                st.dataframe(display_min_prices.sort_values(by="Prezzo minimo"), use_container_width=True)
                
                # Visualizza tutte le OTA disponibili per ciascun hotel
                st.subheader("Tutte le OTA disponibili per hotel")
                all_otas_by_hotel = {}
                
                for hotel in available_df["hotel"].unique():
                    hotel_data = available_df[available_df["hotel"] == hotel]
                    all_otas_by_hotel[hotel] = sorted(hotel_data["ota"].unique())
                
                for hotel, otas in all_otas_by_hotel.items():
                    with st.expander(f"{hotel} - {len(otas)} OTA disponibili"):
                        st.write(", ".join(otas))
                
                # Analisi parità tariffaria
                st.header("Analisi parità tariffaria")
                
                # Seleziona l'hotel di riferimento (default: VOI Alimini)
                reference_hotel = "VOI Alimini" if "VOI Alimini" in available_df["hotel"].unique() else available_df["hotel"].iloc[0]
                
                # Trova il prezzo minimo per l'hotel di riferimento
                ref_min_price = available_df[available_df["hotel"] == reference_hotel][price_column].min()
                
                # Confronta con gli altri hotel
                parity_data = []
                
                for hotel in available_df["hotel"].unique():
                    if hotel != reference_hotel:
                        min_price = available_df[available_df["hotel"] == hotel][price_column].min()
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
            
            # Mostra hotel non disponibili
            unavailable_hotels = df[~df["available"]]["hotel"].unique()
            if len(unavailable_hotels) > 0:
                st.header("Hotel non disponibili")
                unavailable_df = df[~df["available"]][["hotel", "message"]].drop_duplicates()
                st.warning(f"I seguenti hotel non hanno disponibilità: {', '.join(unavailable_hotels)}")
                st.dataframe(unavailable_df, use_container_width=True)
        else:
            st.warning("Nessun hotel disponibile per le date selezionate.")
    else:
        st.info("Clicca su 'Cerca tariffe' per recuperare i dati tariffari")
    
    # Informazioni sul tasso di cambio
    with st.expander("Informazioni sul tasso di cambio"):
        st.write("""
        Questa applicazione utilizza i tassi di cambio ufficiali della Banca Centrale Europea (BCE) tramite l'API Frankfurter.
        
        I tassi di cambio vengono aggiornati ogni ora per garantire la massima precisione. In caso di problemi di connessione,
        viene utilizzata l'API ExchangeRate.host come fonte alternativa.
        
        Se entrambe le fonti non sono disponibili, viene utilizzato un tasso di fallback approssimativo.
        """)
    
    # Sezione informativa
    with st.expander("Come trovare la chiave TripAdvisor dell'hotel"):
        st.write("""
        Per utilizzare questa app, è necessario avere la chiave TripAdvisor per ciascun hotel. Ecco come trovarla:
        
        1. Vai alla pagina dell'hotel su TripAdvisor.it o TripAdvisor.com
        2. Osserva l'URL, che sarà simile a: `https://www.tripadvisor.it/Hotel_Review-g1234567-d12345678-Reviews-Hotel_Name.html`
        3. La chiave è la parte `g1234567-d12345678`
        
        Le chiavi sono universali e funzionano sia con TripAdvisor.it che con TripAdvisor.com.
        """)

# Esegui l'app
if __name__ == "__main__":
    rate_checker_app()
