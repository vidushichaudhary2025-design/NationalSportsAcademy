
import os
import streamlit as st
import pandas as pd
import psycopg
import plotly.express as px
from dotenv import load_dotenv

# Load database configuration from .env
load_dotenv()

st.set_page_config(
    page_title="National Sports Academy",
    page_icon="🏆",
    layout="wide"
)

# Dashboard heading
st.title("🏆 National Sports Academy")
st.subheader("Athlete Management and Performance Analytics")
st.caption(
    "A centralized platform for athletes, competitions, training, "
    "wearable measurements, and injury records."
)


# Database connection and query helper
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

            if cur.description is None:
                return pd.DataFrame()

            columns = [col.name for col in cur.description]
            return pd.DataFrame(cur.fetchall(), columns=columns)


try:
    # --------------------------------------------------
    # DASHBOARD METRICS
    # --------------------------------------------------
    athletes = get_data("SELECT COUNT(*) AS total FROM athletes")
    sports = get_data("SELECT COUNT(*) AS total FROM sports")
    competitions = get_data(
        "SELECT COUNT(*) AS total FROM competitions"
    )
    sessions = get_data(
        "SELECT COUNT(*) AS total FROM training_sessions"
    )
    injuries = get_data("SELECT COUNT(*) AS total FROM injuries")
    readings = get_data(
        "SELECT COUNT(*) AS total FROM sensor_readings"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Registered Athletes",
        int(athletes.iloc[0]["total"])
    )
    c2.metric("Sports", int(sports.iloc[0]["total"]))
    c3.metric(
        "Competitions",
        int(competitions.iloc[0]["total"])
    )

    c4, c5, c6 = st.columns(3)

    c4.metric(
        "Training Sessions",
        int(sessions.iloc[0]["total"])
    )
    c5.metric(
        "Injury Records",
        int(injuries.iloc[0]["total"])
    )
    c6.metric(
        "Wearable Readings",
        int(readings.iloc[0]["total"])
    )

    st.divider()

    # --------------------------------------------------
    # ATHLETES BY SPORT
    # --------------------------------------------------
    left, right = st.columns(2)

    with left:
        st.subheader("🏃 Athletes by Sport")

        sport_data = get_data("""
            SELECT
                s.sport_name,
                COUNT(DISTINCT aps.athlete_id) AS athlete_count
            FROM sports s
            LEFT JOIN athlete_sports aps
                ON s.sport_id = aps.sport_id
            GROUP BY s.sport_id, s.sport_name
            ORDER BY athlete_count DESC
        """)

        if not sport_data.empty:
            fig = px.bar(
                sport_data,
                x="sport_name",
                y="athlete_count",
                title="Registered Athletes per Sport",
                labels={
                    "sport_name": "Sport",
                    "athlete_count": "Athletes"
                },
                color="sport_name"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sports data is available.")

    # --------------------------------------------------
    # INJURY RECOVERY STATUS
    # --------------------------------------------------
    with right:
        st.subheader("🩺 Injury Recovery Status")

        injury_data = get_data("""
            SELECT
                recovery_status,
                COUNT(*) AS total
            FROM injuries
            GROUP BY recovery_status
            ORDER BY total DESC
        """)

        if not injury_data.empty:
            fig = px.pie(
                injury_data,
                names="recovery_status",
                values="total",
                title="Injuries by Recovery Status",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No injury records are available.")

    st.divider()

    # --------------------------------------------------
    # RECENT TRAINING SESSIONS
    # --------------------------------------------------
    st.subheader("🏋️ Recent Training Sessions")

    training_data = get_data("""
        SELECT
            a.full_name AS athlete,
            s.sport_name AS sport,
            ts.session_date,
            ts.duration_minutes,
            ts.training_type,
            ts.intensity,
            ts.distance_km,
            ts.calories_burned
        FROM training_sessions ts
        JOIN athletes a
            ON ts.athlete_id = a.athlete_id
        JOIN sports s
            ON ts.sport_id = s.sport_id
        ORDER BY ts.session_date DESC
        LIMIT 10
    """)

    if not training_data.empty:
        st.dataframe(
            training_data,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No training sessions are available yet.")

    st.divider()

    # --------------------------------------------------
    # COMPETITION RESULTS
    # --------------------------------------------------
    st.subheader("🥇 Competition Results")

    results_data = get_data("""
        SELECT
            a.full_name AS athlete,
            c.competition_name AS competition,
            cr.ranking,
	    cr.result_value,
	    cr.result_unit,
            cr.medal
        FROM competition_results cr
        JOIN athletes a
            ON cr.athlete_id = a.athlete_id
        JOIN competitions c
            ON cr.competition_id = c.competition_id
        ORDER BY
            CASE cr.medal
                WHEN 'Gold' THEN 1
                WHEN 'Silver' THEN 2
                WHEN 'Bronze' THEN 3
                ELSE 4
            END,
            cr.ranking NULLS LAST
        LIMIT 15
    """)

    if not results_data.empty:
        st.dataframe(
            results_data,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No competition results are available yet.")

    st.divider()

    # --------------------------------------------------
    # FOOTER
    # --------------------------------------------------
    st.caption(
        "National Sports Academy Management System | "
        "Powered by Streamlit, PostgreSQL and TimescaleDB"
    )

except Exception as e:
    st.error("Unable to load the dashboard.")
    st.write("Please check your database connection and table names.")
    st.code(str(e))

