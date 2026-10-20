
from flask import Flask, jsonify
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "tsdb"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode="require"
    )

@app.route("/")
def home():
    return "National Sports Academy Management System API is running!"

@app.route("/api/athletes")
def get_athletes():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT athlete_id, athlete_name, status
            FROM athletes
            ORDER BY athlete_id;
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        athletes = [
            {
                "athlete_id": row[0],
                "athlete_name": row[1],
                "status": row[2]
            }
            for row in rows
        ]
        return jsonify(athletes)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
