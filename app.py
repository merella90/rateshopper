import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import base64

st.set_page_config(
    page_title="Rate Checker VOI Alimini (BETA)",
    page_icon="📊",
    layout="wide"
)

# CSS migliorato per una sidebar professionale
st.markdown(
    """
    <style>
    /* Colori professionali */
    [data-testid="stSidebar"] {
        background-color: #2c3e50 !important; /* Blu scuro professionale */
        color: #ecf0f1 !important;
        padding: 1rem 0.5rem !important;
    }
    
    /* Titoli */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4 {
        color: #ecf0f1 !important;
        font-weight: 500 !important;
        margin-top: 1.2rem !important;
        margin-bottom: 0.8rem !important;
        border-bottom: 1px solid rgba(236, 240, 241, 0.2) !important;
        padding-bottom: 0.5rem !important;
    }
    
    /* Maggiore spazio tra i gruppi */
    [data-testid="stSidebar"] .block-container {
        padding-top: 1rem !important;
    }
    
    /* Multiselect più elegante */
    [data-testid="stSidebar"] .stMultiSelect span[data-baseweb="tag"] {
        background-color: #34495e !important;
        border: 1px solid #3498db !important;
        color: #ecf0f1 !important;
    }
    
    /* Bottoni più professionali */
    [data-testid="stSidebar"] button, 
    [data-testid="stSidebar"] [data-testid="baseButton-secondary"] {
        background-color: #3498db !important;
        color: white !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        border-radius: 4px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    [data-testid="stSidebar"] button:hover {
        background-color: #2980b9 !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
    }
    
    /* Input fields */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] [data-testid="stNumberInput"] input {
        background-color: #34495e !important;
        color: #ecf0f1 !important;
        border: 1px solid #7f8c8d !important;
        border-radius: 4px !important;
    }
    
    /* Bottoni di increment/decrement nei numeri */
    [data-testid="stSidebar"] [data-testid="stNumberInput"] button {
        background-color: #3498db !important;
        color: white !important;
        border: none !important;
    }
    
    /* Radio e checkbox */
    [data-testid="stSidebar"] .stRadio input[type="radio"], 
    [data-testid="stSidebar"] .stCheckbox input[type="checkbox"] {
        accent-color: #3498db !important;
    }
    
    /* Info, success e warning messages */
    [data-testid="stSidebar"] .stAlert {
        background-color: #34495e !important;
        color: #ecf0f1 !important;
        border-left: 4px solid #3498db !important;
        padding: 0.8rem !important;
        margin: 0.8rem 0 !important;
    }
    
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] label {
        color: #ecf0f1 !important;
    }
    
    /* Il pulsante rosso può rimanere ma con un rosso più adeguato */
    [data-testid="stSidebar"] [aria-checked="true"] {
        background-color: #e74c3c !important;
    }
    
    /* Logo container */
    .sidebar-logo {
        background-color: #2c3e50 !important;
        padding: 1.2rem 0 !important;
        margin-bottom: 1rem !important;
        text-align: center !important;
        border-bottom: 1px solid rgba(236, 240, 241, 0.2) !important;
    }
    
    /* Rendere gli elementi di data input più coerenti */
    [data-testid="stSidebar"] .stDateInput input {
        background-color: #34495e !important;
        color: #ecf0f1 !important;
        border: 1px solid #7f8c8d !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
class XoteloAPI:
    def __init__(self):
        self.base_url = "https://data.xotelo.com/api"
    
    def get_rates(self, hotel_key, check_in, check_out, adults=2, children_ages=None, rooms=1, currency="EUR"):
        endpoint = f"{self.base_url}/rates"
        params = {
            "hotel_key": hotel_key,
            "chk_in": check_in,
            "chk_out": check_out,
            "adults": adults,
            "rooms": rooms,
            "currency": currency
        }
        
        if children_ages and len(children_ages) > 0:
            params["age_of_children"] = ",".join(map(str, children_ages))
        
        try:
            response = requests.get(endpoint, params=params)
            return response.json()
        except Exception as e:
            return {"error": str(e), "timestamp": 0, "result": None}
    
    def get_heatmap(self, hotel_key, check_out):
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

hotel_keys = {
    "VOI Alimini": "g652004-d1799967",  
    "Ciaoclub Arco Del Saracino": "g946998-d947000", 
    "Hotel Alpiselect Robinson Apulia": "g947837-d949958",  
    "Alpiclub Hotel Thalas Club": "g1179328-d1159227" 
}

location_key = "g652004"

def process_xotelo_response(response, hotel_name, num_nights=1, adults=2, children_count=0, rooms=1, currency="EUR"):
    if response.get("error") is not None or response.get("result") is None:
        return pd.DataFrame([{
            "hotel": hotel_name,
            "ota": "N/A",
            "ota_code": "N/A",
            "price": 0,
            "price_total": 0,
            "currency": currency,
            "check_in": "",
            "check_out": "",
            "timestamp": 0,
            "available": False,
            "message": "Dati non disponibili/sold out",
            "adults": adults,
            "children": children_count,
            "rooms": rooms
        }])
    
    rates = response.get("result", {}).get("rates", [])
    check_in = response.get("result", {}).get("chk_in", "")
    check_out = response.get("result", {}).get("chk_out", "")
    
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
        price_per_night = rate.get("rate", 0)
        total_price = price_per_night * num_nights
        
        data.append({
            "hotel": hotel_name,
            "ota": rate.get("name", ""),
            "ota_code": rate.get("code", ""),
            "price": price_per_night,
            "price_total": total_price,
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

def process_heatmap_response(response, hotel_name):
    if response.get("error") is not None or response.get("result") is None:
        return None
    
    heatmap_data = response.get("result", {}).get("heatmap", {})
    
    if not heatmap_data:
        return None
    
    average_days = heatmap_data.get("average_price_days", [])
    cheap_days = heatmap_data.get("cheap_price_days", [])
    high_days = heatmap_data.get("high_price_days", [])
    
    formatted_average_days = [datetime.strptime(date, "%Y-%m-%d") for date in average_days]
    formatted_cheap_days = [datetime.strptime(date, "%Y-%m-%d") for date in cheap_days]
    formatted_high_days = [datetime.strptime(date, "%Y-%m-%d") for date in high_days]
    
    all_dates = []
    
    for date in formatted_cheap_days:
        all_dates.append({
            "hotel": hotel_name,
            "date": date,
            "price_level": "Economico",
            "level_value": 1
        })
    
    for date in formatted_average_days:
        all_dates.append({
            "hotel": hotel_name,
            "date": date,
            "price_level": "Medio",
            "level_value": 2
        })
    
    for date in formatted_high_days:
        all_dates.append({
            "hotel": hotel_name,
            "date": date,
            "price_level": "Alto",
            "level_value": 3
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

def process_hotel_list_response(response):
    if response.get("error") is not None or response.get("result") is None:
        return None
    
    hotels_list = response.get("result", {}).get("list", [])
    
    if not hotels_list:
        return None
    
    data = []
    for hotel in hotels_list:
        try:
            hotel_key = hotel.get("key", "")
            name = hotel.get("name", "")
            accommodation_type = hotel.get("accommodation_type", "")
            url = hotel.get("url", "")
            
            review_summary = hotel.get("review_summary", {}) or {}
            rating = review_summary.get("rating", 0) if isinstance(review_summary, dict) else 0
            review_count = review_summary.get("count", 0) if isinstance(review_summary, dict) else 0
            
            price_ranges = hotel.get("price_ranges", {}) or {}
            min_price = price_ranges.get("minimum", 0) if isinstance(price_ranges, dict) else 0
            max_price = price_ranges.get("maximum", 0) if isinstance(price_ranges, dict) else 0
            
            geo = hotel.get("geo", {}) or {}
            latitude = geo.get("latitude", 0) if isinstance(geo, dict) else 0
            longitude = geo.get("longitude", 0) if isinstance(geo, dict) else 0
            
            amenities = hotel.get("highlighted_amenities", []) or []
            amenities_list = [a.get("name", "") for a in amenities] if isinstance(amenities, list) else []
            amenities_str = ", ".join(filter(None, amenities_list))
            
            data.append({
                "hotel_key": hotel_key,
                "name": name,
                "accommodation_type": accommodation_type,
                "url": url,
                "rating": rating,
                "review_count": review_count,
                "min_price": min_price,
                "max_price": max_price,
                "latitude": latitude,
                "longitude": longitude,
                "amenities": amenities_str
            })
        except Exception as e:
            continue
    
    if data:
        return pd.DataFrame(data)
    else:
        return None

def normalize_dataframe(df, num_nights):
    normalized_df = df.copy()
    
    columns = df.columns.tolist()
    
    if "price" in columns and "price_night" not in columns:
        normalized_df["price_night"] = normalized_df["price"]
    elif "price_night" in columns and "price" not in columns:
        normalized_df["price"] = normalized_df["price_night"]
    elif "price" not in columns and "price_night" not in columns:
        if "price_total" in columns:
            normalized_df["price"] = normalized_df["price_total"] / num_nights
            normalized_df["price_night"] = normalized_df["price"]
        else:
            normalized_df["price"] = 0
            normalized_df["price_night"] = 0
            normalized_df["price_total"] = 0
    
    if "price_total" not in columns:
        if "price" in columns:
            normalized_df["price_total"] = normalized_df["price"] * num_nights
        elif "price_night" in columns:
            normalized_df["price_total"] = normalized_df["price_night"] * num_nights
        else:
            normalized_df["price_total"] = 0
    
    if "is_available" in columns and "available" not in columns:
        normalized_df["available"] = normalized_df["is_available"]
    elif "available" in columns and "is_available" not in columns:
        normalized_df["is_available"] = normalized_df["available"]
    elif "available" not in columns and "is_available" not in columns:
        normalized_df["available"] = normalized_df["price"] > 0
        normalized_df["is_available"] = normalized_df["available"]
    
    if "message" not in columns:
        normalized_df["message"] = ""
        if "available" in columns:
            normalized_df.loc[~normalized_df["available"], "message"] = "Dati non disponibili/sold out"
        elif "is_available" in columns:
            normalized_df.loc[~normalized_df["is_available"], "message"] = "Dati non disponibili/sold out"
    
    if "adults" not in columns:
        normalized_df["adults"] = 2
    if "children" not in columns:
        normalized_df["children"] = 0
    if "rooms" not in columns:
        normalized_df["rooms"] = 1
    
    return normalized_df

def rate_checker_app():
    st.title("Rate Checker VOI Alimini (Beta)")
    st.subheader("Confronto tariffe basato su TripAdvisor")
    
    if "currency" not in st.session_state:
        st.session_state.currency = "EUR"
    
    st.sidebar.header("Parametri di ricerca")
    
    currency = st.sidebar.selectbox(
        "Valuta",
        ["EUR", "USD", "GBP", "CAD", "CHF", "AUD", "JPY", "CNY", "INR", "THB", "BRL", "HKD", "RUB", "BZD"],
        index=0
    )
    
    competitors = list(hotel_keys.keys())
    selected_hotels = st.sidebar.multiselect(
        "Hotel da confrontare",
        competitors,
        default=competitors
    )
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        check_in_date = st.date_input("Check-in", datetime.now())
    with col2:
        check_out_date = st.date_input("Check-out", datetime.now() + timedelta(days=7))
    
    num_nights = (check_out_date - check_in_date).days
    if num_nights <= 0:
        st.sidebar.error("La data di check-out deve essere successiva alla data di check-in!")
        num_nights = 1
    else:
        st.sidebar.info(f"Durata soggiorno: {num_nights} {'notte' if num_nights == 1 else 'notti'}")
    
    st.sidebar.header("Occupazione")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        num_adults = st.number_input("Adulti", min_value=1, max_value=32, value=2)
    with col2:
        num_rooms = st.number_input("Camere", min_value=1, max_value=8, value=1)
    
    has_children = st.sidebar.checkbox("Aggiungi bambini")
    children_ages = []
    
    if has_children:
        num_children = st.sidebar.number_input("Numero bambini", min_value=1, max_value=16, value=1)
        
        for i in range(num_children):
            age = st.sidebar.number_input(
                f"Età bambino {i+1}",
                min_value=0,
                max_value=17,
                value=min(4, 17),
                key=f"child_age_{i}"
            )
            children_ages.append(age)
    
    occupancy_summary = f"{num_adults} adulti"
    if has_children:
        occupancy_summary += f", {len(children_ages)} bambini"
    occupancy_summary += f" in {num_rooms} {'camera' if num_rooms == 1 else 'camere'}"
    
    st.sidebar.success(f"Configurazione: {occupancy_summary}")
    
    price_view = st.sidebar.radio(
        "Visualizza prezzi",
        ["Totali", "Per notte"],
        index=0,
        help="Scegli se visualizzare i prezzi totali per tutto il soggiorno o i prezzi per notte"
    )
    
    if st.sidebar.button("Cancella dati salvati"):
        keys_to_clear = ["rate_data", "heatmap_data", "hotel_info", "raw_hotel_data"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.sidebar.success("Dati cancellati con successo.")
        st.rerun()
    
    use_total_price = (price_view == "Totali")
    price_column = "price_total" if use_total_price else "price"
    price_description = f"{'totali per ' + str(num_nights) + ' notti' if use_total_price else 'per notte'}"
    
    if st.sidebar.button("Cerca tariffe"):
        xotelo_api = XoteloAPI()
        
        with st.spinner(f"Recupero tariffe e dati per {occupancy_summary}..."):
            all_data = []
            all_heatmap_data = []
            all_raw_hotel_data = {}
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, hotel in enumerate(selected_hotels):
                progress = int(100 * i / (4 * len(selected_hotels)))
                progress_bar.progress(progress)
                status_text.text(f"Elaborazione tariffe per {hotel}... ({i+1}/{len(selected_hotels)})")
                
                hotel_key = hotel_keys.get(hotel, "")
                if hotel_key:
                    response = xotelo_api.get_rates(
                        hotel_key,
                        check_in_date.strftime("%Y-%m-%d"),
                        check_out_date.strftime("%Y-%m-%d"),
                        adults=num_adults,
                        children_ages=children_ages if has_children else None,
                        rooms=num_rooms,
                        currency=currency
                    )
                    
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
                progress = int(25 + 100 * i / (4 * len(selected_hotels)))
                progress_bar.progress(progress)
                status_text.text(f"Elaborazione heatmap per {hotel}... ({i+1}/{len(selected_hotels)})")
                
                hotel_key = hotel_keys.get(hotel, "")
                if hotel_key:
                    heatmap_response = xotelo_api.get_heatmap(
                        hotel_key,
                        check_out_date.strftime("%Y-%m-%d")
                    )
                    
                    heatmap_data = process_heatmap_response(heatmap_response, hotel)
                    if heatmap_data:
                        all_heatmap_data.append(heatmap_data)
            
            status_text.text("Recupero informazioni hotel dalla località...")
            progress_bar.progress(50)
            
            try:
                hotel_list_response = xotelo_api.get_hotel_list(
                    location_key,
                    limit=100,
                    sort="best_value"
                )
                
                hotel_info_df = process_hotel_list_response(hotel_list_response)
                
                if hotel_info_df is not None:
                    all_raw_hotel_data["location_search"] = hotel_info_df.to_dict()
                
                individual_hotel_data = []
                
                for idx, (hotel_name, hotel_key) in enumerate(hotel_keys.items()):
                    progress = int(75 + 25 * idx / len(hotel_keys))
                    progress_bar.progress(progress)
                    status_text.text(f"Recupero rating per {hotel_name}...")
                    
                    location_id = hotel_key.split("-")[0]
                    
                    try:
                        single_hotel_response = xotelo_api.get_hotel_list(
                            location_id,
                            limit=30, 
                            sort="best_value"
                        )
                        
                        single_hotel_df = process_hotel_list_response(single_hotel_response)
                        
                        if single_hotel_df is not None:
                            all_raw_hotel_data[f"search_{hotel_name}"] = single_hotel_df.to_dict()
                            
                            match_hotel = single_hotel_df[single_hotel_df["hotel_key"] == hotel_key]
                            if not match_hotel.empty:
                                match_hotel = match_hotel.copy()
                                match_hotel["our_hotel_name"] = hotel_name
                                individual_hotel_data.append(match_hotel)
                            else:
                                st.warning(f"Hotel {hotel_name} (chiave: {hotel_key}) non trovato nei risultati di ricerca.")
                    except Exception as e:
                        st.warning(f"Errore nel recupero dei dati per {hotel_name}: {str(e)}")
                
                st.session_state.raw_hotel_data = all_raw_hotel_data
                
                merged_hotel_info = None
                
                if individual_hotel_data:
                    individual_df = pd.concat(individual_hotel_data, ignore_index=True)
                    if hotel_info_df is not None and not hotel_info_df.empty:
                        hotel_info_df["our_hotel_name"] = hotel_info_df["hotel_key"].apply(
                            lambda x: hotel_keys.get(x, "")
                        )
                        merged_hotel_info = pd.concat([individual_df, hotel_info_df], ignore_index=True)
                        merged_hotel_info = merged_hotel_info.drop_duplicates(subset=["hotel_key"])
                    else:
                        merged_hotel_info = individual_df
                elif hotel_info_df is not None:
                    hotel_key_to_name = {v: k for k, v in hotel_keys.items()}
                    hotel_info_df["our_hotel_name"] = hotel_info_df["hotel_key"].apply(
                        lambda x: hotel_key_to_name.get(x, "")
                    )
                    merged_hotel_info = hotel_info_df
                
                if merged_hotel_info is not None:
                    filtered_hotel_info = merged_hotel_info[merged_hotel_info["our_hotel_name"] != ""].copy()
                    if not filtered_hotel_info.empty:
                        st.session_state.hotel_info = filtered_hotel_info
                
            except Exception as e:
                st.warning(f"Non è stato possibile recuperare le informazioni degli hotel: {str(e)}")
            
            progress_bar.progress(100)
            status_text.text("Elaborazione completata!")
            
            if all_data:
                combined_df = pd.concat(all_data, ignore_index=True)
                
                normalized_df = normalize_dataframe(combined_df, num_nights)
                
                st.session_state.rate_data = normalized_df
                st.session_state.currency = currency
                st.session_state.num_nights = num_nights
                st.session_state.occupancy = {
                    "adults": num_adults,
                    "children": len(children_ages) if has_children else 0,
                    "children_ages": children_ages if has_children else [],
                    "rooms": num_rooms
                }
                
                if all_heatmap_data:
                    st.session_state.heatmap_data = all_heatmap_data
                
                available_hotels = normalized_df[normalized_df["available"]]["hotel"].unique()
                unavailable_hotels = normalized_df[~normalized_df["available"]]["hotel"].unique()
                
                if len(unavailable_hotels) > 0:
                    st.warning(f"Hotel non disponibili: {', '.join(unavailable_hotels)}")
                
                st.success(f"Dati tariffari recuperati con successo per {len(available_hotels)} hotel!")
            else:
                st.error("Nessun dato recuperato. Verifica le chiavi degli hotel e riprova.")
    
    if "rate_data" in st.session_state:
        df = st.session_state.rate_data
        
        df = normalize_dataframe(df, num_nights)
        st.session_state.rate_data = df
        
        current_currency = st.session_state.currency
        
        saved_occupancy = st.session_state.get("occupancy", {
            "adults": 2,
            "children": 0,
            "children_ages": [],
            "rooms": 1
        })
        
        st.info(
            f"Prezzi visualizzati per: {saved_occupancy['adults']} adulti"
            f"{', ' + str(saved_occupancy['children']) + ' bambini' if saved_occupancy['children'] > 0 else ''}"
            f" in {saved_occupancy['rooms']} {'camera' if saved_occupancy['rooms'] == 1 else 'camere'}"
        )
        
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
        
        if current_currency != currency:
            st.warning(
                f"La valuta selezionata ({currency}) è diversa da quella nei dati visualizzati ({current_currency}). "
                "Clicca 'Cerca tariffe' per aggiornare i dati con la nuova valuta."
            )
        
        if "num_nights" in st.session_state and st.session_state.num_nights != num_nights:
            df["price_total"] = df["price"] * num_nights
            st.session_state.num_nights = num_nights
            st.session_state.rate_data = df
            st.info(f"Prezzi totali aggiornati per {num_nights} notti")
        
        currency_symbols = {
            "EUR": "€", "USD": "$", "GBP": "£", "CAD": "CA$", "CHF": "CHF", 
            "AUD": "A$", "JPY": "¥", "CNY": "¥", "INR": "₹", "THB": "฿", 
            "BRL": "R$", "HKD": "HK$", "RUB": "₽", "BZD": "BZ$"
        }
        currency_symbol = currency_symbols.get(current_currency, current_currency)
        
        tabs = st.tabs(["Confronto Tariffe", "Calendari Prezzi", "Analisi Comparativa", "Rating e Qualità", "Debug"])
        
        with tabs[0]:
            st.header(f"Confronto tariffe tra OTA (Prezzi {price_description})")
            
            available_hotels = df[df["available"]]["hotel"].unique()
            
            if len(available_hotels) > 0:
                selected_hotel = st.selectbox(
                    "Seleziona hotel da analizzare",
                    available_hotels
                )
                
                hotel_df = df[(df["hotel"] == selected_hotel) & df["available"]]
                
                if not hotel_df.empty:
                    ota_count = len(hotel_df["ota"].unique())
                    st.info(f"Trovate {ota_count} OTA per {selected_hotel}")
                    
                    fig = px.bar(
                        hotel_df,
                        x="ota",
                        y=price_column,
                        title=f"Tariffe per {selected_hotel} - {occupancy_summary} ({check_in_date.strftime('%d/%m/%Y')} - {check_out_date.strftime('%d/%m/%Y')})",
                        color="ota",
                        labels={price_column: f"Prezzo {price_description} ({currency_symbol})", "ota": "OTA"}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
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
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        min_price_night = hotel_df["price"].min()
                        min_ota_night = hotel_df.loc[hotel_df["price"].idxmin(), "ota"]
                        st.info(f"Prezzo minimo per notte: {currency_symbol}{min_price_night:.2f} via {min_ota_night}")
                    
                    with col2:
                        min_price_total = hotel_df["price_total"].min()
                        min_ota_total = hotel_df.loc[hotel_df["price_total"].idxmin(), "ota"]
                        st.info(f"Prezzo totale per {num_nights} notti: {currency_symbol}{min_price_total:.2f} via {min_ota_total}")
                    
                    st.subheader("Dettaglio tariffe per tutte le OTA")
                    columns_to_show = ["ota", "price", "price_total"]
                    display_df = hotel_df[columns_to_show].sort_values(by=price_column).copy()
                    display_df["price"] = display_df["price"].apply(lambda x: f"{currency_symbol}{x:.2f}")
                    display_df["price_total"] = display_df["price_total"].apply(lambda x: f"{currency_symbol}{x:.2f}")
                    display_df.columns = ["OTA", f"Prezzo per notte ({currency_symbol})", f"Prezzo totale per {num_nights} notti ({currency_symbol})"]
                    st.dataframe(display_df, use_container_width=True)
                
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
        
        with tabs[1]:
            st.header("Calendari Prezzi - Heatmap")
            
            if "heatmap_data" in st.session_state and st.session_state.heatmap_data:
                heatmap_data = st.session_state.heatmap_data
                
                available_hotels_heatmap = [data["hotel"] for data in heatmap_data]
                
                if available_hotels_heatmap:
                    selected_hotel_heatmap = st.selectbox(
                        "Seleziona hotel per visualizzare il calendario prezzi",
                        available_hotels_heatmap,
                        key="heatmap_hotel_selector"
                    )
                    
                    hotel_heatmap = next((h for h in heatmap_data if h["hotel"] == selected_hotel_heatmap), None)
                    
                    if hotel_heatmap:
                        today = datetime.now()
                        
                        start_date = today.replace(day=1)
                        end_date = (today.replace(day=1) + timedelta(days=60)).replace(day=1)
                        
                        st.subheader(f"Calendario Prezzi per {selected_hotel_heatmap}")
                        
                        df_heatmap = hotel_heatmap["data"]
                        
                        df_heatmap["date_str"] = df_heatmap["date"].dt.strftime("%Y-%m-%d")
                        
                        current_date = start_date
                        months_to_show = 2
                        
                        for month_idx in range(months_to_show):
                            month_name = current_date.strftime("%B %Y")
                            
                            month_start = current_date.replace(day=1)
                            if current_date.month == 12:
                                month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
                            else:
                                month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
                            
                            all_days = [(month_start + timedelta(days=i)) for i in range((month_end - month_start).days + 1)]
                            
                            calendar_data = []
                            for day in all_days:
                                day_str = day.strftime("%Y-%m-%d")
                                
                                price_level = "Non disponibile"
                                level_value = 0
                                
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
                            
                            st.subheader(month_name)
                            
                            color_map = {
                                "Non disponibile": "lightgrey",
                                "Economico": "lightgreen",
                                "Medio": "khaki",
                                "Alto": "lightcoral"
                            }
                            
                            weeks = []
                            week = [None] * 7
                            
                            for i, row in df_calendar.iterrows():
                                day = row["date"]
                                weekday = day.weekday()
                                
                                week[weekday] = {
                                    "day": day.day,
                                    "price_level": row["price_level"],
                                    "level_value": row["level_value"]
                                }
                                
                                if weekday == 6 or i == len(df_calendar) - 1:
                                    weeks.append(week.copy())
                                    week = [None] * 7
                            
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
                            
                            if current_date.month == 12:
                                current_date = current_date.replace(year=current_date.year + 1, month=1)
                            else:
                                current_date = current_date.replace(month=current_date.month + 1)
                else:
                    st.warning("Nessun dato di calendario prezzi disponibile per gli hotel selezionati.")
            else:
                st.warning("Nessun dato di calendario prezzi disponibile. Effettua una ricerca tariffe per visualizzare i calendari.")
        
        with tabs[2]:
            st.header("Analisi Comparativa")
            
            available_df = df[df["available"]]
            
            if not available_df.empty:
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
                
                fig = px.bar(
                    min_prices_df,
                    x="hotel",
                    y="min_price",
                    title=f"Prezzo minimo disponibile per hotel - {occupancy_summary} ({check_in_date.strftime('%d/%m/%Y')} - {check_out_date.strftime('%d/%m/%Y')})",
                    color="hotel",
                    labels={"min_price": f"Prezzo minimo {price_description} ({currency_symbol})", "hotel": "Hotel"}
                )
                
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
                
                st.subheader(f"Confronto prezzi minimi tra hotel ({price_description})")
                display_min_prices = min_prices_df.copy()
                display_min_prices["min_price"] = display_min_prices["min_price"].apply(lambda x: f"{currency_symbol}{x:.2f}")
                display_min_prices.columns = ["Hotel", "Prezzo minimo", "OTA", "Numero OTA disponibili"]
                st.dataframe(display_min_prices.sort_values(by="Prezzo minimo"), use_container_width=True)
                
                st.subheader("Analisi parità tariffaria")
                
                reference_hotel = "VOI Alimini" if "VOI Alimini" in available_df["hotel"].unique() else available_df["hotel"].iloc[0]
                
                ref_min_price = available_df[available_df["hotel"] == reference_hotel][price_column].min()
                
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
                    
                    st.subheader("Dettaglio analisi parità tariffaria")
                    
                    display_df = parity_df.copy()
                    display_df["min_price"] = display_df["min_price"].apply(lambda x: f"{currency_symbol}{x:.2f}")
                    display_df["price_diff"] = display_df["price_diff"].apply(lambda x: f"{currency_symbol}{x:.2f}")
                    display_df["perc_diff"] = display_df["perc_diff"].apply(lambda x: f"{x:.2f}%")
                    
                    st.dataframe(display_df, use_container_width=True)
            
            unavailable_hotels = df[~df["available"]]["hotel"].unique()
            if len(unavailable_hotels) > 0:
                st.header("Hotel non disponibili")
                unavailable_df = df[~df["available"]][["hotel", "message"]].drop_duplicates()
                st.warning(f"I seguenti hotel non hanno disponibilità: {', '.join(unavailable_hotels)}")
                st.dataframe(unavailable_df, use_container_width=True)
        
        with tabs[3]:
            st.header("Rating e Qualità degli Hotel")
            
            if "hotel_info" in st.session_state and not st.session_state.hotel_info.empty:
                hotel_info_df = st.session_state.hotel_info
                
                has_rating = "rating" in hotel_info_df.columns
                
                if has_rating:
                    st.subheader("Confronto Rating e Prezzi")
                    
                    rating_comparison = []
                    for hotel_name in hotel_keys.keys():
                        hotel_rating_info = hotel_info_df[hotel_info_df["our_hotel_name"] == hotel_name]
                        
                        min_price = None
                        if hotel_name in available_df["hotel"].unique():
                            hotel_data = available_df[available_df["hotel"] == hotel_name]
                            min_price = hotel_data[price_column].min()
                        
                        rating = "N/A"
                        review_count = 0
                        if not hotel_rating_info.empty:
                            rating_value = hotel_rating_info.iloc[0]["rating"]
                            review_count = hotel_rating_info.iloc[0]["review_count"]
                            rating = f"{rating_value}/5"
                        
                        price_display = f"{currency_symbol}{min_price:.2f}" if min_price is not None else "Non disponibile"
                        
                        rating_comparison.append({
                            "Hotel": hotel_name,
                            "Rating": rating,
                            "Prezzo minimo": price_display
                        })
                    
                    comparison_df = pd.DataFrame(rating_comparison)
                    st.dataframe(comparison_df, use_container_width=True)
                    
                    rating_data = []
                    
                    for _, row in hotel_info_df.iterrows():
                        hotel_name = row["our_hotel_name"]
                        min_price = None
                        
                        if hotel_name in available_df["hotel"].unique():
                            hotel_data = available_df[available_df["hotel"] == hotel_name]
                            min_price = hotel_data[price_column].min()
                        
                        if min_price is not None and row["rating"] > 0:
                            rating_data.append({
                                "hotel": hotel_name,
                                "rating": row["rating"],
                                "review_count": row["review_count"],
                                "min_price": min_price,
                                "amenities": row["amenities"]
                            })
                    
                    if rating_data:
                        rating_df = pd.DataFrame(rating_data)
                        
                        st.subheader("Valutazioni TripAdvisor degli hotel")
                        
                        for i, row in rating_df.iterrows():
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                st.markdown(f"**{row['hotel']}**")
                            with col2:
                                stars = "★" * int(row["rating"]) + "☆" * (5 - int(row["rating"]))
                                decimal = row["rating"] - int(row["rating"])
                                if decimal >= 0.5:
                                    stars = stars.replace("☆", "✫", 1)
                                
                                st.markdown(f"{stars} ({row['rating']}/5 - {row['review_count']} recensioni)")
                        
                        fig = px.bar(
                            rating_df,
                            x="hotel",
                            y="rating",
                            title="Rating degli hotel su TripAdvisor",
                            color="rating",
                            color_continuous_scale="Viridis",
                            labels={"rating": "Punteggio (1-5)", "hotel": "Hotel"},
                            text="rating"
                        )
                        
                        fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
                        fig.update_layout(yaxis_range=[0, 5.5])
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.subheader("Rapporto Qualità/Prezzo")
                        
                        rating_df["quality_price_ratio"] = rating_df["rating"] / rating_df["min_price"] * 100
                        
                        rating_df_sorted = rating_df.sort_values("quality_price_ratio", ascending=False)
                        
                        qp_fig = px.bar(
                            rating_df_sorted,
                            x="hotel",
                            y="quality_price_ratio",
                            title="Indice di Qualità/Prezzo (Rating/Prezzo × 100)",
                            color="quality_price_ratio",
                            color_continuous_scale="RdYlGn",
                            labels={"quality_price_ratio": "Indice Q/P", "hotel": "Hotel"}
                        )
                        
                        st.plotly_chart(qp_fig, use_container_width=True)
                        
                        scatter_fig = px.scatter(
                            rating_df,
                            x="min_price",
                            y="rating",
                            color="hotel",
                            size="review_count",
                            hover_name="hotel",
                            labels={
                                "min_price": f"Prezzo minimo {price_description} ({currency_symbol})",
                                "rating": "Rating (1-5)",
                                "review_count": "Numero recensioni"
                            },
                            title="Confronto Prezzo vs Rating"
                        )
                        
                        price_min = rating_df["min_price"].min() * 0.8
                        price_max = rating_df["min_price"].max() * 1.2
                        avg_qp = rating_df["quality_price_ratio"].median() / 100
                        
                        scatter_fig.add_trace(
                            go.Scatter(
                                x=[price_min, price_max],
                                y=[price_min * avg_qp, price_max * avg_qp],
                                mode="lines",
                                line=dict(dash="dash", color="gray"),
                                name="Rapporto Q/P medio"
                            )
                        )
                        
                        for i, row in rating_df.iterrows():
                            scatter_fig.add_annotation(
                                x=row["min_price"],
                                y=row["rating"],
                                text=row["hotel"],
                                showarrow=False,
                                yshift=10
                            )
                        
                        st.plotly_chart(scatter_fig, use_container_width=True)
                    else:
                        st.warning("Non è stato possibile abbinare i dati di rating con i prezzi degli hotel.")
                else:
                    st.warning("Nessun dato di rating disponibile per gli hotel selezionati.")
            else:
                st.warning("Nessun dato di rating disponibile. Effettua una ricerca tariffe per visualizzare i rating.")
        
        with tabs[4]:
            st.header("Debug e Informazioni Tecniche")
            
            with st.expander("Dati delle chiamate API"):
                if "raw_hotel_data" in st.session_state:
                    raw_data = st.session_state.raw_hotel_data
                    
                    st.subheader("Dati grezzi ricevuti dalle API")
                    
                    for key, value in raw_data.items():
                        st.markdown(f"**{key}**")
                        try:
                            data_df = pd.DataFrame.from_dict(value)
                            st.dataframe(data_df)
                        except Exception as e:
                            st.write(f"Errore nella visualizzazione dei dati: {str(e)}")
                
                if "hotel_info" in st.session_state:
                    st.subheader("Dati hotel elaborati")
                    st.dataframe(st.session_state.hotel_info)
            
            with st.expander("Chiavi hotel configurate"):
                st.write("Hotel configurati nell'applicazione:")
                for hotel_name, hotel_key in hotel_keys.items():
                    st.write(f"- **{hotel_name}**: `{hotel_key}`")
    else:
        st.info("Clicca su 'Cerca tariffe' per recuperare i dati tariffari")
    
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
    
    with st.expander("Come trovare la chiave TripAdvisor dell'hotel"):
        st.write("""
        Per utilizzare questa app, è necessario avere la chiave TripAdvisor per ciascun hotel. Ecco come trovarla:
        
        1. Vai alla pagina dell'hotel su TripAdvisor.it o TripAdvisor.com
        2. Osserva l'URL, che sarà simile a: `https://www.tripadvisor.it/Hotel_Review-g1234567-d12345678-Reviews-Hotel_Name.html`
        3. La chiave è la parte `g1234567-d12345678`
        
        """)
    
    st.sidebar.markdown("---")
    st.sidebar.info("Versione 0.5.0 - Developed by Alessandro Merella with Xotelo API")

if __name__ == "__main__":
    rate_checker_app()
