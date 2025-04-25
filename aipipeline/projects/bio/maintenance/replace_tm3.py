# Correcting the media_files field in the tator_online database
import time
import psycopg2
import os

# Postgres settings
POSTGRES_HOST="mantis.shore.mbari.org"
POSTGRES_USER=os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD=os.environ.get("POSTGRES_PASSWORD")
POSTGRES_DB=os.environ.get("POSTGRES_DB")

sql_query = """
UPDATE tator_online.public.main_media
SET media_files = replace(media_files::TEXT, 'm3.shore.mbari.org', 'mantis.shore.mbari.org')::jsonb
WHERE media_files::TEXT LIKE '%m3.shore.mbari.org%';
"""

try:
    conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=5432
    )
    # Run the SQL query every 3 minutes
    while True:
        cur = conn.cursor()
        cur.execute(sql_query)
        conn.commit()
        print("Update successful! Rows affected:", cur.rowcount)
        time.sleep(180)

except Exception as e:
    print(f"Error: {e}")

finally:
    if cur:
        cur.close()
    if conn:
        conn.close()
