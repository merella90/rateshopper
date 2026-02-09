import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
import io
from typing import Dict, List, Optional, Tuple

# ============================================================================
# CONFIGURAZIONE PAGINA
# ============================================================================

st.set_page_config(
    page_title="Rate Checker VOI Alimini PRO",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# STILI CSS MIGLIORATI
# ============================================================================

st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <style>
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0f7378 !important;
        color: white !important;
    }
    
    .sidebar-logo {
        text-align: center;
        padding: 20px 0;
        margin-bottom: 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        background-color: rgba(255, 255, 255, 0.05);
    }
    
    .sidebar-logo img {
        max-width: 80%;
        height: auto;
        filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.2));
        transition: all 0.3s ease;
    }
    
    .sidebar-logo img:hover {
        transform: scale(1.05);
    }
    
    .logo-subtitle {
        color: rgba(255, 255, 255, 0.8);
        font-size: 12px;
        margin-top: 5px;
        font-style: italic;
    }
    
    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    .kpi-card.success {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%);
    }
    
    .kpi-card.warning {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .kpi-card.info {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    .kpi-title {
        font-size: 14px;
        font-weight: 500;
        opacity: 0.9;
        margin-bottom: 5px;
    }
    
    .kpi-value {
        font-size: 32px;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .kpi-delta {
        font-size: 14px;
        opacity: 0.9;
    }
    
    /* Alert boxes */
    .alert-box {
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .alert-box.warning {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        color: #856404;
    }
    
    .alert-box.success {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        color: #155724;
    }
    
    .alert-box.info {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        color: #0c5460;
    }
    
    /* Sidebar elements */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stMultiSelect span[data-baseweb="tag"] {
        background-color: #0a5c60 !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    [data-testid="stSidebar"] button[kind="primary"] {
        background-color: #f5f5f5 !important;
        color: #0a5c60 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        width: 100% !important;
        margin: 8px 0 !important;
    }
    
    [data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: white !important;
        transform: translateY(-1px) !important;
    }
    
    /* Info banners */
    .info-banner {
        background-color: rgba(255, 255, 255, 0.1);
        border-left: 3px solid rgba(255, 255, 255, 0.7);
        padding: 10px 15px;
        margin: 12px 0;
        border-radius: 0 4px 4px 0;
        display: flex;
        align-items: center;
    }
    
    .info-banner i {
        margin-right: 10px;
        color: rgba(255, 255, 255, 0.9);
    }
    
    .info-banner-text {
        font-size: 14px;
        font-weight: 500;
        color: white;
    }
    
    .info-banner-value {
        font-weight: 700;
    }
    
    /* Timestamp */
    .timestamp {
        text-align: right;
        font-size: 12px;
        color: #666;
        font-style: italic;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# CONFIGURAZIONE E COSTANTI
# ============================================================================

HOTEL_KEYS = {
    "VOI Alimini": "g652004-d1799967",
    "Ciaoclub Arco Del Saracino": "g946998-d947000",
    "Hotel Alpiselect Robinson Apulia": "g947837-d949958",
    "Alpiclub Hotel Thalas Club": "g1179328-d1159227"
}

LOCATION_KEY = "g652004"

CURRENCY_SYMBOLS = {
    "EUR": "€", "USD": "$", "GBP": "£", "CAD": "CA$", "CHF": "CHF",
    "AUD": "A$", "JPY": "¥", "CNY": "¥", "INR": "₹", "THB": "฿",
    "BRL": "R$", "HKD": "HK$", "RUB": "₽", "BZD": "BZ$"
}

# ============================================================================
# API CLIENT CLASS
# ============================================================================

class XoteloAPI:
    """Client per le API Xotelo con gestione errori migliorata"""
    
    def __init__(self):
        self.base_url = "https://data.xotelo.com/api"
        self.session = requests.Session()
    
    def _make_request(self, endpoint: str, params: dict) -> dict:
        """Metodo generico per le richieste API"""
        try:
            response = self.session.get(f"{self.base_url}/{endpoint}", params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            return {"error": "Timeout nella richiesta", "timestamp": 0, "result": None}
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "timestamp": 0, "result": None}
        except json.JSONDecodeError:
            return {"error": "Errore nel parsing JSON", "timestamp": 0, "result": None}
    
    def get_rates(self, hotel_key: str, check_in: str, check_out: str, 
                  adults: int = 2, children_ages: Optional[List[int]] = None, 
                  rooms: int = 1, currency: str = "EUR") -> dict:
        """Recupera le tariffe per un hotel"""
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
        
        return self._make_request("rates", params)
    
    def get_heatmap(self, hotel_key: str, check_out: str) -> dict:
        """Recupera i dati heatmap per un hotel"""
        params = {
            "hotel_key": hotel_key,
            "chk_out": check_out
        }
        return self._make_request("heatmap", params)
    
    def get_hotel_list(self, location_key: str, limit: int = 30, 
                       offset: int = 0, sort: str = "best_value") -> dict:
        """Recupera la lista degli hotel per una località"""
        params = {
            "location_key": location_key,
            "limit": limit,
            "offset": offset,
            "sort": sort
        }
        return self._make_request("list", params)

# ============================================================================
# FUNZIONI DI CACHING
# ============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def fetch_rates_cached(hotel_key: str, check_in: str, check_out: str, 
                       adults: int, children_ages_tuple: Optional[tuple], 
                       rooms: int, currency: str) -> dict:
    """Cache delle richieste rates per 5 minuti"""
    api = XoteloAPI()
    children_ages = list(children_ages_tuple) if children_ages_tuple else None
    return api.get_rates(hotel_key, check_in, check_out, adults, children_ages, rooms, currency)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_heatmap_cached(hotel_key: str, check_out: str) -> dict:
    """Cache delle richieste heatmap per 1 ora"""
    api = XoteloAPI()
    return api.get_heatmap(hotel_key, check_out)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_hotel_list_cached(location_key: str, limit: int, sort: str) -> dict:
    """Cache delle richieste hotel list per 1 ora"""
    api = XoteloAPI()
    return api.get_hotel_list(location_key, limit, 0, sort)

# ============================================================================
# FUNZIONI DI PROCESSING DATI
# ============================================================================

def process_xotelo_response(response: dict, hotel_name: str, num_nights: int = 1,
                           adults: int = 2, children_count: int = 0, 
                           rooms: int = 1, currency: str = "EUR") -> pd.DataFrame:
    """Processa la risposta API in DataFrame"""
    
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
        if "traveloka" not in rate.get("name", "").lower():
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
    
    return pd.DataFrame(data) if data else pd.DataFrame()

def process_heatmap_response(response: dict, hotel_name: str) -> Optional[dict]:
    """Processa i dati heatmap"""
    
    if response.get("error") is not None or response.get("result") is None:
        return None
    
    heatmap_data = response.get("result", {}).get("heatmap", {})
    
    if not heatmap_data:
        return None
    
    average_days = heatmap_data.get("average_price_days", [])
    cheap_days = heatmap_data.get("cheap_price_days", [])
    high_days = heatmap_data.get("high_price_days", [])
    
    all_dates = []
    
    for date_str in cheap_days:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            all_dates.append({
                "hotel": hotel_name,
                "date": date,
                "price_level": "Economico",
                "level_value": 1
            })
        except:
            continue
    
    for date_str in average_days:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            all_dates.append({
                "hotel": hotel_name,
                "date": date,
                "price_level": "Medio",
                "level_value": 2
            })
        except:
            continue
    
    for date_str in high_days:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            all_dates.append({
                "hotel": hotel_name,
                "date": date,
                "price_level": "Alto",
                "level_value": 3
            })
        except:
            continue
    
    if all_dates:
        df = pd.DataFrame(all_dates)
        return {
            "hotel": hotel_name,
            "timestamp": response.get("timestamp", 0),
            "check_out": response.get("result", {}).get("chk_out", ""),
            "data": df
        }
    
    return None

def process_hotel_list_response(response: dict) -> Optional[pd.DataFrame]:
    """Processa la lista hotel"""
    
    if response.get("error") is not None or response.get("result") is None:
        return None
    
    hotels_list = response.get("result", {}).get("list", [])
    
    if not hotels_list:
        return None
    
    data = []
    for hotel in hotels_list:
        try:
            review_summary = hotel.get("review_summary", {}) or {}
            price_ranges = hotel.get("price_ranges", {}) or {}
            geo = hotel.get("geo", {}) or {}
            amenities = hotel.get("highlighted_amenities", []) or []
            
            data.append({
                "hotel_key": hotel.get("key", ""),
                "name": hotel.get("name", ""),
                "accommodation_type": hotel.get("accommodation_type", ""),
                "url": hotel.get("url", ""),
                "rating": review_summary.get("rating", 0) if isinstance(review_summary, dict) else 0,
                "review_count": review_summary.get("count", 0) if isinstance(review_summary, dict) else 0,
                "min_price": price_ranges.get("minimum", 0) if isinstance(price_ranges, dict) else 0,
                "max_price": price_ranges.get("maximum", 0) if isinstance(price_ranges, dict) else 0,
                "latitude": geo.get("latitude", 0) if isinstance(geo, dict) else 0,
                "longitude": geo.get("longitude", 0) if isinstance(geo, dict) else 0,
                "amenities": ", ".join([a.get("name", "") for a in amenities if isinstance(a, dict)])
            })
        except:
            continue
    
    return pd.DataFrame(data) if data else None

# ============================================================================
# FUNZIONI DI VISUALIZZAZIONE
# ============================================================================

def create_kpi_dashboard(df: pd.DataFrame, currency_symbol: str) -> None:
    """Crea dashboard KPI principale"""
    
    available_df = df[df["available"]]
    
    if available_df.empty:
        st.warning("Nessun dato disponibile per mostrare i KPI")
        return
    
    st.markdown("### 📊 Dashboard KPI")
    
    voi_data = available_df[available_df["hotel"] == "VOI Alimini"]
    
    if voi_data.empty:
        st.info("Dati VOI Alimini non disponibili per i KPI")
        return
    
    voi_min_price = voi_data["price"].min()
    voi_ota_count = len(voi_data["ota"].unique())
    
    # Calcola statistiche competitive
    all_min_prices = available_df.groupby("hotel")["price"].min().sort_values()
    voi_position = (all_min_prices <= voi_min_price).sum()
    total_hotels = len(all_min_prices)
    
    competitors = all_min_prices[all_min_prices.index != "VOI Alimini"]
    market_avg = all_min_prices.mean()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Posizione Mercato",
            f"{voi_position}° / {total_hotels}",
            delta=f"{currency_symbol}{voi_min_price:.0f}",
            help="Posizione di VOI Alimini rispetto ai competitor"
        )
    
    with col2:
        if not competitors.empty:
            closest_competitor = competitors.iloc[(competitors - voi_min_price).abs().argsort()[0]]
            price_diff = voi_min_price - closest_competitor
            perc_diff = (price_diff / closest_competitor * 100)
            
            st.metric(
                "Gap vs Competitor",
                f"{currency_symbol}{abs(price_diff):.0f}",
                delta=f"{perc_diff:+.1f}%",
                delta_color="inverse",
                help="Differenza rispetto al competitor più vicino"
            )
    
    with col3:
        market_diff = ((voi_min_price - market_avg) / market_avg * 100)
        st.metric(
            "vs Media Mercato",
            f"{currency_symbol}{market_avg:.0f}",
            delta=f"{market_diff:+.1f}%",
            delta_color="inverse",
            help="Posizione rispetto alla media del mercato"
        )
    
    with col4:
        st.metric(
            "OTA Disponibili",
            voi_ota_count,
            delta="Live",
            help="Numero di OTA che distribuiscono l'hotel"
        )

def create_price_positioning_chart(df: pd.DataFrame, currency_symbol: str) -> go.Figure:
    """Crea grafico di price positioning"""
    
    available_df = df[df["available"]]
    
    hotel_stats = available_df.groupby("hotel").agg({
        "price": ["min", "max", "mean"],
        "ota": "count"
    }).reset_index()
    
    hotel_stats.columns = ["hotel", "min_price", "max_price", "avg_price", "ota_count"]
    
    # Ordina per prezzo minimo
    hotel_stats = hotel_stats.sort_values("min_price")
    
    fig = go.Figure()
    
    colors = ['#0f7378' if hotel == 'VOI Alimini' else '#a0c4c7' for hotel in hotel_stats["hotel"]]
    
    # Range bars
    for idx, row in hotel_stats.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["min_price"], row["max_price"]],
            y=[row["hotel"], row["hotel"]],
            mode="lines",
            line=dict(width=15, color=colors[idx]),
            showlegend=False,
            hoverinfo="skip"
        ))
        
        # Marker per prezzo medio
        fig.add_trace(go.Scatter(
            x=[row["avg_price"]],
            y=[row["hotel"]],
            mode="markers",
            marker=dict(
                size=14,
                color="white",
                symbol="diamond",
                line=dict(width=2, color=colors[idx])
            ),
            name="Prezzo medio" if idx == 0 else "",
            showlegend=(idx == 0),
            hovertemplate=f"<b>{row['hotel']}</b><br>" +
                         f"Min: {currency_symbol}{row['min_price']:.2f}<br>" +
                         f"Avg: {currency_symbol}{row['avg_price']:.2f}<br>" +
                         f"Max: {currency_symbol}{row['max_price']:.2f}<br>" +
                         f"OTA: {int(row['ota_count'])}<extra></extra>"
        ))
    
    fig.update_layout(
        title="Price Positioning - Range e Media Prezzi",
        xaxis_title=f"Prezzo per notte ({currency_symbol})",
        yaxis_title="",
        height=400,
        showlegend=True,
        hovermode="closest"
    )
    
    return fig

