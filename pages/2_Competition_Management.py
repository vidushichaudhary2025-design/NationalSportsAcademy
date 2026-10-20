
import os
import streamlit as st
import pandas as pd
import psycopg
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Competition Management",
    page_icon="🏆",
    layout="wide"
)

st.title("🏆 Competition Management")
st.caption("Manage competitions, schedules, and athlete results.")


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


# Load competitions and sports
try:
    competitions = load_data("""
        SELECT
            c.competition_id,
            c.competition_name,
            s.sport_name,
            c.competition_level,
            c.location,
            c.start_date,
            c.end_date
        FROM competitions c
        LEFT JOIN sports s ON c.sport_id = s.sport_id
        ORDER BY c.start_date DESC
    """)

    results = load_data("""
        SELECT
            c.competition_name,
            a.full_name AS athlete_name,
            cr.result_value,
            cr.result_unit,
            cr.ranking,
            cr.medal
        FROM competition_results cr
        JOIN competitions c
            ON cr.competition_id = c.competition_id
        JOIN athletes a
            ON cr.athlete_id = a.athlete_id
        ORDER BY c.competition_name, cr.ranking
    """)

    # Summary cards
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Competitions", len(competitions))
    col2.metric("Sports Represented", competitions["sport_name"].nunique())
    col3.metric("Recorded Results", len(results))

    st.divider()

    # Competition directory
    st.subheader("📋 Competition Directory")

    search = st.text_input("Search competition by name")

    if search:
        displayed = competitions[
            competitions["competition_name"].str.contains(
                search, case=False, na=False
            )
        ]
    else:
        displayed = competitions

    st.dataframe(
        displayed,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # Add competition
    st.subheader("➕ Add a New Competition")

    sports = load_data("""
        SELECT sport_id, sport_name
        FROM sports
        ORDER BY sport_name
    """)

    if sports.empty:
        st.warning("Add sports to the sports table before creating competitions.")
    else:
        with st.form("add_competition"):
            competition_name = st.text_input("Competition name")

            sport_options = dict(
                zip(sports["sport_name"], sports["sport_id"])
            )
            selected_sport = st.selectbox(
                "Sport",
                list(sport_options.keys())
            )

            level = st.selectbox(
                "Competition level",
                ["District", "State", "National", "International", "Inter-Academy"]
            )

            location = st.text_input("Location")

            start_date = st.date_input(
                "Start date",
                value=pd.Timestamp.today().date()
            )

            end_date = st.date_input(
                "End date",
                value=pd.Timestamp.today().date()
            )

            submitted = st.form_submit_button("Add Competition")

            if submitted:
                if not competition_name.strip():
                    st.error("Please enter a competition name.")
                elif end_date < start_date:
                    st.error("End date cannot be before the start date.")
                else:
                    try:
                        with connect_db() as conn:
                            with conn.cursor() as cur:
                                cur.execute("""
                                    INSERT INTO competitions (
                                        competition_name,
                                        sport_id,
                                        competition_level,
                                        location,
                                        start_date,
                                        end_date
                                    )
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                    RETURNING competition_id
                                """, (
                                    competition_name.strip(),
                                    sport_options[selected_sport],
                                    level,
                                    location.strip() or None,
                                    start_date,
                                    end_date
                                ))

                                new_id = cur.fetchone()[0]

                        st.success(
                            f"Competition added successfully! ID: {new_id}"
                        )
                        st.rerun()

                    except psycopg.errors.UniqueViolation:
                        st.error("This competition already exists.")
                    except Exception as e:
                        st.error(f"Could not add competition: {e}")

    st.divider()

    # Results
    st.subheader("🥇 Competition Results")

    if results.empty:
        st.info("No competition results have been recorded yet.")
    else:
        st.dataframe(
            results,
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"Could not load competition data: {e}")
    st.info(
        "Check your database connection and confirm that "
        "the competitions, sports, athletes, and competition_results "
        "tables exist."
    )

