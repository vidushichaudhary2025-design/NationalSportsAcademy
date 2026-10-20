import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=5
    )

    cur = conn.cursor()
    cur.execute("""
        SELECT current_database(),
               current_user,
               version()
    """)

    print("Database connection successful!")
    print(cur.fetchone())

    cur.close()
    conn.close()

except Exception as e:
    print("Connection failed:", e)