def create_price_calendar_heatmap(df_heatmap: pd.DataFrame, hotel_name: str) -> go.Figure:
    """Crea heatmap calendario prezzi migliorata"""
    
    df = df_heatmap.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["day_of_week"] = df["date"].dt.day_name()
    df["week_of_year"] = df["date"].dt.isocalendar().week
    df["day"] = df["date"].dt.day
    df["month"] = df["date"].dt.strftime("%B")
    
    # Pivot per heatmap
    pivot_df = df.pivot_table(
        index="week_of_year",
        columns="day_of_week",
        values="level_value",
        aggfunc="first"
    )
    
    # Ordina giorni della settimana
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot_df = pivot_df.reindex(columns=day_order)
    
    # Custom data per hover
    hover_data = df.pivot_table(
        index="week_of_year",
        columns="day_of_week",
        values="date",
        aggfunc="first"
    )
    hover_data = hover_data.reindex(columns=day_order)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"],
        y=pivot_df.index,
        customdata=hover_data.values,
        hovertemplate="<b>%{customdata|%d/%m/%Y}</b><br>Settimana: %{y}<extra></extra>",
        colorscale=[
            [0, "#D3D3D3"],    # Non disponibile
            [0.33, "#90EE90"],  # Economico
            [0.66, "#F0E68C"],  # Medio
            [1, "#F08080"]      # Alto
        ],
        showscale=False
    ))
    
    fig.update_layout(
        title=f"Calendario Prezzi - {hotel_name}",
        xaxis_title="Giorno della settimana",
        yaxis_title="Settimana dell'anno",
        height=500
    )
    
    return fig

