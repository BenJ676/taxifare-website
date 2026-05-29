import streamlit as st
import requests
import folium

from datetime import datetime
from streamlit_folium import st_folium


# --------------------------------------------------
# Configuration générale
# --------------------------------------------------

st.set_page_config(
    page_title="NYC Taxi Fare",
    page_icon="🚕",
    layout="wide"
)

API_URL = "https://taxifare-321391081145.europe-west1.run.app/predict"


# --------------------------------------------------
# Style CSS
# --------------------------------------------------

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #fff8e7 0%, #f7fbff 45%, #f4f0ff 100%);
    }

    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        color: #2d2a32;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        font-size: 1.1rem;
        color: #5f5b66;
        margin-bottom: 1.5rem;
    }

    .soft-card {
        background: rgba(255, 255, 255, 0.82);
        padding: 1.4rem;
        border-radius: 22px;
        box-shadow: 0 8px 28px rgba(45, 42, 50, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.9);
        margin-bottom: 1rem;
    }

    .result-card {
        background: linear-gradient(135deg, #ffe08a 0%, #ffb86b 100%);
        padding: 1.4rem;
        border-radius: 22px;
        box-shadow: 0 8px 28px rgba(45, 42, 50, 0.12);
        color: #2d2a32;
        text-align: center;
        margin-top: 1rem;
    }

    .result-price {
        font-size: 2.4rem;
        font-weight: 800;
        margin-top: 0.3rem;
    }

    .small-muted {
        color: #6c6672;
        font-size: 0.9rem;
    }

    div.stButton > button:first-child {
        border-radius: 14px;
        border: none;
        padding: 0.6rem 1rem;
        font-weight: 700;
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.75);
        padding: 1rem;
        border-radius: 18px;
        box-shadow: 0 4px 18px rgba(45, 42, 50, 0.06);
    }
    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# Fonctions
# --------------------------------------------------

