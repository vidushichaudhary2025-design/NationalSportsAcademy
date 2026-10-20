
import os
import streamlit as st
import pandas as pd
import psycopg
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Wearable Analytics",
    page_icon="⌚",
    layout="wide"
)

st.title("⌚ Wearable Data Visualization")
st.caption("Analyze athlete measurements collected from wearable devices.")


def connect_db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


def load_data(query, params=None):
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            columns = [col.name for col in cur.description]
            return pd.DataFrame(cur.fetchall(), columns=columns)


try:
    data = load_data("""
        SELECT
            sr.time,
            a.full_name AS athlete_name,
            d.serial_number,
            sr.heart_rate,
            sr.speed_kmh,
            sr.distance_km,
            sr.calories_burned,
            sr.training_intensity
        FROM sensor_readings sr
        JOIN devices d ON sr.device_id = d.device_id
        JOIN athletes a ON d.athlete_id = a.athlete_id
        ORDER BY sr.time
    """)

    if data.empty:
        st.warning(
            "No wearable readings found. Add records to sensor_readings "
            "and make sure each device is assigned to an athlete."
        )
    else:
        data["time"] = pd.to_datetime(data["time"])

        athletes = ["All Athletes"] + sorted(
            data["athlete_name"].dropna().unique().tolist()
        )
        selected = st.selectbox("Select athlete", athletes)

        if selected != "All Athletes":
            data = data[data["athlete_name"] == selected]

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Sensor Readings", len(data))

        avg_hr = data["heart_rate"].dropna().mean()
        c2.metric(
            "Average Heart Rate",
            f"{avg_hr:.1f} bpm" if pd.notna(avg_hr) else "N/A"
        )

        max_speed = data["speed_kmh"].dropna().max()
        c3.metric(
            "Maximum Speed",
            f"{max_speed:.1f} km/h" if pd.notna(max_speed) else "N/A"
        )

        total_distance = data["distance_km"].dropna().sum()
        c4.metric("Sum of Distance Values", f"{total_distance:.2f} km")

        st.divider()

        st.subheader("❤️ Heart Rate Over Time")
        hr_data = data.dropna(subset=["heart_rate"])

        if not hr_data.empty:
            fig = px.line(
                hr_data,
                x="time",
                y="heart_rate",
                color="athlete_name",
                markers=True,
                title="Heart Rate Measurements",
                labels={
                    "time": "Timestamp",
                    "heart_rate": "Heart Rate (bpm)",
                    "athlete_name": "Athlete"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("🏃 Speed Over Time")
        speed_data = data.dropna(subset=["speed_kmh"])

        if not speed_data.empty:
            fig = px.line(
                speed_data,
                x="time",
                y="speed_kmh",
                color="athlete_name",
                markers=True,
                title="Recorded Speed",
                labels={
                    "time": "Timestamp",
                    "speed_kmh": "Speed (km/h)"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("🔥 Calories Recorded")
        calories_data = data.dropna(subset=["calories_burned"])

        if not calories_data.empty:
            fig = px.bar(
                calories_data,
                x="time",
                y="calories_burned",
                color="athlete_name",
                title="Calories per Sensor Reading",
                labels={
                    "time": "Timestamp",
                    "calories_burned": "Calories"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Sensor Records")
        st.dataframe(data, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Could not load wearable data: {e}")
    st.info(
        "Check that sensor_readings, devices, and athletes exist "
        "and that their column names match the SQL query."
    )

