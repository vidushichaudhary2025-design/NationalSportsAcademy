
import os
import streamlit as st
import pandas as pd
import psycopg
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Athlete Management",
    page_icon="🏃",
    layout="wide"
)

st.title("🏃 Athlete Management")
st.caption("View, search, and register academy athletes.")

def connect_db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

def load_athletes():
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT athlete_id, full_name, date_of_birth,
                       gender, email, phone, enrollment_date, status
                FROM athletes
                ORDER BY athlete_id
            """)
            return pd.DataFrame(
                cur.fetchall(),
                columns=[col.name for col in cur.description]
            )

search = st.text_input("Search by athlete name")

try:
    athletes = load_athletes()

    if search:
        athletes = athletes[
            athletes["full_name"].str.contains(
                search, case=False, na=False
            )
        ]

    st.subheader("Athlete Directory")
    st.dataframe(athletes, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Register a New Athlete")

    with st.form("new_athlete"):
        name = st.text_input("Full name")
        dob = st.date_input(
            "Date of birth",
            value=None,
            min_value=pd.Timestamp("1900-01-01").date()
        )
        gender = st.selectbox(
            "Gender",
            ["Not specified", "Male", "Female", "Other"]
        )
        email = st.text_input("Email address")
        phone = st.text_input("Phone number")
        status = st.selectbox(
            "Status", ["Active", "Inactive", "Injured"]
        )

        submitted = st.form_submit_button("Register Athlete")

        if submitted:
            if not name.strip():
                st.error("Please enter the athlete's name.")
            else:
                try:
                    with connect_db() as conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                INSERT INTO athletes
                                    (full_name, date_of_birth, gender,
                                     email, phone, status)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                RETURNING athlete_id
                            """, (
                                name.strip(),
                                dob,
                                None if gender == "Not specified" else gender,
                                email.strip() or None,
                                phone.strip() or None,
                                status
                            ))
                            new_id = cur.fetchone()[0]

                    st.success(
                        f"Athlete registered successfully! ID: {new_id}"
                    )
                    st.rerun()

                except psycopg.errors.UniqueViolation:
                    st.error("That email address is already registered.")
                except Exception as e:
                    st.error(f"Could not register athlete: {e}")

except Exception as e:
    st.error(f"Could not load athletes: {e}")