@st.cache_data(ttl=3600)
def get_route(pickup_latitude, pickup_longitude, dropoff_latitude, dropoff_longitude):
    """
    Calcule un itinéraire routier avec OSRM.
    """

    osrm_url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{pickup_longitude},{pickup_latitude};"
        f"{dropoff_longitude},{dropoff_latitude}"
    )

    params = {
        "overview": "full",
        "geometries": "geojson"
    }

    try:
        response = requests.get(osrm_url, params=params, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()

        if not data.get("routes"):
            return None

        route = data["routes"][0]
        coordinates = route["geometry"]["coordinates"]

        route_coordinates = [[lat, lon] for lon, lat in coordinates]

        distance_km = route["distance"] / 1000
        duration_min = route["duration"] / 60

        return route_coordinates, distance_km, duration_min

    except requests.exceptions.RequestException:
        return None


def init_session_state():
    """
    Initialise les coordonnées par défaut.
    """

    defaults = {
        "pickup_latitude": 40.783282,
        "pickup_longitude": -73.950655,
        "dropoff_latitude": 40.769802,
        "dropoff_longitude": -73.984365,
        "last_clicked": None,
        "fare_prediction": None
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# --------------------------------------------------
# En-tête
# --------------------------------------------------

st.markdown('<div class="main-title">🚕 NYC Taxi Fare Predictor</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Sélectionne un départ et une arrivée sur la carte, puis estime le prix de la course.</div>',
    unsafe_allow_html=True
)


# --------------------------------------------------
# Calcul de route
# --------------------------------------------------

route_result = get_route(
    st.session_state.pickup_latitude,
    st.session_state.pickup_longitude,
    st.session_state.dropoff_latitude,
    st.session_state.dropoff_longitude
)


# --------------------------------------------------
# Layout principal
# --------------------------------------------------

map_col, side_col = st.columns([1.75, 1], gap="large")


# --------------------------------------------------
# Colonne carte
# --------------------------------------------------

with map_col:
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.subheader("🗺️ Carte interactive de New York")
    st.caption("Clique sur la carte, puis choisis si le point correspond au départ ou à l’arrivée.")

    nyc_map = folium.Map(
        location=[40.7580, -73.9855],
        zoom_start=12,
        tiles="CartoDB positron"
    )

    folium.Marker(
        [st.session_state.pickup_latitude, st.session_state.pickup_longitude],
        popup="Départ",
        tooltip="Départ",
        icon=folium.Icon(color="green", icon="play")
    ).add_to(nyc_map)

    folium.Marker(
        [st.session_state.dropoff_latitude, st.session_state.dropoff_longitude],
        popup="Arrivée",
        tooltip="Arrivée",
        icon=folium.Icon(color="red", icon="flag")
    ).add_to(nyc_map)

    if route_result:
        route_coordinates, route_distance_km, route_duration_min = route_result

        folium.PolyLine(
            locations=route_coordinates,
            weight=5,
            opacity=0.85,
            tooltip=f"{route_distance_km:.2f} km - {route_duration_min:.0f} min"
        ).add_to(nyc_map)

    else:
        folium.PolyLine(
            locations=[
                [st.session_state.pickup_latitude, st.session_state.pickup_longitude],
                [st.session_state.dropoff_latitude, st.session_state.dropoff_longitude]
            ],
            weight=4,
            opacity=0.7,
            tooltip="Trajet direct"
        ).add_to(nyc_map)

    map_data = st_folium(
        nyc_map,
        height=610,
        width=None,
        returned_objects=["last_clicked"],
        key="nyc_map"
    )

    if map_data and map_data.get("last_clicked"):
        st.session_state.last_clicked = map_data["last_clicked"]

    if st.session_state.last_clicked:
        lat = st.session_state.last_clicked["lat"]
        lng = st.session_state.last_clicked["lng"]

        st.info(f"Point sélectionné : latitude {lat:.6f}, longitude {lng:.6f}")

        point_col_1, point_col_2 = st.columns(2)

        with point_col_1:
            if st.button("📍 Utiliser comme départ"):
                st.session_state.pickup_latitude = lat
                st.session_state.pickup_longitude = lng
                st.session_state.fare_prediction = None
                st.rerun()

        with point_col_2:
            if st.button("🏁 Utiliser comme arrivée"):
                st.session_state.dropoff_latitude = lat
                st.session_state.dropoff_longitude = lng
                st.session_state.fare_prediction = None
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# --------------------------------------------------
# Colonne droite
# --------------------------------------------------

with side_col:
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.subheader("⚙️ Paramètres")

    pickup_date = st.date_input("Date de la course")
    pickup_time = st.time_input("Heure de la course")

    passenger_count = st.number_input(
        "Nombre de passagers",
        min_value=1,
        max_value=8,
        value=1
    )

    st.markdown("### 📍 Départ")

    pickup_latitude = st.number_input(
        "Latitude départ",
        value=st.session_state.pickup_latitude,
        format="%.6f"
    )

    pickup_longitude = st.number_input(
        "Longitude départ",
        value=st.session_state.pickup_longitude,
        format="%.6f"
    )

    st.markdown("### 🏁 Arrivée")

    dropoff_latitude = st.number_input(
        "Latitude arrivée",
        value=st.session_state.dropoff_latitude,
        format="%.6f"
    )

    dropoff_longitude = st.number_input(
        "Longitude arrivée",
        value=st.session_state.dropoff_longitude,
        format="%.6f"
    )

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.subheader("🛣️ Trajet")

    if route_result:
        st.metric("Distance routière", f"{route_distance_km:.2f} km")
        st.metric("Durée estimée", f"{route_duration_min:.0f} min")
    else:
        st.warning("Impossible de calculer l’itinéraire routier pour le moment.")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.subheader("🔮 Prédiction")

    pickup_datetime = datetime.combine(pickup_date, pickup_time)

    params = {
        "pickup_datetime": pickup_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        "pickup_longitude": pickup_longitude,
        "pickup_latitude": pickup_latitude,
        "dropoff_longitude": dropoff_longitude,
        "dropoff_latitude": dropoff_latitude,
        "passenger_count": passenger_count,
    }

    if st.button("🚕 Estimer le prix", type="primary", use_container_width=True):
        try:
            response = requests.get(API_URL, params=params, timeout=20)

            if response.status_code == 200:
                prediction = response.json()
                st.session_state.fare_prediction = prediction["fare"]
            else:
                st.error("L’API n’a pas répondu correctement.")
                st.write("Code erreur :", response.status_code)
                st.write(response.text)

        except requests.exceptions.RequestException:
            st.error("Impossible de contacter l’API.")

    if st.session_state.fare_prediction is not None:
        st.markdown(
            f"""
            <div class="result-card">
                <div>Prix estimé de la course</div>
                <div class="result-price">${st.session_state.fare_prediction:.2f}</div>
                <div class="small-muted">Sinon tu peux marcher, ce sera toujours moins cher !!</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)
