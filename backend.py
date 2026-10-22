
from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)
CORS(app)

# PostgreSQL / TimescaleDB connection
def get_db_connection():
    return psycopg2.connect(
        host="127.0.0.1",
        port=6543,
        database=os.getenv("DB_NAME", "sports_academy"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )


# Home route
@app.route("/")
def home():
    return "National Sports Academy Backend is running!"


# Get all athletes
@app.route("/api/athletes", methods=["GET"])
def get_athletes():
    conn = None

    try:
        conn = get_db_connection()

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT athlete_name, status
                FROM athletes
                ORDER BY athlete_name;
            """)

            athletes = cursor.fetchall()

        return jsonify(athletes)

    except Exception as e:
        app.logger.exception("Could not fetch athletes")
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

