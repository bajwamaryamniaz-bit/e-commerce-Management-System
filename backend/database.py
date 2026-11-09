import os
import sys
import logging
from .config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Try importing psycopg2 for PostgreSQL
HAS_PSYCOPG2 = False
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_PSYCOPG2 = True
except ImportError:
    logger.warning("psycopg2 is not installed. Run 'pip install psycopg2-binary' to connect to PostgreSQL.")

import sqlite3

_POSTGRES_FAILED = False

def get_connection():
    """
    Establishes and returns a database connection according to Config.
    Defaults to PostgreSQL as requested in DBMS project specifications.
    Falls back gracefully to SQLite if PostgreSQL fails or isn't configured.
    """
    global _POSTGRES_FAILED
    if Config.DB_ENGINE == "postgresql" and HAS_PSYCOPG2 and not _POSTGRES_FAILED:
        try:
            if Config.DATABASE_URL:
                conn = psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor)
            else:
                conn = psycopg2.connect(
                    host=Config.DB_HOST,
                    port=Config.DB_PORT,
                    database=Config.DB_NAME,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    cursor_factory=RealDictCursor
                )
            return conn, "postgresql"
        except Exception as e:
            _POSTGRES_FAILED = True
            logger.warning(f"Could not connect to PostgreSQL ({e}). Using local preview database.")
    
    # Fallback SQLite connection
    conn = sqlite3.connect(Config.SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn, "sqlite"

def execute_query(query, params=None, fetch=None, commit=True):
    """
    Execute a parameterized SQL query safely against SQL injection.
    """
    conn, engine = get_connection()
    try:
        adjusted_query = query
        if engine == "sqlite":
            adjusted_query = adjusted_query.replace("%s", "?")
            adjusted_query = adjusted_query.replace("TO_CHAR(sale_date, 'Mon DD')", "strftime('%m/%d', sale_date)")
            adjusted_query = adjusted_query.replace("CURRENT_TIMESTAMP - INTERVAL '15 days'", "datetime('now', '-15 days')")
            adjusted_query = adjusted_query.replace("CURRENT_TIMESTAMP - INTERVAL '8 days'", "datetime('now', '-8 days')")
            adjusted_query = adjusted_query.replace("CURRENT_TIMESTAMP - INTERVAL '5 days'", "datetime('now', '-5 days')")
            adjusted_query = adjusted_query.replace("CURRENT_TIMESTAMP - INTERVAL '3 days'", "datetime('now', '-3 days')")
            adjusted_query = adjusted_query.replace("CURRENT_TIMESTAMP - INTERVAL '2 days'", "datetime('now', '-2 days')")
            adjusted_query = adjusted_query.replace("CURRENT_TIMESTAMP - INTERVAL '1 day'", "datetime('now', '-1 day')")
            adjusted_query = adjusted_query.replace("CURRENT_TIMESTAMP - INTERVAL '6 hours'", "datetime('now', '-6 hours')")

        cursor = conn.cursor()
        if params:
            cursor.execute(adjusted_query, params)
        else:
            cursor.execute(adjusted_query)
        
        result = None
        if fetch == "all":
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
        elif fetch == "one":
            row = cursor.fetchone()
            if row:
                result = dict(row)
        else:
            if commit:
                conn.commit()
            result = cursor.rowcount

        cursor.close()
        return result
    except Exception as err:
        conn.rollback()
        logger.error(f"Database error executing query: {err}\nQuery: {query}\nParams: {params}")
        raise err
    finally:
        conn.close()

def execute_transaction_block(callback):
    """
    Executes a series of database operations atomically within a single transaction.
    """
    conn, engine = get_connection()
    cursor = conn.cursor()
    try:
        result = callback(cursor, engine)
        conn.commit()
        return result
    except Exception as e:
        conn.rollback()
        logger.error(f"Transaction failed and was rolled back: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()
