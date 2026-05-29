import streamlit as st
import requests
from datetime import datetime

st.title("TaxiFareModel front")

st.markdown("""
Cette application permet d'estimer le prix d'une course de taxi à partir de plusieurs paramètres :
date, coordonnées de départ, coordonnées d'arrivée et nombre de passagers.
""")

st.header("Paramètres de la course de taxi")

pickup_date = st.date_input("Date de la course")
pickup_time = st.time_input("Heure de la course")

pickup_longitude = st.number_input("Pickup longitude", value=-73.950655)
pickup_latitude = st.number_input("Pickup latitude", value=40.783282)

dropoff_longitude = st.number_input("Dropoff longitude", value=-73.984365)
dropoff_latitude = st.number_input("Dropoff latitude", value=40.769802)

passenger_count = st.number_input("Nombre de passagers", min_value=1, max_value=8, value=1)

pickup_datetime = datetime.combine(pickup_date, pickup_time)

url = "https://taxifare-321391081145.europe-west1.run.app/predict"

params = {
    "pickup_datetime": pickup_datetime.strftime("%Y-%m-%d %H:%M:%S"),
    "pickup_longitude": pickup_longitude,
    "pickup_latitude": pickup_latitude,
    "dropoff_longitude": dropoff_longitude,
    "dropoff_latitude": dropoff_latitude,
    "passenger_count": passenger_count
}

if st.button("Prédire le prix de la course"):
    response = requests.get(url, params=params)

    if response.status_code == 200:
        prediction = response.json()
        fare = prediction["fare"]

        st.success(f"Prix estimé : ${fare:.2f}")
    else:
        st.error("Erreur lors de l'appel à l'API.")
        st.write(response.text)
