
import os
import streamlit as st
import pandas as pd
import psycopg
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Injury Monitoring",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Injury Monitoring")
st.caption("Track injury records, severity, and recovery status.")


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
    injuries = load_data("""
        SELECT
            i.injury_id,
            a.full_name AS athlete_name,
            i.injury_date,
            i.injury_type,
            i.severity,
            i.treatment,
            i.recovery_status,
            i.return_date,
            s.full_name AS treated_by
        FROM injuries i
        JOIN athletes a ON i.athlete_id = a.athlete_id
        LEFT JOIN staff s ON i.treated_by = s.staff_id
        ORDER BY i.injury_date DESC
    """)

    total = len(injuries)
    ongoing = len(
        injuries[injuries["recovery_status"].isin(
            ["Under Treatment", "Recovering"]
        )]
    )
    severe = len(injuries[injuries["severity"] == "Severe"])
    recovered = len(
        injuries[injuries["recovery_status"] == "Recovered"]
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Injury Records", total)
    c2.metric("Ongoing Cases", ongoing)
    c3.metric("Severe Injuries", severe)
    c4.metric("Recovered Cases", recovered)

    st.divider()

    st.subheader("🔎 Filter Injury Records")

    if not injuries.empty:
        athlete_options = ["All Athletes"] + sorted(
            injuries["athlete_name"].dropna().unique().tolist()
        )
        status_options = ["All Statuses"] + sorted(
            injuries["recovery_status"].dropna().unique().tolist()
        )

        col1, col2 = st.columns(2)

        with col1:
            selected_athlete = st.selectbox(
                "Athlete", athlete_options
            )

        with col2:
            selected_status = st.selectbox(
                "Recovery status", status_options
            )

        filtered = injuries.copy()

        if selected_athlete != "All Athletes":
            filtered = filtered[
                filtered["athlete_name"] == selected_athlete
            ]

        if selected_status != "All Statuses":
            filtered = filtered[
                filtered["recovery_status"] == selected_status
            ]

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader("📊 Injuries by Severity")
        severity_data = (
            injuries.groupby("severity")
            .size()
            .reset_index(name="count")
        )

        if not severity_data.empty:
            fig = px.bar(
                severity_data,
                x="severity",
                y="count",
                title="Injury Severity Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Recovery Status Distribution")
        recovery_data = (
            injuries.groupby("recovery_status")
            .size()
            .reset_index(name="count")
        )

        if not recovery_data.empty:
            fig = px.pie(
                recovery_data,
                names="recovery_status",
                values="count",
                title="Injury Recovery Status"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No injury records have been entered yet.")

    st.divider()

    st.subheader("➕ Add an Injury Record")

    athletes = load_data("""
        SELECT athlete_id, full_name
        FROM athletes
        ORDER BY full_name
    """)

    staff = load_data("""
        SELECT staff_id, full_name, role
        FROM staff
        ORDER BY full_name
    """)

    if athletes.empty:
        st.warning("Register athletes before adding injury records.")
    else:
        athlete_lookup = dict(
            zip(athletes["full_name"], athletes["athlete_id"])
        )

        staff_lookup = dict(
            zip(staff["full_name"], staff["staff_id"])
        )

        with st.form("add_injury"):
            athlete_name = st.selectbox(
                "Athlete",
                list(athlete_lookup.keys())
            )

            injury_date = st.date_input(
                "Injury date",
                value=pd.Timestamp.today().date()
            )

            injury_type = st.text_input("Injury type")

            severity = st.selectbox(
                "Severity", ["Mild", "Moderate", "Severe"]
            )

            recovery_status = st.selectbox(
                "Recovery status",
                ["Under Treatment", "Recovering", "Recovered"]
            )

            treatment = st.text_area(
                "Treatment notes (optional)"
            )

            treated_by_name = st.selectbox(
                "Treated by (optional)",
                ["Not assigned"] + list(staff_lookup.keys())
            )

            return_date = st.date_input(
                "Expected/actual return date (optional)",
                value=None
            )

            submitted = st.form_submit_button("Save Injury Record")

            if submitted:
                if not injury_type.strip():
                    st.error("Please enter the injury type.")
                else:
                    try:
                        treated_by_id = (
                            None if treated_by_name == "Not assigned"
                            else staff_lookup[treated_by_name]
                        )

                        with connect_db() as conn:
                            with conn.cursor() as cur:
                                cur.execute("""
                                    INSERT INTO injuries (
                                        athlete_id,
                                        treated_by,
                                        injury_date,
                                        injury_type,
                                        severity,
                                        treatment,
                                        recovery_status,
                                        return_date
                                    )
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                    RETURNING injury_id
                                """, (
                                    athlete_lookup[athlete_name],
                                    treated_by_id,
                                    injury_date,
                                    injury_type.strip(),
                                    severity,
                                    treatment.strip() or None,
                                    recovery_status,
                                    return_date
                                ))

                                new_id = cur.fetchone()[0]

                        st.success(
                            f"Injury record saved successfully! ID: {new_id}"
                        )
                        st.rerun()

                    except Exception as e:
                        st.error(f"Could not save injury record: {e}")

except Exception as e:
    st.error(f"Could not load injury monitoring: {e}")
    st.info(
        "Check your database connection and the column names "
        "in the injuries, athletes, and staff tables."
    )