def check_price_alerts(df: pd.DataFrame, currency_symbol: str) -> List[dict]:
    """Controlla e genera alerts intelligenti"""
    
    alerts = []
    available_df = df[df["available"]]
    
    if available_df.empty:
        return alerts
    
    voi_data = available_df[available_df["hotel"] == "VOI Alimini"]
    
    if voi_data.empty:
        return alerts
    
    voi_min = voi_data["price"].min()
    voi_max = voi_data["price"].max()
    voi_ota_count = len(voi_data["ota"].unique())
    
    all_min_prices = available_df.groupby("hotel")["price"].min()
    competitors = all_min_prices[all_min_prices.index != "VOI Alimini"]
    
    if competitors.empty:
        return alerts
    
    market_min = competitors.min()
    market_max = competitors.max()
    market_avg = competitors.mean()
    
    # Alert 1: Prezzo troppo alto
    if voi_min > market_avg * 1.1:
        diff_perc = ((voi_min - market_avg) / market_avg * 100)
        alerts.append({
            "type": "warning",
            "icon": "⚠️",
            "message": f"Il prezzo VOI Alimini ({currency_symbol}{voi_min:.0f}) è del {diff_perc:.1f}% superiore alla media di mercato ({currency_symbol}{market_avg:.0f})"
        })
    
    # Alert 2: Posizione competitiva forte
    elif voi_min <= np.percentile(list(competitors.values), 25):
        alerts.append({
            "type": "success",
            "icon": "✅",
            "message": f"Ottima posizione! VOI Alimini è nel 25% più competitivo del mercato con {currency_symbol}{voi_min:.0f}"
        })
    
    # Alert 3: Parity con competitor
    closest_diff = min(abs(competitors - voi_min))
    if closest_diff < voi_min * 0.02:  # Differenza < 2%
        alerts.append({
            "type": "info",
            "icon": "ℹ️",
            "message": f"Price parity raggiunto con il competitor più vicino (differenza < 2%)"
        })
    
    # Alert 4: Poche OTA
    if voi_ota_count < 5:
        alerts.append({
            "type": "warning",
            "icon": "📢",
            "message": f"Solo {voi_ota_count} OTA distribuiscono l'hotel. Considera di espandere la distribuzione."
        })
    
    # Alert 5: Buona distribuzione
    elif voi_ota_count >= 8:
        alerts.append({
            "type": "success",
            "icon": "🎯",
            "message": f"Eccellente copertura distributiva con {voi_ota_count} OTA attive"
        })
    
    # Alert 6: Spread prezzi elevato
    if voi_ota_count > 1:
        price_spread = ((voi_max - voi_min) / voi_min * 100)
        if price_spread > 15:
            alerts.append({
                "type": "warning",
                "icon": "📊",
                "message": f"Spread prezzi elevato ({price_spread:.1f}%) tra le OTA. Range: {currency_symbol}{voi_min:.0f} - {currency_symbol}{voi_max:.0f}"
            })
    
    return alerts

def show_alerts(alerts: List[dict]) -> None:
    """Mostra gli alerts con styling appropriato"""
    
    if not alerts:
        return
    
    st.markdown("### 🔔 Alerts e Raccomandazioni")
    
    for alert in alerts:
        alert_type = alert["type"]
        icon = alert.get("icon", "")
        message = alert["message"]
        
        alert_html = f"""
        <div class="alert-box {alert_type}">
            <span style="font-size: 20px;">{icon}</span>
            <span>{message}</span>
        </div>
        """
        st.markdown(alert_html, unsafe_allow_html=True)

# ============================================================================
# FUNZIONI DI EXPORT
# ============================================================================

