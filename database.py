import os
import urllib.parse

from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase

# Load the variables from .env
load_dotenv()

def get_db():
    """
    Initializes and returns a LangChain SQLDatabase object 
    connected to a PostgreSQL instance.
    """
    user = os.getenv("DB_USER")
    password = os.getenv("PASSWORD")
    host = os.getenv("HOST")
    port = os.getenv("PORT")
    dbname = os.getenv("DBNAME")
    encoded_password = urllib.parse.quote_plus(password)

    uri = f"postgresql+psycopg2://{user}:{encoded_password}@{host}:{port}/{dbname}"

    try:
        db = SQLDatabase.from_uri(uri, sample_rows_in_table_info=1)
        return db
    except Exception as e:
        print(f"❌ Database Connection Error: {e}")
        return None

# Quick test if run directly
if __name__ == "__main__":
    db = get_db()
    if db:
        print("✅ Database Connection Successful!")
    else:
        print("❌ Database Connection Failed. Check your credentials.")