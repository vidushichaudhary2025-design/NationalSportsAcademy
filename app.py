
import os
import streamlit as st
import pandas as pd
import psycopg
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="National Sports Academy",
    page_icon="🏆",
    layout="wide"
)

st.title("🏆 National Sports Academy")
st.subheader("Athlete Management and Performance Analytics")
st.caption(
    "A centralized platform for athletes, competitions, training, "
    "wearable measurements, and injury records."
)


def get_data(query, params=None):
    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            columns = [col.name for col in cur.description]
            return pd.DataFrame(cur.fetchall(), columns=columns)


try:
    # Dashboard metrics
    athletes = get_data(
        "SELECT COUNT(*) AS total FROM athletes"
    )
    sports = get_data(
        "SELECT COUNT(*) AS total FROM sports"
    )
    competitions = get_data(
        "SELECT COUNT(*) AS total FROM competitions"
    )
    sessions = get_data(
        "SELECT COUNT(*) AS total FROM training_sessions"
    )
    injuries = get_data(
        "SELECT COUNT(*) AS total FROM injuries"
    )
    readings = get_data(
        "SELECT COUNT(*) AS total FROM sensor_readings"
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Registered Athletes", int(athletes.iloc[0, 0]))
    c2.metric("Sports", int(sports.iloc[0, 0]))
    c3.metric("Competitions", int(competitions.iloc[0, 0]))

    c4, c5, c6 = st.columns(3)
    c4.metric("Training Sessions", int(sessions.iloc[0, 0]))
    c5.metric("Injury Records", int(injuries.iloc[0, 0]))
    c6.metric("Wearable Readings", int(readings.iloc[0, 0]))

    st.divider()

    # Athletes by sport
    left, right = st.columns(2)

    with left:
        st.subheader("🏃 Athletes by Sport")

        sport_data = get_data("""
            SELECT s.sport_name,
                   COUNT(DISTINCT aps.athlete_id) AS athlete_count
            FROM sports s
            LEFT JOIN athlete_sports aps
                ON s.sport_id = aps.sport_id
            GROUP BY s.sport_id, s.sport_name
            ORDER BY athlete_count DESC
        """)

        fig = px.bar(
            sport_data,
            x="sport_name",
            y="athlete_count",
            title="Registered Athletes per Sport",
            labels={
                "sport_name": "Sport",
                "athlete_count": "Athletes"
            }
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("🏥 Injury Recovery Status")

        injury_data = get_data("""
            SELECT recovery_status, COUNT(*) AS total
            FROM injuries
            GROUP BY recovery_status
        """)

        if not injury_data.empty:
            fig = px.pie(
                injury_data,
                names="recovery_status",
                values="total",
                title="Recovery Status Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No injury records available yet.")

    st.divider()

    # Recent training sessions
    st.subheader("📊 Recent Training Sessions")

    recent_sessions = get_data("""
        SELECT a.full_name AS athlete,
               s.sport_name,
               ts.session_date,
               ts.duration_minutes,
               ts.intensity,
               ts.training_type
        FROM training_sessions ts
        JOIN athletes a ON ts.athlete_id = a.athlete_id
        JOIN sports s ON ts.sport_id = s.sport_id
        ORDER BY ts.session_date DESC
        LIMIT 10
    """)

    st.dataframe(
        recent_sessions,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # Competition results
    st.subheader("🥇 Competition Results")

    results = get_data("""
        SELECT c.competition_name,
               a.full_name AS athlete,
               cr.ranking,
               cr.medal,
               cr.result_value,
               cr.result_unit
        FROM competition_results cr
        JOIN competitions c
            ON c.competition_id = cr.competition_id
        JOIN athletes a
            ON a.athlete_id = cr.athlete_id
        ORDER BY cr.ranking NULLS LAST
        LIMIT 20
    """)

    if results.empty:
        st.info("No competition results recorded yet.")
    else:
        st.dataframe(
            results,
            use_container_width=True,
            hide_index=True
        )

    st.caption(
        "National Sports Academy Management System | "
        "PostgreSQL + TimescaleDB + Python + Streamlit"
    )

except Exception as e:
    st.error(f"Unable to load dashboard data: {e}")
    st.info(
        "Check that PostgreSQL is running and that the required "
        "tables and column names exist."
    )