def export_to_excel(df: pd.DataFrame, filename: str = "rate_comparison.xlsx") -> bytes:
    """Esporta dati in Excel con formattazione professionale"""
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Dati completi
        df.to_excel(writer, sheet_name='Dati Completi', index=False)
        
        # Sheet 2: Summary per hotel
        available_df = df[df["available"]]
        if not available_df.empty:
            summary = available_df.groupby("hotel").agg({
                "price": ["min", "max", "mean"],
                "ota": "count"
            }).reset_index()
            summary.columns = ["Hotel", "Prezzo Min", "Prezzo Max", "Prezzo Medio", "Numero OTA"]
            summary.to_excel(writer, sheet_name='Summary Hotel', index=False)
        
        # Sheet 3: Best rates per hotel
        if not available_df.empty:
            best_rates = []
            for hotel in available_df["hotel"].unique():
                hotel_data = available_df[available_df["hotel"] == hotel]
                min_idx = hotel_data["price"].idxmin()
                best_rate = hotel_data.loc[min_idx]
                best_rates.append({
                    "Hotel": hotel,
                    "OTA": best_rate["ota"],
                    "Prezzo per notte": best_rate["price"],
                    "Prezzo totale": best_rate["price_total"],
                    "Check-in": best_rate["check_in"],
                    "Check-out": best_rate["check_out"]
                })
            
            best_rates_df = pd.DataFrame(best_rates)
            best_rates_df.to_excel(writer, sheet_name='Best Rates', index=False)
        
        # Formattazione
        workbook = writer.book
        
        for sheet_name in workbook.sheetnames:
            worksheet = workbook[sheet_name]
            
            # Auto-width colonne
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Header bold
            for cell in worksheet[1]:
                cell.font = cell.font.copy(bold=True)
    
    output.seek(0)
    return output.getvalue()

# ============================================================================
# APPLICAZIONE PRINCIPALE
# ============================================================================

