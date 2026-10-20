
import os
import streamlit as st
import pandas as pd
import psycopg
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Training Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Training Analytics")
st.caption("Monitor athlete training sessions, workload, and performance.")


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
    sessions = load_data("""
        SELECT
            ts.session_id,
            a.full_name AS athlete_name,
            s.sport_name,
            stf.full_name AS coach_name,
            ts.session_date,
            ts.duration_minutes,
            ts.training_type,
            ts.intensity,
            ts.distance_km,
            ts.calories_burned,
            ts.notes
        FROM training_sessions ts
        JOIN athletes a ON ts.athlete_id = a.athlete_id
        JOIN sports s ON ts.sport_id = s.sport_id
        LEFT JOIN staff stf ON ts.coach_id = stf.staff_id
        ORDER BY ts.session_date DESC
    """)

    st.subheader("Training Overview")

    total_sessions = len(sessions)
    total_minutes = (
        pd.to_numeric(sessions["duration_minutes"], errors="coerce")
        .fillna(0).sum()
    )
    athlete_count = sessions["athlete_name"].nunique()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Sessions", total_sessions)
    c2.metric("Training Hours", f"{total_minutes / 60:.1f}")
    c3.metric("Athletes Trained", athlete_count)

    st.divider()

    if sessions.empty:
        st.info(
            "No training sessions found. Add records to the "
            "training_sessions table to display analytics."
        )
    else:
        st.subheader("Filter Training Sessions")

        athlete_options = ["All Athletes"] + sorted(
            sessions["athlete_name"].dropna().unique().tolist()
        )

        selected_athlete = st.selectbox(
            "Select athlete", athlete_options
        )

        filtered = sessions.copy()

        if selected_athlete != "All Athletes":
            filtered = filtered[
                filtered["athlete_name"] == selected_athlete
            ]

        st.dataframe(filtered, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Training Duration by Athlete")

        duration_data = (
            filtered.groupby("athlete_name", as_index=False)
            ["duration_minutes"].sum()
        )

        fig = px.bar(
            duration_data,
            x="athlete_name",
            y="duration_minutes",
            title="Total Training Duration",
            labels={
                "athlete_name": "Athlete",
                "duration_minutes": "Duration (minutes)"
            }
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Training Sessions by Sport")

        sport_data = (
            filtered.groupby("sport_name", as_index=False)
            .size()
            .rename(columns={"size": "sessions"})
        )

        fig = px.bar(
            sport_data,
            x="sport_name",
            y="sessions",
            title="Number of Sessions per Sport"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Training Intensity Distribution")

        intensity_data = (
            filtered.groupby("intensity", dropna=False)
            .size()
            .reset_index(name="sessions")
        )

        fig = px.pie(
            intensity_data,
            names="intensity",
            values="sessions",
            title="Sessions by Intensity"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Distance Covered")

        distance_data = filtered.dropna(subset=["distance_km"])

        if not distance_data.empty:
            fig = px.bar(
                distance_data,
                x="athlete_name",
                y="distance_km",
                color="sport_name",
                title="Distance per Training Session",
                labels={"distance_km": "Distance (km)"}
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Calories Burned")

        calorie_data = filtered.dropna(subset=["calories_burned"])

        if not calorie_data.empty:
            fig = px.bar(
                calorie_data,
                x="athlete_name",
                y="calories_burned",
                color="sport_name",
                title="Calories Recorded per Session",
                labels={"calories_burned": "Calories"}
            )
            st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Could not load training analytics: {e}")
    st.info(
        "Check the database connection and training_sessions table."
    )

