import os
import psycopg2

#def get_connection():
#    return psycopg2.connect(
#        host=os.getenv("POSTGRES_HOST", "localhost"),
#        port=int(os.getenv("POSTGRES_PORT", "5433")),
#        dbname=os.getenv("POSTGRES_DB", "bank_db"),
#        user=os.getenv("POSTGRES_USER", "postgres"),
#        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
#    )

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "banking"),
        user=os.getenv("POSTGRES_USER", "bank"),
        password=os.getenv("POSTGRES_PASSWORD", "bankpass"),
    )

