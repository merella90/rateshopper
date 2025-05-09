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
    
    def get_rates(self, hotel_key, check_in, check_out, adults=2, children_ages=None, rooms=1, currency="EUR"):
        """
        Ottieni le tariffe per un hotel specifico con specifiche di occupazione
        
        Args:
            hotel_key (str): Chiave TripAdvisor dell'hotel
            check_in (str): Data di check-in in formato YYYY-MM-DD
            check_out (str): Data di check-out in formato YYYY-MM-DD
            adults (int): Numero di adulti (default 2)
            children_ages (list): Lista delle età dei bambini (default None)
            rooms (int): Numero di camere (default 1)
            currency (str): Valuta desiderata (default EUR)
        """
        endpoint = f"{self.base_url}/rates"
        params = {
            "hotel_key": hotel_key,
            "chk_in": check_in,
            "chk_out": check_out,
            "adults": adults,
            "rooms": rooms,
            "currency": currency
        }
        
        # Aggiungi età dei bambini se specificato
        if children_ages and len(children_ages) > 0:
            params["age_of_children"] = ",".join(map(str, children_ages))
        
        try:
            response = requests.get(endpoint, params=params)
            return response.json()
        except Exception as e:
            return {"error": str(e), "timestamp": 0, "result": None}
    
    def get_heatmap(self, hotel_key, check_out):
        """
        Ottieni i dati dell'heatmap dei prezzi per un hotel specifico
        
        Args:
            hotel_key (str): Chiave TripAdvisor dell'hotel
            check_out (str): Data di check-out in formato YYYY-MM-DD
        """
        endpoint = f"{self.base_url}/heatmap"
        params = {
            "hotel_key": hotel_key,
            "chk_out": check_out
        }
        
        try:
            response = requests.get(endpoint, params=params)
            return response.json()
        except Exception as e:
            return {"error": str(e), "timestamp": 0, "result": None}
    
    def get_hotel_list(self, location_key, limit=30, offset=0, sort="best_value"):
        """
        Ottieni la lista degli hotel in una località specifica
        
        Args:
            location_key (str): Chiave TripAdvisor della località
            limit (int): Limite di risultati (default 30, max 100)
            offset (int): Offset per la paginazione (default 0)
            sort (str): Criterio di ordinamento (default "best_value")
        """
        endpoint = f"{self.base_url}/list"
        params = {
            "location_key": location_key,
            "limit": limit,
            "offset": offset,
            "sort": sort
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

# Chiave TripAdvisor per la località (Lecce/Salento)
location_key = "g652004"  # Otranto, Puglia

# Funzione per convertire la risposta API in DataFrame
def process_xotelo_response(response, hotel_name, num_nights=1, adults=2, children_count=0, rooms=1, currency="EUR"):
    """
    Elabora la risposta dell'API Xotelo e la converte in un DataFrame
    
    Args:
        response (dict): Risposta JSON dell'API
        hotel_name (str): Nome dell'hotel
        num_nights (int): Numero di notti del soggiorno
        adults (int): Numero di adulti
        children_count (int): Numero di bambini
        rooms (int): Numero di camere
        currency (str): Valuta (default: EUR)
        
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
            "currency": currency,
            "check_in": "",
            "check_out": "",
            "timestamp": 0,
            "available": False,  # Usare "available" per maggiore compatibilità
            "message": "Dati non disponibili/sold out",
            "adults": adults,
            "children": children_count,
            "rooms": rooms
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
            "currency": currency,
            "check_in": check_in,
            "check_out": check_out,
            "timestamp": response.get("timestamp", 0),
            "available": False,
            "message": "Dati non disponibili/sold out",
            "adults": adults,
            "children": children_count,
            "rooms": rooms
        }])
    
    data = []
    for rate in rates:
        # L'API Xotelo fornisce i prezzi nella valuta specificata
        price_per_night = rate.get("rate", 0)
        total_price = price_per_night * num_nights
        
        data.append({
            "hotel": hotel_name,
            "ota": rate.get("name", ""),
            "ota_code": rate.get("code", ""),
            "price": price_per_night,  # Prezzo unitario/per notte
            "price_total": total_price,  # Prezzo totale per il soggiorno
            "currency": currency,
            "check_in": check_in,
            "check_out": check_out,
            "timestamp": response.get("timestamp", 0),
            "available": True,
            "message": "",
            "adults": adults,
            "children": children_count,
            "rooms": rooms
        })
    
    return pd.DataFrame(data)

# Funzione per elaborare i dati dell'heatmap
def process_heatmap_response(response, hotel_name):
    """
    Elabora la risposta dell'API Heatmap e la converte in un formato adatto per la visualizzazione
    
    Args:
        response (dict): Risposta JSON dell'API
        hotel_name (str): Nome dell'hotel
        
    Returns:
        dict: Dati formattati dell'heatmap o None se non disponibili
    """
    # Verifica se la risposta contiene un errore o non ha risultati
    if response.get("error") is not None or response.get("result") is None:
        return None
    
    heatmap_data = response.get("result", {}).get("heatmap", {})
    
    if not heatmap_data:
        return None
    
    # Estrai le date per i diversi livelli di prezzo
    average_days = heatmap_data.get("average_price_days", [])
    cheap_days = heatmap_data.get("cheap_price_days", [])
    high_days = heatmap_data.get("high_price_days", [])
    
    # Converti le stringhe di date in oggetti datetime per un migliore ordinamento e visualizzazione
    formatted_average_days = [datetime.strptime(date, "%Y-%m-%d") for date in average_days]
    formatted_cheap_days = [datetime.strptime(date, "%Y-%m-%d") for date in cheap_days]
    formatted_high_days = [datetime.strptime(date, "%Y-%m-%d") for date in high_days]
    
    # Crea un DataFrame per tutte le date e il loro livello di prezzo
    all_dates = []
    
    for date in formatted_cheap_days:
        all_dates.append({
            "hotel": hotel_name,
            "date": date,
            "price_level": "Economico",
            "level_value": 1  # Per ordinamento e colore
        })
    
    for date in formatted_average_days:
        all_dates.append({
            "hotel": hotel_name,
            "date": date,
            "price_level": "Medio",
            "level_value": 2  # Per ordinamento e colore
        })
    
    for date in formatted_high_days:
        all_dates.append({
            "hotel": hotel_name,
            "date": date,
            "price_level": "Alto",
            "level_value": 3  # Per ordinamento e colore
        })
    
    if all_dates:
        df = pd.DataFrame(all_dates)
        return {
            "hotel": hotel_name,
            "timestamp": response.get("timestamp", 0),
            "check_out": response.get("result", {}).get("chk_out", ""),
            "data": df,
            "ranges": {
                "cheap": formatted_cheap_days,
                "average": formatted_average_days,
                "high": formatted_high_days
            }
        }
    
    return None

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
    
    # Assicurati che siano presenti le colonne per l'occupazione
    if "adults" not in columns:
        normalized_df["adults"] = 2  # Default
    if "children" not in columns:
        normalized_df["children"] = 0  # Default
    if "rooms" not in columns:
        normalized_df["rooms"] = 1  # Default
    
    return normalized_df

# Applicazione Streamlit
def rate_checker_app():
    st.title("Rate Checker VOI Alimini con Xotelo API")
    st.subheader("Confronto tariffe basato su TripAdvisor")
    
    # Assicuriamoci che la valuta predefinita sia impostata
    if "currency" not in st.session_state:
        st.session_state.currency = "EUR"
    
    # Sidebar per i controlli
    st.sidebar.header("Parametri di ricerca")
    
    # Selezione della valuta
    currency = st.sidebar.selectbox(
        "Valuta",
        ["EUR", "USD", "GBP", "CAD", "CHF", "AUD", "JPY", "CNY", "INR", "THB", "BRL", "HKD", "RUB", "BZD"],
        index=0  # Default: EUR
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
    
    # Parametri di occupazione
    st.sidebar.header("Occupazione")
    
    # Adulti e camere
    col1, col2 = st.sidebar.columns(2)
    with col1:
        num_adults = st.number_input("Adulti", min_value=1, max_value=32, value=2)
    with col2:
        num_rooms = st.number_input("Camere", min_value=1, max_value=8, value=1)
    
    # Gestione bambini
    has_children = st.sidebar.checkbox("Aggiungi bambini")
    children_ages = []
    
    if has_children:
        num_children = st.sidebar.number_input("Numero bambini", min_value=1, max_value=16, value=1)
        
        for i in range(num_children):
            age = st.sidebar.number_input(
                f"Età bambino {i+1}",
                min_value=0,
                max_value=17,
                value=min(4, 17),  # Default a 4 anni, ma non oltre 17
                key=f"child_age_{i}"
            )
            children_ages.append(age)
    
    # Visualizzazione del riepilogo dell'occupazione
    occupancy_summary = f"{num_adults} adulti"
    if has_children:
        occupancy_summary += f", {len(children_ages)} bambini"
    occupancy_summary += f" in {num_rooms} {'camera' if num_rooms == 1 else 'camere'}"
    
    st.sidebar.success(f"Configurazione: {occupancy_summary}")
    
    # Visualizzazione dei prezzi
    price_view = st.sidebar.radio(
        "Visualizza prezzi",
        ["Totali", "Per notte"],
        index=0,  # Default: prezzi totali
        help="Scegli se visualizzare i prezzi totali per tutto il soggiorno o i prezzi per notte"
    )
    
    # Reset dei dati
    if st.sidebar.button("Cancella dati salvati"):
        keys_to_clear = ["rate_data", "heatmap_data"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
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
        
        with st.spinner(f"Recupero tariffe e dati per {occupancy_summary}..."):
            # Raccogli i dati per ciascun hotel selezionato
            all_data = []
            all_heatmap_data = []
            
            # Mostra stato debug
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, hotel in enumerate(selected_hotels):
                progress = int(100 * i / (2 * len(selected_hotels)))
                progress_bar.progress(progress)
                status_text.text(f"Elaborazione tariffe per {hotel}... ({i+1}/{len(selected_hotels)})")
                
                hotel_key = hotel_keys.get(hotel, "")
                if hotel_key:
                    # Ottieni le tariffe dall'API
                    response = xotelo_api.get_rates(
                        hotel_key,
                        check_in_date.strftime("%Y-%m-%d"),
                        check_out_date.strftime("%Y-%m-%d"),
                        adults=num_adults,
                        children_ages=children_ages if has_children else None,
                        rooms=num_rooms,
                        currency=currency
                    )
                    
                    # Processa la risposta, considerando il numero di notti
                    df = process_xotelo_response(
                        response, 
                        hotel,
                        num_nights,
                        num_adults,
                        len(children_ages) if has_children else 0,
                        num_rooms,
                        currency
                    )
                    
                    all_data.append(df)
            
            for i, hotel in enumerate(selected_hotels):
                progress = int(50 + 100 * i / (2 * len(selected_hotels)))
                progress_bar.progress(progress)
                status_text.text(f"Elaborazione heatmap per {hotel}... ({i+1}/{len(selected_hotels)})")
                
                hotel_key = hotel_keys.get(hotel, "")
                if hotel_key:
                    # Ottieni i dati dell'heatmap
                    heatmap_response = xotelo_api.get_heatmap(
                        hotel_key,
                        check_out_date.strftime("%Y-%m-%d")
                    )
                    
                    # Processa la risposta dell'heatmap
                    heatmap_data = process_heatmap_response(heatmap_response, hotel)
                    if heatmap_data:
                        all_heatmap_data.append(heatmap_data)
            
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
                st.session_state.occupancy = {
                    "adults": num_adults,
                    "children": len(children_ages) if has_children else 0,
                    "children_ages": children_ages if has_children else [],
                    "rooms": num_rooms
                }
                
                # Memorizza i dati dell'heatmap
                if all_heatmap_data:
                    st.session_state.heatmap_data = all_heatmap_data
                
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
        
        # Ottieni l'occupazione salvata
        saved_occupancy = st.session_state.get("occupancy", {
            "adults": 2,
            "children": 0,
            "children_ages": [],
            "rooms": 1
        })
        
        # Visualizza il banner dell'occupazione attuale nei dati
        st.info(
            f"Prezzi visualizzati per: {saved_occupancy['adults']} adulti"
            f"{', ' + str(saved_occupancy['children']) + ' bambini' if saved_occupancy['children'] > 0 else ''}"
            f" in {saved_occupancy['rooms']} {'camera' if saved_occupancy['rooms'] == 1 else 'camere'}"
        )
        
        # Avviso se l'occupazione corrente è diversa da quella nei dati
        current_occupancy_different = (
            num_adults != saved_occupancy['adults'] or
            (len(children_ages) if has_children else 0) != saved_occupancy['children'] or
            num_rooms != saved_occupancy['rooms']
        )
        
        if current_occupancy_different:
            st.warning(
                "L'occupazione selezionata è diversa da quella usata per cercare i prezzi. "
                "Clicca 'Cerca tariffe' per aggiornare i dati con la nuova occupazione."
            )
        
        # Avviso se la valuta corrente è diversa da quella nei dati
        if current_currency != currency:
            st.warning(
                f"La valuta selezionata ({currency}) è diversa da quella nei dati visualizzati ({current_currency}). "
                "Clicca 'Cerca tariffe' per aggiornare i dati con la nuova valuta."
            )
        
        # Aggiorna il conteggio delle notti se è cambiato
        if "num_nights" in st.session_state and st.session_state.num_nights != num_nights:
            # Ricalcola i prezzi totali con il nuovo numero di notti
            df["price_total"] = df["price"] * num_nights
            st.session_state.num_nights = num_nights
            st.session_state.rate_data = df
            st.info(f"Prezzi totali aggiornati per {num_nights} notti")
        
        # Simbolo della valuta
        currency_symbols = {
            "EUR": "€", "USD": "$", "GBP": "£", "CAD": "CA$", "CHF": "CHF", 
            "AUD": "A$", "JPY": "¥", "CNY": "¥", "INR": "₹", "THB": "฿", 
            "BRL": "R$", "HKD": "HK$", "RUB": "₽", "BZD": "BZ$"
        }
        currency_symbol = currency_symbols.get(current_currency, current_currency)
        
        # Crea tabs per diversi tipi di visualizzazioni
        tabs = st.tabs(["Confronto Tariffe", "Calendari Prezzi", "Analisi Comparativa"])
        
        # Tab 1: Confronto tariffe tra OTA
        with tabs[0]:
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
                        title=f"Tariffe per {selected_hotel} - {occupancy_summary} ({check_in_date.strftime('%d/%m/%Y')} - {check_out_date.strftime('%d/%m/%Y')})",
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
                
                # Visualizza tutte le OTA disponibili per ciascun hotel
                st.subheader("Tutte le OTA disponibili per hotel")
                available_df = df[df["available"]]
                all_otas_by_hotel = {}
                
                for hotel in available_df["hotel"].unique():
                    hotel_data = available_df[available_df["hotel"] == hotel]
                    all_otas_by_hotel[hotel] = sorted(hotel_data["ota"].unique())
                
                for hotel, otas in all_otas_by_hotel.items():
                    with st.expander(f"{hotel} - {len(otas)} OTA disponibili"):
                        st.write(", ".join(otas))
            else:
                st.warning("Nessun hotel disponibile per le date selezionate.")
        
        # Tab 2: Calendari dei prezzi (heatmap)
        with tabs[1]:
            st.header("Calendari Prezzi - Heatmap")
            
            if "heatmap_data" in st.session_state and st.session_state.heatmap_data:
                heatmap_data = st.session_state.heatmap_data
                
                # Seleziona hotel per la visualizzazione dell'heatmap
                available_hotels_heatmap = [data["hotel"] for data in heatmap_data]
                
                if available_hotels_heatmap:
                    selected_hotel_heatmap = st.selectbox(
                        "Seleziona hotel per visualizzare il calendario prezzi",
                        available_hotels_heatmap,
                        key="heatmap_hotel_selector"
                    )
                    
                    # Trova i dati dell'heatmap per l'hotel selezionato
                    hotel_heatmap = next((h for h in heatmap_data if h["hotel"] == selected_hotel_heatmap), None)
                    
                    if hotel_heatmap:
                        # Crea un dataframe con tutte le date del mese corrente e successivo
                        today = datetime.now()
                        
                        # Calcola le date del calendario
                        start_date = today.replace(day=1)
                        end_date = (today.replace(day=1) + timedelta(days=60)).replace(day=1)
                        
                        # Crea un calendario visivo con codice colore
                        st.subheader(f"Calendario Prezzi per {selected_hotel_heatmap}")
                        
                        # Ottieni i dati dell'heatmap
                        df_heatmap = hotel_heatmap["data"]
                        
                        # Converti la colonna delle date in stringa nel formato "YYYY-MM-DD" per il join
                        df_heatmap["date_str"] = df_heatmap["date"].dt.strftime("%Y-%m-%d")
                        
                        # Crea un dataframe per ogni mese da visualizzare
                        current_date = start_date
                        months_to_show = 2
                        
                        for month_idx in range(months_to_show):
                            # Nome del mese e anno
                            month_name = current_date.strftime("%B %Y")
                            
                            # Calcola date per il mese corrente
                            month_start = current_date.replace(day=1)
                            if current_date.month == 12:  # Dicembre
                                month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
                            else:
                                month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
                            
                            # Crea una lista di tutte le date nel mese
                            all_days = [(month_start + timedelta(days=i)) for i in range((month_end - month_start).days + 1)]
                            
                            # Crea un DataFrame per il calendario
                            calendar_data = []
                            for day in all_days:
                                day_str = day.strftime("%Y-%m-%d")
                                
                                # Trova il livello di prezzo per questa data
                                price_level = "Non disponibile"
                                level_value = 0
                                
                                # Cerca nel dataframe dell'heatmap
                                match = df_heatmap[df_heatmap["date_str"] == day_str]
                                if not match.empty:
                                    price_level = match.iloc[0]["price_level"]
                                    level_value = match.iloc[0]["level_value"]
                                
                                calendar_data.append({
                                    "date": day,
                                    "day": day.day,
                                    "weekday": day.strftime("%a"),
                                    "price_level": price_level,
                                    "level_value": level_value
                                })
                            
                            df_calendar = pd.DataFrame(calendar_data)
                            
                            # Crea una tabella per visualizzare il calendario
                            st.subheader(month_name)
                            
                            # Definisci colori per i livelli di prezzo
                            color_map = {
                                "Non disponibile": "lightgrey",
                                "Economico": "lightgreen",
                                "Medio": "khaki",
                                "Alto": "lightcoral"
                            }
                            
                            # Converti il calendario in formato settimanale
                            weeks = []
                            week = [None] * 7  # 7 giorni in una settimana, inizializzati a None
                            
                            for i, row in df_calendar.iterrows():
                                day = row["date"]
                                weekday = day.weekday()  # 0 = Lunedì, 6 = Domenica
                                
                                # Riorganizza per iniziare la settimana da lunedì (0)
                                week[weekday] = {
                                    "day": day.day,
                                    "price_level": row["price_level"],
                                    "level_value": row["level_value"]
                                }
                                
                                # Se è domenica (6) o l'ultimo giorno del mese, aggiungi la settimana
                                if weekday == 6 or i == len(df_calendar) - 1:
                                    weeks.append(week.copy())
                                    week = [None] * 7
                            
                            # Crea HTML per visualizzare il calendario
                            html_calendar = """
                            <style>
                                .calendar-table {
                                    width: 100%;
                                    border-collapse: collapse;
                                }
                                .calendar-table th, .calendar-table td {
                                    border: 1px solid #ddd;
                                    padding: 8px;
                                    text-align: center;
                                }
                                .calendar-day {
                                    font-weight: bold;
                                    font-size: 16px;
                                }
                                .price-level {
                                    font-size: 12px;
                                }
                                .price-non-disponibile { background-color: lightgrey; }
                                .price-economico { background-color: lightgreen; }
                                .price-medio { background-color: khaki; }
                                .price-alto { background-color: lightcoral; }
                            </style>
                            <table class='calendar-table'>
                                <tr>
                                    <th>Lun</th>
                                    <th>Mar</th>
                                    <th>Mer</th>
                                    <th>Gio</th>
                                    <th>Ven</th>
                                    <th>Sab</th>
                                    <th>Dom</th>
                                </tr>
                            """
                            
                            for week in weeks:
                                html_calendar += "<tr>"
                                for day in week:
                                    if day is None:
                                        html_calendar += "<td></td>"
                                    else:
                                        price_level = day["price_level"].lower()
                                        html_calendar += f"""
                                        <td class='price-{price_level.replace(" ", "-")}'>
                                            <div class='calendar-day'>{day["day"]}</div>
                                            <div class='price-level'>{day["price_level"]}</div>
                                        </td>
                                        """
                                html_calendar += "</tr>"
                            
                            html_calendar += "</table>"
                            
                            st.markdown(html_calendar, unsafe_allow_html=True)
                            
                            # Legenda
                            legend_html = """
                            <div style="display: flex; margin-top: 10px; justify-content: center;">
                                <div style="display: flex; align-items: center; margin-right: 20px;">
                                    <div style="width: 20px; height: 20px; background-color: lightgreen; margin-right: 5px;"></div>
                                    <span>Economico</span>
                                </div>
                                <div style="display: flex; align-items: center; margin-right: 20px;">
                                    <div style="width: 20px; height: 20px; background-color: khaki; margin-right: 5px;"></div>
                                    <span>Medio</span>
                                </div>
                                <div style="display: flex; align-items: center; margin-right: 20px;">
                                    <div style="width: 20px; height: 20px; background-color: lightcoral; margin-right: 5px;"></div>
                                    <span>Alto</span>
                                </div>
                                <div style="display: flex; align-items: center;">
                                    <div style="width: 20px; height: 20px; background-color: lightgrey; margin-right: 5px;"></div>
                                    <span>Non disponibile</span>
                                </div>
                            </div>
                            """
                            
                            st.markdown(legend_html, unsafe_allow_html=True)
                            
                            # Passa al mese successivo
                            if current_date.month == 12:
                                current_date = current_date.replace(year=current_date.year + 1, month=1)
                            else:
                                current_date = current_date.replace(month=current_date.month + 1)
                else:
                    st.warning("Nessun dato di calendario prezzi disponibile per gli hotel selezionati.")
            else:
                st.warning("Nessun dato di calendario prezzi disponibile. Effettua una ricerca tariffe per visualizzare i calendari.")
        
        # Tab 3: Analisi comparativa
        with tabs[2]:
            st.header("Analisi Comparativa")
            
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
                    title=f"Prezzo minimo disponibile per hotel - {occupancy_summary} ({check_in_date.strftime('%d/%m/%Y')} - {check_out_date.strftime('%d/%m/%Y')})",
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
                
                # Analisi parità tariffaria
                st.subheader("Analisi parità tariffaria")
                
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
        st.info("Clicca su 'Cerca tariffe' per recuperare i dati tariffari")
    
    # Informazioni sull'API Xotelo e l'occupazione
    with st.expander("Informazioni sui parametri di occupazione"):
        st.write("""
        I prezzi mostrati si riferiscono all'occupazione specificata nelle impostazioni (adulti, bambini e camere).
        
        L'API Xotelo consente di specificare:
        - Numero di adulti (1-32)
        - Età dei bambini (0-17 anni)
        - Numero di camere (1-8)
        - Valuta (EUR, USD, GBP, ecc.)
        
        Modificando questi parametri e facendo una nuova ricerca, otterrai i prezzi aggiornati per la configurazione scelta.
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
    
    # Informazioni sulla versione
    st.sidebar.markdown("---")
    st.sidebar.info("Versione 0.4.0 - Con supporto per heatmap di prezzo")

# Esegui l'app
if __name__ == "__main__":
    rate_checker_app()
