import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import base64
import locale

# Imposta locale italiana per nomi mesi e giorni
try:
    locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'it_IT')
    except:
        pass  # Fallback alla locale di default

st.set_page_config(
    page_title="Rate Checker VOI Alimini (BETA)",
    page_icon="📊",
    layout="wide"
)

# Aggiunta di Font Awesome per le icone
st.markdown(
    """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    """,
    unsafe_allow_html=True
)

# CSS personalizzato per la sidebar e gli elementi
st.markdown(
    """
    <style>
    /* Colori base */
    [data-testid="stSidebar"] {
        background-color: #0f7378 !important;
        color: white !important;
    }
    [data-testid="stSidebar"] .css-1d391kg {
        padding-top: 0;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 0;
    }
    
    /* Contenitore del logo */
    .sidebar-logo {
        text-align: center;
        padding: 20px 0;
        margin-bottom: 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        background-color: rgba(255, 255, 255, 0.05);
    }
    
    /* Stile immagine logo */
    .sidebar-logo img {
        max-width: 80%;
        height: auto;
        filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.2));
        transition: all 0.3s ease;
    }
    
    /* Effetto hover sul logo */
    .sidebar-logo img:hover {
        transform: scale(1.05);
    }
    
    /* Testo sottotitolo del logo */
    .logo-subtitle {
        color: rgba(255, 255, 255, 0.8);
        font-size: 12px;
        margin-top: 5px;
        font-style: italic;
    }
    
    /* Miglioramento delle pills del multiselect */
    [data-testid="stSidebar"] .stMultiSelect span[data-baseweb="tag"] {
        background-color: #0a5c60 !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 4px !important;
        margin: 2px !important;
        padding: 5px 8px !important;
        font-size: 0.9em !important;
    }
    
    [data-testid="stSidebar"] .stMultiSelect span[data-baseweb="tag"]:hover {
        background-color: #084548 !important;
        border-color: white !important;
    }
    
    /* Miglioramento pulsante X nelle pills */
    [data-testid="stSidebar"] .stMultiSelect span[data-baseweb="tag"] button {
        background-color: transparent !important;
        color: rgba(255, 255, 255, 0.8) !important;
        border: none !important;
        font-weight: bold !important;
        padding: 0 4px !important;
        margin-left: 5px !important;
    }
    
    [data-testid="stSidebar"] .stMultiSelect span[data-baseweb="tag"] button:hover {
        color: white !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-radius: 50% !important;
    }
    
    /* Radio e checkbox */
    [data-testid="stSidebar"] .stRadio input,
    [data-testid="stSidebar"] .stCheckbox input {
        accent-color: #f5f5f5 !important;
    }
    
    /* Testo e label */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4, [data-testid="stSidebar"] h5, [data-testid="stSidebar"] h6,
    [data-testid="stSidebar"] p {
        color: white !important;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }
    [data-testid="stSidebar"] .css-pkbazv {
        color: white !important;
    }
    [data-testid="stSidebar"] .css-16idsys p {
        color: white !important;
    }
    [data-testid="stSidebar"] .e1nzilvr1 {
        color: white !important;
    }
    
    /* Banner informativi */
    .info-banner {
        background-color: rgba(255, 255, 255, 0.1);
        border-left: 3px solid rgba(255, 255, 255, 0.7);
        padding: 10px 15px;
        margin: 12px 0;
        border-radius: 0 4px 4px 0;
        display: flex;
        align-items: center;
    }
    
    /* Icone per i banner */
    .info-banner i {
        margin-right: 10px;
        color: rgba(255, 255, 255, 0.9);
    }
    
    /* Testo nei banner */
    .info-banner-text {
        font-size: 14px;
        font-weight: 500;
        color: white;
    }
    
    /* Evidenziazione dei valori numerici */
    .info-banner-value {
        font-weight: 700;
    }
    
    /* Stile bottone primario */
    [data-testid="stSidebar"] button[kind="primary"] {
        background-color: #f5f5f5 !important;
        color: #0a5c60 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
        transition: all 0.2s !important;
        border: none !important;
        width: 100% !important;
        margin: 8px 0 !important;
    }
    
    [data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: white !important;
        box-shadow: 0 3px 8px rgba(0,0,0,0.2) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Stile bottone secondario */
    [data-testid="stSidebar"] button[kind="secondary"] {
        background-color: transparent !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.6) !important;
        border-radius: 6px !important;
        font-weight: 400 !important;
        padding: 0.4rem 0.8rem !important;
        transition: all 0.2s !important;
        width: 100% !important;
        margin: 5px 0 !important;
    }
    
    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: rgba(255,255,255,0.1) !important;
        border-color: white !important;
    }
    
    /* Miglioramento bottoni +/- nei selettori numerici */
    [data-testid="stSidebar"] [data-testid="stNumberInput"] button {
        background-color: #0a5c60 !important; 
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 4px !important;
        font-weight: bold !important;
        width: 28px !important;
        height: 28px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stNumberInput"] button:hover {
        background-color: white !important;
        color: #0a5c60 !important;
        border-color: white !important;
        transform: scale(1.05);
        transition: all 0.2s;
    }
    
    /* Campo input del numero più grande e meglio centrato */
    [data-testid="stSidebar"] [data-testid="stNumberInput"] input {
        text-align: center !important;
        font-size: 1.1em !important;
        font-weight: 500 !important;
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #0a5c60 !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Miglioramento dei dropdown */
    [data-testid="stSidebar"] .stSelectbox select {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #0a5c60 !important;
        border-radius: 4px !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Miglioramento date input */
    [data-testid="stSidebar"] .stDateInput input {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #0a5c60 !important;
        border-radius: 4px !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        text-align: center !important;
    }
    
    /* Header della sidebar */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        margin-top: 20px !important;
        margin-bottom: 10px !important;
        font-weight: 600 !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding-bottom: 5px !important;
    }
    
    /* Stile calendario */
    .calendar-container table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
    }
    .calendar-container th, 
    .calendar-container td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: center;
    }
    .calendar-container th {
        background-color: #f2f2f2;
        font-weight: bold;
    }
    .calendar-day {
        font-weight: bold;
        font-size: 16px;
        margin-bottom: 4px;
    }
    .price-level {
        font-size: 12px;
    }
    .price-economic {
        background-color: #90EE90;
    }
    .price-medium {
        background-color: #F0E68C;
    }
    .price-high {
        background-color: #F08080;
    }
    .price-unavailable {
        background-color: #D3D3D3;
    }
    .calendar-legend {
        display: flex;
        justify-content: center;
        margin-top: 10px;
        margin-bottom: 30px;
    }
    .legend-item {
        display: flex;
        align-items: center;
        margin-right: 20px;
    }
    .legend-color {
        width: 20px;
        height: 20px;
        margin-right: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Logo nella sidebar
st.sidebar.markdown(
    """
    <div class="sidebar-logo">
        <img src="https://revguardian.altervista.org/images/ratevision_logo.png" alt="Rate Vision Logo">
        <div class="logo-subtitle">Hotel Rate Intelligence</div>
    </div>
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

# Nomi mesi in italiano (fallback se locale non disponibile)
MESI_IT = {
    1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
    5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
    9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
}

def get_nome_mese(data):
    """Restituisce il nome del mese in italiano"""
    return f"{MESI_IT[data.month]} {data.year}"

def process_xotelo_response(response, hotel_name, num_nights=1, adults=2, children_count=0, rooms=1, currency="EUR"):
    if response.get("error") is not None or response.get("result") is None:
        return pd.DataFrame([{
            "hotel": hotel_name,
            "ota": "N/A",
            "ota_code": "N/A",
            "price": 0,
            "price_net": 0,
            "tax": 0,
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
            "price_net": 0,
            "tax": 0,
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
    # Filtriamo Traveloka dai risultati
    for rate in rates:
        if "traveloka" not in rate.get("name", "").lower():  # Escludiamo Traveloka
            rate_net = rate.get("rate", 0)
            tax = rate.get("tax", 0)
            price_per_night = rate_net + tax  # FIX: prezzo comprensivo di tasse come su TripAdvisor
            total_price = price_per_night * num_nights
            
            data.append({
                "hotel": hotel_name,
                "ota": rate.get("name", ""),
                "ota_code": rate.get("code", ""),
                "price": price_per_night,
                "price_net": rate_net,
                "tax": tax,
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
        # Banner informativo per durata soggiorno migliorato
        st.sidebar.markdown(
            f"""
            <div class="info-banner">
                <i class="fas fa-calendar-alt"></i>
                <div class="info-banner-text">
                    Durata soggiorno: <span class="info-banner-value">{num_nights} {'notte' if num_nights == 1 else 'notti'}</span>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
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
    
    # Banner informativo per configurazione migliorato
    st.sidebar.markdown(
        f"""
        <div class="info-banner">
            <i class="fas fa-users"></i>
            <div class="info-banner-text">
                Configurazione: <span class="info-banner-value">{occupancy_summary}</span>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    price_view = st.sidebar.radio(
        "Visualizza prezzi",
        ["Totali", "Per notte"],
        index=0,
        help="Scegli se visualizzare i prezzi totali per tutto il soggiorno o i prezzi per notte"
    )
    
    show_tax_detail = st.sidebar.checkbox(
        "Mostra dettaglio tasse",
        value=False,
        help="Mostra la suddivisione tra tariffa netta e tasse per ogni OTA"
    )
    
    if st.sidebar.button("Cancella dati salvati", key="clear_data"):
        keys_to_clear = ["rate_data", "heatmap_data", "hotel_info", "raw_hotel_data", "raw_api_responses"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.sidebar.success("Dati cancellati con successo.")
        st.rerun()
    
    use_total_price = (price_view == "Totali")
    price_column = "price_total" if use_total_price else "price"
    price_description = f"{'totali per ' + str(num_nights) + ' notti' if use_total_price else 'per notte'}"
    
    if st.sidebar.button("Cerca tariffe", key="search_rates"):
        xotelo_api = XoteloAPI()
        
        with st.spinner(f"Recupero tariffe e dati per {occupancy_summary}..."):
            all_data = []
            all_heatmap_data = []
            all_raw_hotel_data = {}
            
            # Inizializza il dizionario delle risposte API
            if "raw_api_responses" not in st.session_state:
                st.session_state.raw_api_responses = {}
            
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
                    
                    # Salva la risposta grezza per il debug
                    st.session_state.raw_api_responses[f"rates_{hotel}"] = response
                    
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
                    
                    # Salva la risposta grezza per il debug
                    st.session_state.raw_api_responses[f"heatmap_{hotel}"] = heatmap_response
                    
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
                
                # Salva la risposta grezza per il debug
                st.session_state.raw_api_responses["hotel_list"] = hotel_list_response
                
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
                        
                        # Salva la risposta grezza per il debug
                        st.session_state.raw_api_responses[f"hotel_list_{hotel_name}"] = single_hotel_response
                        
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
                    if show_tax_detail:
                        columns_to_show = ["ota", "price_net", "tax", "price", "price_total"]
                        display_df = hotel_df[columns_to_show].sort_values(by=price_column).copy()
                        display_df["price_net"] = display_df["price_net"].apply(lambda x: f"{currency_symbol}{x:.2f}")
                        display_df["tax"] = display_df["tax"].apply(lambda x: f"{currency_symbol}{x:.2f}")
                        display_df["price"] = display_df["price"].apply(lambda x: f"{currency_symbol}{x:.2f}")
                        display_df["price_total"] = display_df["price_total"].apply(lambda x: f"{currency_symbol}{x:.2f}")
                        display_df.columns = ["OTA", f"Tariffa netta ({currency_symbol})", f"Tasse ({currency_symbol})", f"Prezzo per notte ({currency_symbol})", f"Prezzo totale {num_nights} notti ({currency_symbol})"]
                    else:
                        columns_to_show = ["ota", "price", "price_total"]
                        display_df = hotel_df[columns_to_show].sort_values(by=price_column).copy()
                        display_df["price"] = display_df["price"].apply(lambda x: f"{currency_symbol}{x:.2f}")
                        display_df["price_total"] = display_df["price_total"].apply(lambda x: f"{currency_symbol}{x:.2f}")
                        display_df.columns = ["OTA", f"Prezzo per notte ({currency_symbol})", f"Prezzo totale {num_nights} notti ({currency_symbol})"]
                    st.dataframe(display_df, use_container_width=True)
                    
                    st.caption("⚠️ I prezzi possono differire di ±2€ rispetto a TripAdvisor per arrotondamenti dell'API Xotelo.")
                
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
                        st.subheader(f"Calendario Prezzi per {selected_hotel_heatmap}")
                        
                        df_heatmap = hotel_heatmap["data"]
                        df_heatmap["date_str"] = df_heatmap["date"].dt.strftime("%Y-%m-%d")
                        
                        today = datetime.now()
                        start_date = today.replace(day=1)
                        months_to_show = 2
                        
                        for month_idx in range(months_to_show):
                            month_name = get_nome_mese(start_date)
                            st.subheader(month_name)
                            
                            month_start = start_date.replace(day=1)
                            if start_date.month == 12:
                                month_end = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
                            else:
                                month_end = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)
                            
                            # Creiamo dataframe con giorni del mese
                            calendar_days = []
                            for d in range((month_end - month_start).days + 1):
                                current_day = month_start + timedelta(days=d)
                                day_str = current_day.strftime("%Y-%m-%d")
                                # FIX: weekday() già restituisce 0=Lunedì, 6=Domenica (formato ISO)
                                weekday = current_day.weekday()
                                
                                price_level = "Non disponibile"
                                day_matches = df_heatmap[df_heatmap["date_str"] == day_str]
                                if not day_matches.empty:
                                    price_level = day_matches.iloc[0]["price_level"]
                                
                                calendar_days.append({
                                    "date": current_day,
                                    "day": current_day.day,
                                    "weekday": weekday,
                                    "price_level": price_level
                                })
                            
                            calendar_df = pd.DataFrame(calendar_days)
                            
                            # FIX: Calendario con settimana Lun-Dom (0=Lun, 6=Dom)
                            weeks = []
                            current_week = [None] * 7
                            
                            for _, day_row in calendar_df.iterrows():
                                wd = day_row["weekday"]  # 0=Lun, 6=Dom
                                
                                # Se è Lunedì e la settimana corrente ha già dei giorni, salva e crea nuova
                                if wd == 0 and any(d is not None for d in current_week):
                                    weeks.append(current_week)
                                    current_week = [None] * 7
                                
                                current_week[wd] = {
                                    "day": day_row["day"],
                                    "price_level": day_row["price_level"]
                                }
                            
                            # Aggiungi l'ultima settimana
                            if any(d is not None for d in current_week):
                                weeks.append(current_week)
                            
                            # Header: Lun-Dom
                            header = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
                            rows = []
                            
                            for week in weeks:
                                row = []
                                for day in week:
                                    if day is None:
                                        row.append("")
                                    else:
                                        row.append(f"{day['day']}\n{day['price_level']}")
                                rows.append(row)
                            
                            # Creiamo il DataFrame per visualizzare il calendario
                            calendar_display = pd.DataFrame(rows, columns=header)
                            st.dataframe(calendar_display, use_container_width=True)
                            
                            # Legenda
                            legend_cols = st.columns(4)
                            with legend_cols[0]:
                                st.markdown('<div style="display: flex; align-items: center;"><div style="width: 20px; height: 20px; background-color: #90EE90; margin-right: 5px;"></div><span>Economico</span></div>', unsafe_allow_html=True)
                            with legend_cols[1]:
                                st.markdown('<div style="display: flex; align-items: center;"><div style="width: 20px; height: 20px; background-color: #F0E68C; margin-right: 5px;"></div><span>Medio</span></div>', unsafe_allow_html=True)
                            with legend_cols[2]:
                                st.markdown('<div style="display: flex; align-items: center;"><div style="width: 20px; height: 20px; background-color: #F08080; margin-right: 5px;"></div><span>Alto</span></div>', unsafe_allow_html=True)
                            with legend_cols[3]:
                                st.markdown('<div style="display: flex; align-items: center;"><div style="width: 20px; height: 20px; background-color: #D3D3D3; margin-right: 5px;"></div><span>Non disponibile</span></div>', unsafe_allow_html=True)
                            
                            # Prossimo mese
                            if start_date.month == 12:
                                start_date = start_date.replace(year=start_date.year + 1, month=1)
                            else:
                                start_date = start_date.replace(month=start_date.month + 1)
                            
                            st.write("")  # Aggiungi spazio tra i mesi
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
                
                st.subheader("Analisi differenza tariffaria")
                
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
                    
                    st.subheader("Dettaglio analisi differenza tariffaria")
                    
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
            
            st.subheader("Dati grezzi delle chiamate API Xotelo")
            
            # Dati Rates
            with st.expander("Risposte API Rates"):
                if "raw_api_responses" in st.session_state:
                    api_responses = st.session_state.raw_api_responses
                    rate_keys = [k for k in api_responses.keys() if k.startswith("rates_")]
                    
                    for key in rate_keys:
                        st.markdown(f"**{key}**")
                        try:
                            st.json(api_responses[key])
                        except:
                            st.write("Errore nella visualizzazione JSON")
            
            # Dati Heatmap
            with st.expander("Risposte API Heatmap"):
                if "raw_api_responses" in st.session_state:
                    api_responses = st.session_state.raw_api_responses
                    heatmap_keys = [k for k in api_responses.keys() if k.startswith("heatmap_")]
                    
                    for key in heatmap_keys:
                        st.markdown(f"**{key}**")
                        try:
                            st.json(api_responses[key])
                        except:
                            st.write("Errore nella visualizzazione JSON")
            
            # Dati Hotel List
            with st.expander("Risposte API Hotel List"):
                if "raw_api_responses" in st.session_state:
                    api_responses = st.session_state.raw_api_responses
                    hotel_list_keys = [k for k in api_responses.keys() if k.startswith("hotel_list")]
                    
                    for key in hotel_list_keys:
                        st.markdown(f"**{key}**")
                        try:
                            st.json(api_responses[key])
                        except:
                            st.write("Errore nella visualizzazione JSON")
            
            # Analisi OTA
            with st.expander("Analisi OTA"):
                if "rate_data" in st.session_state:
                    df = st.session_state.rate_data
                    
                    # Contiamo gli OTA per hotel
                    st.markdown("### Conteggio OTA per hotel")
                    available_df = df[df["available"]]
                    if not available_df.empty:
                        ota_counts = available_df.groupby("hotel")["ota"].nunique()
                        st.bar_chart(ota_counts)
                        
                        # Mostriamo tutti gli OTA trovati
                        st.markdown("### Tutti gli OTA trovati")
                        all_otas = sorted(available_df["ota"].unique())
                        st.write(", ".join(all_otas))
                        
                        # Verifichiamo se ci sono prezzi diretti dell'hotel
                        direct_prices = available_df[available_df["ota"].str.contains("Official Site|Direct|Hotel Website", case=False, regex=True)]
                        if not direct_prices.empty:
                            st.markdown("### Prezzi diretti dell'hotel trovati")
                            st.dataframe(direct_prices[["hotel", "ota", "price_net", "tax", "price", "price_total"]])
                        else:
                            st.warning("⚠️ Nessun prezzo diretto dell'hotel trovato. Questo potrebbe essere dovuto a:\n"
                                    "1. L'hotel non espone tariffe sul proprio sito web\n"
                                    "2. TripAdvisor non ha accesso alle tariffe dirette dell'hotel\n"
                                    "3. Xotelo API non restituisce le tariffe dirette nelle risposte")
                            
                            # Aggiungiamo un suggerimento per verificare se l'hotel ha un sito ufficiale
                            st.markdown("**Suggerimento**: Verificare se gli hotel hanno un sito ufficiale con booking engine:")
                            for hotel_name in hotel_keys.keys():
                                st.markdown(f"- {hotel_name}")
                        
                        # Statistiche sui range di prezzo
                        st.markdown("### Statistiche sui range di prezzo")
                        price_stats = available_df.groupby("hotel").agg({
                            "price": ["min", "max", "mean", "std"],
                            "ota": "count"
                        })
                        st.dataframe(price_stats)
                    else:
                        st.warning("Nessun dato disponibile per l'analisi OTA")
            
            # Dettagli API
            with st.expander("Dettagli delle richieste API"):
                st.markdown("### Parametri utilizzati nelle richieste API")
                
                if "occupancy" in st.session_state:
                    occupancy = st.session_state.occupancy
                    st.json({
                        "adults": occupancy["adults"],
                        "children": occupancy["children"],
                        "children_ages": occupancy["children_ages"],
                        "rooms": occupancy["rooms"],
                        "currency": st.session_state.get("currency", "EUR"),
                        "nights": st.session_state.get("num_nights", 1),
                        "check_in": check_in_date.strftime("%Y-%m-%d"),
                        "check_out": check_out_date.strftime("%Y-%m-%d")
                    })
                
                st.markdown("### Chiavi hotel configurate:")
                for hotel_name, hotel_key in hotel_keys.items():
                    parts = hotel_key.split("-")
                    location_id = parts[0] if len(parts) > 0 else ""
                    hotel_id = parts[1] if len(parts) > 1 else ""
                    
                    st.write(f"- **{hotel_name}**: `{hotel_key}`")
                    st.write(f"  - Location ID: `{location_id}`")
                    st.write(f"  - Hotel ID: `{hotel_id}`")
                    st.write(f"  - TripAdvisor URL: https://www.tripadvisor.com/Hotel_Review-{hotel_key}")
            
            # Hotel info
            with st.expander("Dati hotel elaborati"):
                if "hotel_info" in st.session_state:
                    st.dataframe(st.session_state.hotel_info)
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
    st.sidebar.info("Versione 0.5.5 - Developed by Alessandro Merella with Xotelo API")

if __name__ == "__main__":
    rate_checker_app()
