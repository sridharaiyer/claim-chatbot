# db_utils.py
import sqlite3
import os
from contextlib import contextmanager
from typing import List, Tuple, Any, Dict, Optional
from models import Claim  # Use the Claim model from models.py
import logfire  # Optional logging

DATABASE_FILE = "claims.db"

# Optional: configure logfire
logfire.configure(send_to_logfire="if-token-present")

# --- Database Schema ---
# Matches the SQLAlchemy definition provided
DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS claims (
    id TEXT PRIMARY KEY,
    policy_holder_name TEXT,
    policy_number TEXT UNIQUE,
    vehicle_make TEXT,
    vehicle_model TEXT,
    vehicle_year INTEGER,
    incident_date DATETIME,
    incident_description TEXT,
    adjuster_name TEXT,
    status TEXT,
    company TEXT,
    claim_office TEXT,
    point_of_impact TEXT
);
"""


@contextmanager
def get_db_connection():
    """Provides a database connection."""
    # Use check_same_thread=False only if needed for specific frameworks like Streamlit
    # Be cautious about thread safety if modifying data concurrently.
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Return rows as dictionary-like objects
    try:
        yield conn
    finally:
        conn.close()


@logfire.instrument("Executing SQL: {query}")  # Optional instrumentation
def execute_sql(query: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Executes a SELECT SQL query and returns results or an error message."""
    # Basic validation (already done in SQL agent, but good defense)
    if not query.strip().upper().startswith("SELECT"):
        return [], "Error: Only SELECT queries are allowed for retrieval."

    results = []
    error = None
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            # Fetch all results as dictionaries
            results = [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        error = f"Error executing SQL: {e}"
        logfire.error("SQL Execution Failed", sql=query,
                      error=str(e))  # Log error

    return results, error


def explain_sql(query: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Runs EXPLAIN QUERY PLAN on a SQL query."""
    plan = []
    error = None
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            plan = [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        error = f"Error explaining SQL: {e}"
    return plan, error