def main():
    """Funzione principale dell'applicazione"""
    
    # Logo nella sidebar
    st.sidebar.markdown("""
        <div class="sidebar-logo">
            <img src="https://revguardian.altervista.org/images/ratevision_logo.png" alt="Rate Vision Logo">
            <div class="logo-subtitle">Hotel Rate Intelligence PRO</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Titolo principale
    st.title("📊 Rate Checker VOI Alimini PRO")
    st.markdown("*Sistema avanzato di monitoraggio e analisi tariffaria competitiva*")
    
    # Inizializza session state
    if "currency" not in st.session_state:
        st.session_state.currency = "EUR"
    if "last_update" not in st.session_state:
        st.session_state.last_update = None
    
    # ========================================================================
    # SIDEBAR - PARAMETRI DI RICERCA
    # ========================================================================
    
    st.sidebar.header("🔍 Parametri di ricerca")
    
    # Valuta
    currency = st.sidebar.selectbox(
        "Valuta",
        list(CURRENCY_SYMBOLS.keys()),
        index=0
    )
    currency_symbol = CURRENCY_SYMBOLS[currency]
    
    # Selezione hotel
    competitors = list(HOTEL_KEYS.keys())
    selected_hotels = st.sidebar.multiselect(
        "Hotel da confrontare",
        competitors,
        default=competitors
    )
    
    # Date
    st.sidebar.subheader("📅 Periodo")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        check_in_date = st.date_input("Check-in", datetime.now())
    with col2:
        check_out_date = st.date_input("Check-out", datetime.now() + timedelta(days=7))
    
    num_nights = (check_out_date - check_in_date).days
    
    if num_nights <= 0:
        st.sidebar.error("⚠️ La data di check-out deve essere successiva alla data di check-in!")
        num_nights = 1
    else:
        st.sidebar.markdown(
            f"""
            <div class="info-banner">
                <i class="fas fa-calendar-alt"></i>
                <div class="info-banner-text">
                    Soggiorno: <span class="info-banner-value">{num_nights} {'notte' if num_nights == 1 else 'notti'}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Occupazione
    st.sidebar.subheader("👥 Occupazione")
    
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
    
    st.sidebar.markdown(
        f"""
        <div class="info-banner">
            <i class="fas fa-users"></i>
            <div class="info-banner-text">
                <span class="info-banner-value">{occupancy_summary}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Visualizzazione prezzi
    price_view = st.sidebar.radio(
        "Visualizza prezzi",
        ["Per notte", "Totali"],
        index=0,
        help="Scegli se visualizzare i prezzi per notte o totali per il soggiorno"
    )
    
    # Pulsanti azione
    st.sidebar.markdown("---")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        search_button = st.button("🔍 Cerca tariffe", type="primary", use_container_width=True)
    
    with col2:
        if st.button("🗑️ Cancella cache", use_container_width=True):
            st.cache_data.clear()
            for key in ["rate_data", "heatmap_data", "hotel_info", "raw_api_responses"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.sidebar.success("✅ Cache cancellata!")
            st.rerun()
    
    # Timestamp ultimo aggiornamento
    if st.session_state.last_update:
        st.sidebar.markdown(
            f'<div class="timestamp">Ultimo aggiornamento: {st.session_state.last_update}</div>',
            unsafe_allow_html=True
        )
    
    # ========================================================================
    # RICERCA TARIFFE
    # ========================================================================
    
    use_total_price = (price_view == "Totali")
    price_column = "price_total" if use_total_price else "price"
    price_description = f"{'totali' if use_total_price else 'per notte'}"
    
    if search_button:
        if not selected_hotels:
            st.error("⚠️ Seleziona almeno un hotel da confrontare!")
            return
        
        with st.spinner(f"🔄 Recupero dati per {len(selected_hotels)} hotel..."):
            all_data = []
            all_heatmap_data = []
            
            if "raw_api_responses" not in st.session_state:
                st.session_state.raw_api_responses = {}
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Recupero rates
            for i, hotel in enumerate(selected_hotels):
                progress = int(50 * i / len(selected_hotels))
                progress_bar.progress(progress)
                status_text.text(f"📊 Elaborazione tariffe per {hotel}... ({i+1}/{len(selected_hotels)})")
                
                hotel_key = HOTEL_KEYS.get(hotel, "")
                if hotel_key:
                    # Converti in tupla per il caching
                    children_ages_tuple = tuple(children_ages) if has_children else None
                    
                    response = fetch_rates_cached(
                        hotel_key,
                        check_in_date.strftime("%Y-%m-%d"),
                        check_out_date.strftime("%Y-%m-%d"),
                        num_adults,
                        children_ages_tuple,
                        num_rooms,
                        currency
                    )
                    
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
                    
                    if not df.empty:
                        all_data.append(df)
            
            # Recupero heatmap
            for i, hotel in enumerate(selected_hotels):
                progress = int(50 + 30 * i / len(selected_hotels))
                progress_bar.progress(progress)
                status_text.text(f"📅 Elaborazione calendario per {hotel}... ({i+1}/{len(selected_hotels)})")
                
                hotel_key = HOTEL_KEYS.get(hotel, "")
                if hotel_key:
                    heatmap_response = fetch_heatmap_cached(
                        hotel_key,
                        check_out_date.strftime("%Y-%m-%d")
                    )
                    
                    st.session_state.raw_api_responses[f"heatmap_{hotel}"] = heatmap_response
                    
                    heatmap_data = process_heatmap_response(heatmap_response, hotel)
                    if heatmap_data:
                        all_heatmap_data.append(heatmap_data)
            
            # Recupero info hotel
            progress_bar.progress(80)
            status_text.text("🏨 Recupero rating e informazioni hotel...")
            
            try:
                hotel_list_response = fetch_hotel_list_cached(LOCATION_KEY, 100, "best_value")
                st.session_state.raw_api_responses["hotel_list"] = hotel_list_response
                
                hotel_info_df = process_hotel_list_response(hotel_list_response)
                
                if hotel_info_df is not None:
                    hotel_key_to_name = {v: k for k, v in HOTEL_KEYS.items()}
                    hotel_info_df["our_hotel_name"] = hotel_info_df["hotel_key"].apply(
                        lambda x: hotel_key_to_name.get(x, "")
                    )
                    filtered_hotel_info = hotel_info_df[hotel_info_df["our_hotel_name"] != ""].copy()
                    
                    if not filtered_hotel_info.empty:
                        st.session_state.hotel_info = filtered_hotel_info
            
            except Exception as e:
                st.warning(f"⚠️ Impossibile recuperare le informazioni hotel: {str(e)}")
            
            progress_bar.progress(100)
            status_text.text("✅ Elaborazione completata!")
            
            # Salva dati
            if all_data:
                combined_df = pd.concat(all_data, ignore_index=True)
                st.session_state.rate_data = combined_df
                st.session_state.currency = currency
                st.session_state.num_nights = num_nights
                st.session_state.occupancy = {
                    "adults": num_adults,
                    "children": len(children_ages) if has_children else 0,
                    "children_ages": children_ages if has_children else [],
                    "rooms": num_rooms
                }
                st.session_state.last_update = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                if all_heatmap_data:
                    st.session_state.heatmap_data = all_heatmap_data
                
                available_hotels = combined_df[combined_df["available"]]["hotel"].unique()
                unavailable_hotels = combined_df[~combined_df["available"]]["hotel"].unique()
                
                if len(unavailable_hotels) > 0:
                    st.warning(f"⚠️ Hotel non disponibili: {', '.join(unavailable_hotels)}")
                
                st.success(f"✅ Dati recuperati con successo per {len(available_hotels)} hotel!")
                st.rerun()
            else:
                st.error("❌ Nessun dato recuperato. Verifica le chiavi degli hotel e riprova.")
    
    # ========================================================================
    # VISUALIZZAZIONE DATI
    # ========================================================================
    
    if "rate_data" in st.session_state:
        df = st.session_state.rate_data
        current_currency = st.session_state.currency
        
        saved_occupancy = st.session_state.get("occupancy", {
            "adults": 2,
            "children": 0,
            "children_ages": [],
            "rooms": 1
        })
        
        # Info occupazione
        st.info(
            f"💡 Prezzi per: {saved_occupancy['adults']} adulti"
            f"{', ' + str(saved_occupancy['children']) + ' bambini' if saved_occupancy['children'] > 0 else ''}"
            f" in {saved_occupancy['rooms']} {'camera' if saved_occupancy['rooms'] == 1 else 'camere'}"
        )
        
        # Warning se parametri sono cambiati
        current_occupancy_different = (
            num_adults != saved_occupancy['adults'] or
            (len(children_ages) if has_children else 0) != saved_occupancy['children'] or
            num_rooms != saved_occupancy['rooms']
        )
        
        if current_occupancy_different:
            st.warning(
                "⚠️ L'occupazione selezionata è diversa da quella usata per cercare i prezzi. "
                "Clicca 'Cerca tariffe' per aggiornare i dati."
            )
        
        if current_currency != currency:
            st.warning(
                f"⚠️ La valuta selezionata ({currency}) è diversa da quella nei dati ({current_currency}). "
                "Clicca 'Cerca tariffe' per aggiornare."
            )
        
        # KPI Dashboard
        create_kpi_dashboard(df, currency_symbol)
        
        # Alerts
        alerts = check_price_alerts(df, currency_symbol)
        if alerts:
            show_alerts(alerts)
        
        st.markdown("---")
        
        # ====================================================================
        # TABS
        # ====================================================================
        
        tabs = st.tabs([
            "📊 Analisi Comparativa",
            "💰 Confronto OTA",
            "📅 Calendari Prezzi",
            "⭐ Rating e Qualità",
            "🔧 Debug"
        ])
        
        # TAB 1: ANALISI COMPARATIVA
        with tabs[0]:
            st.header("Analisi Comparativa Hotel")
            
            available_df = df[df["available"]]
            
            if not available_df.empty:
                # Price Positioning Chart
                st.plotly_chart(
                    create_price_positioning_chart(available_df, currency_symbol),
                    use_container_width=True
                )
                
                # Confronto prezzi minimi
                st.subheader("Confronto Prezzi Minimi")
                
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
                
                min_prices_df = pd.DataFrame(min_prices_data).sort_values("min_price")
                
                fig = px.bar(
                    min_prices_df,
                    x="hotel",
                    y="min_price",
                    title=f"Prezzi Minimi per Hotel ({price_description})",
                    color="hotel",
                    labels={"min_price": f"Prezzo {price_description} ({currency_symbol})", "hotel": "Hotel"},
                    color_discrete_map={"VOI Alimini": "#0f7378"}
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
                
                # Tabella riepilogativa
                st.subheader("Riepilogo Competitivo")
                
                display_min_prices = min_prices_df.copy()
                display_min_prices["min_price"] = display_min_prices["min_price"].apply(
                    lambda x: f"{currency_symbol}{x:.2f}"
                )
                display_min_prices.columns = ["Hotel", "Prezzo Minimo", "Migliore OTA", "N° OTA"]
                
                st.dataframe(display_min_prices, use_container_width=True, hide_index=True)
                
                # Export Excel
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    if st.button("📥 Esporta in Excel", use_container_width=True):
                        excel_data = export_to_excel(df)
                        st.download_button(
                            label="💾 Download Excel",
                            data=excel_data,
                            file_name=f"rate_comparison_{check_in_date.strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                
                # Analisi differenza tariffaria
                st.subheader("Analisi Differenza Tariffaria vs VOI Alimini")
                
                reference_hotel = "VOI Alimini"
                ref_data = available_df[available_df["hotel"] == reference_hotel]
                
                if not ref_data.empty:
                    ref_min_price = ref_data[price_column].min()
                    
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
                    
                    if parity_data:
                        parity_df = pd.DataFrame(parity_data)
                        
                        fig = px.bar(
                            parity_df,
                            x="hotel",
                            y="perc_diff",
                            title=f"Differenza Percentuale rispetto a {reference_hotel}",
                            labels={"perc_diff": "Differenza (%)", "hotel": "Hotel"},
                            color="perc_diff",
                            color_continuous_scale="RdYlGn_r"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
            
            else:
                st.warning("⚠️ Nessun hotel disponibile per le date selezionate.")
        
        # TAB 2: CONFRONTO OTA
        with tabs[1]:
            st.header("Confronto Tariffe OTA")
            
            available_df = df[df["available"]]
            
            if not available_df.empty:
                available_hotels = available_df["hotel"].unique()
                
                selected_hotel = st.selectbox(
                    "Seleziona hotel da analizzare",
                    available_hotels,
                    index=0 if "VOI Alimini" not in available_hotels else list(available_hotels).index("VOI Alimini")
                )
                
                hotel_df = available_df[available_df["hotel"] == selected_hotel]
                
                if not hotel_df.empty:
                    ota_count = len(hotel_df["ota"].unique())
                    st.info(f"📊 Trovate **{ota_count} OTA** per {selected_hotel}")
                    
                    # Grafico tariffe OTA
                    fig = px.bar(
                        hotel_df.sort_values(price_column),
                        x="ota",
                        y=price_column,
                        title=f"Tariffe per {selected_hotel} ({price_description})",
                        color=price_column,
                        labels={price_column: f"Prezzo ({currency_symbol})", "ota": "OTA"},
                        color_continuous_scale="RdYlGn_r"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Metriche
                    col1, col2, col3, col4 = st.columns(4)
                    
                    min_price = hotel_df[price_column].min()
                    max_price = hotel_df[price_column].max()
                    avg_price = hotel_df[price_column].mean()
                    price_range = max_price - min_price
                    
                    min_ota = hotel_df.loc[hotel_df[price_column].idxmin(), "ota"]
                    max_ota = hotel_df.loc[hotel_df[price_column].idxmax(), "ota"]
                    
                    with col1:
                        st.metric("Prezzo Minimo", f"{currency_symbol}{min_price:.2f}", f"via {min_ota}")
                    
                    with col2:
                        st.metric("Prezzo Massimo", f"{currency_symbol}{max_price:.2f}", f"via {max_ota}")
                    
                    with col3:
                        st.metric("Prezzo Medio", f"{currency_symbol}{avg_price:.2f}")
                    
                    with col4:
                        spread_perc = (price_range / min_price * 100) if min_price > 0 else 0
                        st.metric("Spread", f"{currency_symbol}{price_range:.2f}", f"{spread_perc:.1f}%")
                    
                    # Dettaglio tabella
                    st.subheader("Dettaglio Tariffe OTA")
                    
                    display_df = hotel_df[["ota", "price", "price_total"]].sort_values(price_column).copy()
                    display_df["price"] = display_df["price"].apply(lambda x: f"{currency_symbol}{x:.2f}")
                    display_df["price_total"] = display_df["price_total"].apply(lambda x: f"{currency_symbol}{x:.2f}")
                    display_df.columns = ["OTA", "Prezzo/notte", f"Prezzo {num_nights} notti"]
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Lista OTA per tutti gli hotel
                st.subheader("OTA Disponibili per Hotel")
                
                for hotel in available_df["hotel"].unique():
                    hotel_data = available_df[available_df["hotel"] == hotel]
                    otas = sorted(hotel_data["ota"].unique())
                    
                    with st.expander(f"{hotel} - {len(otas)} OTA"):
                        st.write(", ".join(otas))
        
        # TAB 3: CALENDARI PREZZI
        with tabs[2]:
            st.header("Calendari Prezzi - Heatmap")
            
            if "heatmap_data" in st.session_state and st.session_state.heatmap_data:
                heatmap_data = st.session_state.heatmap_data
                available_hotels_heatmap = [data["hotel"] for data in heatmap_data]
                
                if available_hotels_heatmap:
                    selected_hotel_heatmap = st.selectbox(
                        "Seleziona hotel",
                        available_hotels_heatmap,
                        key="heatmap_selector",
                        index=0 if "VOI Alimini" not in available_hotels_heatmap 
                        else available_hotels_heatmap.index("VOI Alimini")
                    )
                    
                    hotel_heatmap = next(
                        (h for h in heatmap_data if h["hotel"] == selected_hotel_heatmap),
                        None
                    )
                    
                    if hotel_heatmap:
                        df_heatmap = hotel_heatmap["data"]
                        
                        # Heatmap calendar
                        fig = create_price_calendar_heatmap(df_heatmap, selected_hotel_heatmap)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Legenda
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.markdown(
                                '<div style="display: flex; align-items: center;">'
                                '<div style="width: 20px; height: 20px; background-color: #90EE90; margin-right: 5px;"></div>'
                                '<span>Economico</span></div>',
                                unsafe_allow_html=True
                            )
                        
                        with col2:
                            st.markdown(
                                '<div style="display: flex; align-items: center;">'
                                '<div style="width: 20px; height: 20px; background-color: #F0E68C; margin-right: 5px;"></div>'
                                '<span>Medio</span></div>',
                                unsafe_allow_html=True
                            )
                        
                        with col3:
                            st.markdown(
                                '<div style="display: flex; align-items: center;">'
                                '<div style="width: 20px; height: 20px; background-color: #F08080; margin-right: 5px;"></div>'
                                '<span>Alto</span></div>',
                                unsafe_allow_html=True
                            )
                        
                        with col4:
                            st.markdown(
                                '<div style="display: flex; align-items: center;">'
                                '<div style="width: 20px; height: 20px; background-color: #D3D3D3; margin-right: 5px;"></div>'
                                '<span>Non disponibile</span></div>',
                                unsafe_allow_html=True
                            )
                        
                        # Statistiche calendario
                        st.subheader("Statistiche Calendario")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        economico_count = len(df_heatmap[df_heatmap["price_level"] == "Economico"])
                        medio_count = len(df_heatmap[df_heatmap["price_level"] == "Medio"])
                        alto_count = len(df_heatmap[df_heatmap["price_level"] == "Alto"])
                        
                        with col1:
                            st.metric("Giorni Economici", economico_count)
                        
                        with col2:
                            st.metric("Giorni Medi", medio_count)
                        
                        with col3:
                            st.metric("Giorni Alti", alto_count)
            
            else:
                st.info("💡 Effettua una ricerca tariffe per visualizzare i calendari prezzi")
        
        # TAB 4: RATING E QUALITÀ
        with tabs[3]:
            st.header("Rating e Qualità Hotel")
            
            if "hotel_info" in st.session_state and not st.session_state.hotel_info.empty:
                hotel_info_df = st.session_state.hotel_info
                
                # Confronto Rating e Prezzi
                st.subheader("Confronto Rating e Prezzi")
                
                rating_comparison = []
                for hotel_name in HOTEL_KEYS.keys():
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
                        rating = f"{rating_value:.1f}/5.0"
                    
                    price_display = f"{currency_symbol}{min_price:.2f}" if min_price is not None else "N/A"
                    
                    rating_comparison.append({
                        "Hotel": hotel_name,
                        "Rating": rating,
                        "Recensioni": review_count,
                        "Prezzo Minimo": price_display
                    })
                
                comparison_df = pd.DataFrame(rating_comparison)
                st.dataframe(comparison_df, use_container_width=True, hide_index=True)
                
                # Rating chart
                rating_data = []
                
                for _, row in hotel_info_df.iterrows():
                    hotel_name = row["our_hotel_name"]
                    if hotel_name and row["rating"] > 0:
                        min_price = None
                        
                        if hotel_name in available_df["hotel"].unique():
                            hotel_data = available_df[available_df["hotel"] == hotel_name]
                            min_price = hotel_data[price_column].min()
                        
                        if min_price is not None:
                            rating_data.append({
                                "hotel": hotel_name,
                                "rating": row["rating"],
                                "review_count": row["review_count"],
                                "min_price": min_price
                            })
                
                if rating_data:
                    rating_df = pd.DataFrame(rating_data)
                    
                    # Bar chart rating
                    fig = px.bar(
                        rating_df,
                        x="hotel",
                        y="rating",
                        title="Rating TripAdvisor",
                        color="rating",
                        color_continuous_scale="Viridis",
                        labels={"rating": "Punteggio (1-5)", "hotel": "Hotel"},
                        text="rating"
                    )
                    
                    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
                    fig.update_layout(yaxis_range=[0, 5.5])
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Quality/Price Ratio
                    st.subheader("Rapporto Qualità/Prezzo")
                    
                    rating_df["quality_price_ratio"] = rating_df["rating"] / rating_df["min_price"] * 100
                    rating_df_sorted = rating_df.sort_values("quality_price_ratio", ascending=False)
                    
                    qp_fig = px.bar(
                        rating_df_sorted,
                        x="hotel",
                        y="quality_price_ratio",
                        title="Indice Qualità/Prezzo (Rating/Prezzo × 100)",
                        color="quality_price_ratio",
                        color_continuous_scale="RdYlGn",
                        labels={"quality_price_ratio": "Indice Q/P", "hotel": "Hotel"}
                    )
                    
                    st.plotly_chart(qp_fig, use_container_width=True)
                    
                    # Scatter: Prezzo vs Rating
                    scatter_fig = px.scatter(
                        rating_df,
                        x="min_price",
                        y="rating",
                        color="hotel",
                        size="review_count",
                        hover_name="hotel",
                        labels={
                            "min_price": f"Prezzo {price_description} ({currency_symbol})",
                            "rating": "Rating (1-5)",
                            "review_count": "Recensioni"
                        },
                        title="Analisi Prezzo vs Rating"
                    )
                    
                    st.plotly_chart(scatter_fig, use_container_width=True)
            
            else:
                st.info("💡 Effettua una ricerca tariffe per visualizzare i rating")
        
        # TAB 5: DEBUG
        with tabs[4]:
            st.header("Debug e Informazioni Tecniche")
            
            # API Responses
            with st.expander("📡 Risposte API Rates"):
                if "raw_api_responses" in st.session_state:
                    api_responses = st.session_state.raw_api_responses
                    rate_keys = [k for k in api_responses.keys() if k.startswith("rates_")]
                    
                    for key in rate_keys:
                        st.markdown(f"**{key}**")
                        st.json(api_responses[key])
            
            with st.expander("📅 Risposte API Heatmap"):
                if "raw_api_responses" in st.session_state:
                    api_responses = st.session_state.raw_api_responses
                    heatmap_keys = [k for k in api_responses.keys() if k.startswith("heatmap_")]
                    
                    for key in heatmap_keys:
                        st.markdown(f"**{key}**")
                        st.json(api_responses[key])
            
            with st.expander("🏨 Risposte API Hotel List"):
                if "raw_api_responses" in st.session_state:
                    api_responses = st.session_state.raw_api_responses
                    hotel_list_keys = [k for k in api_responses.keys() if k.startswith("hotel_list")]
                    
                    for key in hotel_list_keys:
                        st.markdown(f"**{key}**")
                        st.json(api_responses[key])
            
            # Analisi OTA
            with st.expander("🔍 Analisi OTA"):
                if "rate_data" in st.session_state:
                    available_df = df[df["available"]]
                    
                    if not available_df.empty:
                        st.markdown("### Conteggio OTA per hotel")
                        ota_counts = available_df.groupby("hotel")["ota"].nunique().sort_values(ascending=False)
                        st.bar_chart(ota_counts)
                        
                        st.markdown("### Tutte le OTA trovate")
                        all_otas = sorted(available_df["ota"].unique())
                        st.write(", ".join(all_otas))
                        
                        st.markdown("### Statistiche Prezzi per Hotel")
                        price_stats = available_df.groupby("hotel").agg({
                            "price": ["min", "max", "mean", "std"],
                            "ota": "count"
                        })
                        st.dataframe(price_stats)
            
            # Session State
            with st.expander("💾 Session State"):
                st.json({
                    "currency": st.session_state.get("currency", "N/A"),
                    "num_nights": st.session_state.get("num_nights", "N/A"),
                    "last_update": st.session_state.get("last_update", "N/A"),
                    "has_rate_data": "rate_data" in st.session_state,
                    "has_heatmap_data": "heatmap_data" in st.session_state,
                    "has_hotel_info": "hotel_info" in st.session_state
                })
        
    else:
        # Stato iniziale
        st.info("👆 Configura i parametri di ricerca nella sidebar e clicca su 'Cerca tariffe' per iniziare")
        
        # Quick stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 🏨 Hotel Monitorati
            - VOI Alimini
            - Ciaoclub Arco Del Saracino
            - Hotel Alpiselect Robinson Apulia
            - Alpiclub Hotel Thalas Club
            """)
        
        with col2:
            st.markdown("""
            ### 💰 Valute Supportate
            14 valute internazionali tra cui:
            - EUR (Euro)
            - USD (Dollaro USA)
            - GBP (Sterlina)
            - E molte altre...
            """)
        
        with col3:
            st.markdown("""
            ### 📊 Funzionalità
            - Confronto tariffe real-time
            - Analisi competitiva
            - Calendar pricing
            - Rating e qualità
            - Export Excel
            """)
    
    # Footer
    st.markdown("---")
    st.sidebar.markdown("---")
    st.sidebar.info("**Rate Checker VOI Alimini PRO**\nVersione 1.0.0\n\nDeveloped by Alessandro Merella\nPowered by Xotelo API")
    
    with st.expander("ℹ️ Informazioni e Guida"):
        st.markdown("""
        ### 🚀 Come usare il Rate Checker PRO
        
        **1. Configura la ricerca**
        - Seleziona hotel, date, occupazione e valuta nella sidebar
        - Puoi monitorare fino a 4 hotel competitor contemporaneamente
        - Supporta configurazioni complesse con bambini e camere multiple
        
        **2. Avvia la ricerca**
        - Clicca su "🔍 Cerca tariffe" per recuperare i dati in tempo reale
        - Il sistema recupera automaticamente: tariffe, calendari prezzi e rating
        - I dati vengono cached per ottimizzare le performance
        
        **3. Analizza i risultati**
        - **Dashboard KPI**: Metriche chiave sulla posizione competitiva di VOI Alimini
        - **Alerts intelligenti**: Raccomandazioni automatiche basate sui dati di mercato
        - **Analisi Comparativa**: Confronto dettagliato tra tutti gli hotel
        - **Confronto OTA**: Analisi canali di distribuzione per hotel
        - **Calendari Prezzi**: Heatmap per identificare periodi economici/costosi
        - **Rating e Qualità**: Correlazione tra qualità percepita e prezzi
        
        **4. Esporta i dati**
        - Usa il pulsante "📥 Esporta in Excel" per salvare i risultati
        - Export multi-sheet con dati completi, summary e best rates
        
        ---
        
        ### 📊 Funzionalità Principali
        
        **Dashboard KPI**
        - Posizione di mercato in tempo reale
        - Gap vs competitor più vicino
        - Benchmark vs media mercato
        - Numero OTA attive
        
        **Sistema Alerts Intelligente**
        - ⚠️ Warning se prezzi fuori mercato
        - ✅ Conferme per posizionamento ottimale
        - ℹ️ Info su distribuzione e spread prezzi
        - 🎯 Raccomandazioni strategiche
        
        **Price Positioning Chart**
        - Visualizzazione range prezzi min-max-avg
        - Identificazione immediata dei gap competitivi
        - Evidenziazione VOI Alimini
        
        **Analisi OTA Dettagliata**
        - Confronto prezzi per singola OTA
        - Calcolo spread distributivo
        - Identificazione best rate per canale
        
        **Calendar Pricing**
        - Heatmap settimanale dei prezzi
        - Identificazione periodi economici/medi/alti
        - Supporto pianificazione strategica tariffaria
        
        **Rating Analysis**
        - Confronto rating TripAdvisor
        - Indice Qualità/Prezzo
        - Scatter plot Prezzo vs Rating
        
        ---
        
        ### ⚙️ Note Tecniche
        
        **Caching e Performance**
        - Rates: cached per 5 minuti
        - Heatmap/Hotel Info: cached per 1 ora
        - Usa "🗑️ Cancella cache" per forzare aggiornamento dati
        
        **Dati Fonte**
        - Tutte le tariffe provengono da Xotelo API
        - Basato su meta-search di TripAdvisor
        - Aggiornamento real-time delle disponibilità
        
        **Chiavi Hotel**
        - Formato TripAdvisor: `g{location_id}-d{hotel_id}`
        - Esempio: VOI Alimini = `g652004-d1799967`
        - Recuperabili dall'URL TripAdvisor dell'hotel
        
        **Limitazioni Note**
        - Alcune OTA potrebbero non essere sempre disponibili
        - I prezzi visualizzati sono indicativi e soggetti a variazione
        - La disponibilità dipende dalle policy di rate display delle OTA
        
        ---
        
        ### 💡 Tips per Revenue Managers
        
        **Monitoraggio Quotidiano**
        - Controlla la dashboard KPI ogni mattina
        - Presta attenzione agli alerts per azioni rapide
        - Monitora lo spread OTA per identificare anomalie
        
        **Analisi Settimanale**
        - Esporta i dati Excel per analisi storica
        - Confronta i trend week-over-week
        - Analizza il calendar pricing per ottimizzare la strategia
        
        **Pianificazione Strategica**
        - Usa l'indice Qualità/Prezzo per posizionamento
        - Identifica i periodi per promozioni mirate
        - Monitora la distribuzione OTA e il coverage
        
        **Best Practices**
        - Fai screenshot della dashboard per meeting
        - Usa l'export Excel per presentazioni
        - Combina con dati PMS per analisi complete
        
        ---
        
        ### 🆘 Supporto e Troubleshooting
        
        **Nessun dato recuperato?**
        - Verifica la connessione internet
        - Controlla le date (check-out > check-in)
        - Prova a cancellare la cache
        
        **Prezzi sembrano errati?**
        - Verifica l'occupazione selezionata
        - Controlla la valuta
        - I prezzi sono per notte o totali?
        
        **Performance lente?**
        - Riduci il numero di hotel monitorati
        - Cancella la cache se troppo vecchia
        - Verifica la banda internet
        
        ---
        
        **Per supporto tecnico o feedback**: alessandro.merella@example.com
        
        **Versione**: 1.0.0 PRO  
        **Ultimo aggiornamento**: Febbraio 2026
        """)

if __name__ == "__main__":
    main()
