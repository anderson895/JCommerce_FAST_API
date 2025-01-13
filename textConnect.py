import psycopg2

# Replace with your actual connection details
DATABASE_URL = "postgresql://postgres.dajcekyqugcgteookxfb:DNWhZ7UsPWnMxbN0@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

try:
    # Attempt to connect
    conn = psycopg2.connect(DATABASE_URL)
    print("Connection successful")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
