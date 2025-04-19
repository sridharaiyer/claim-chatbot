# sql_agent.py
from pydantic_ai import Agent, RunContext, ModelRetry, format_as_xml
from models import SQLResponse, SQLQuery, InvalidSQLRequest  # Import response models
from db_utils import DB_SCHEMA  # Import DB schema
import os
from typing import Union

GPT4_MODEL = "openai:gpt-4.1-nano"


class SQLAgentDeps:
    pass


# Use a model good at code/SQL generation
sql_agent = Agent[None, SQLResponse](  # No explicit Deps needed for now
    # GPT-4o is good for this
    model=GPT4_MODEL,
    deps_type=None,  # No deps passed during run
    system_prompt=f"""
    You are an expert SQLite query generator. Your task is to create a SQLite SELECT query 
    based on the user's request to retrieve information from the 'claims' table.

    **Database Schema:**
    ```sql
    {DB_SCHEMA}
    Use code with caution.
    Python
    Important Notes:
    The table name is claims.
    Generate ONLY SELECT queries. Do NOT generate INSERT, UPDATE, DELETE, or other modifying queries.
    Use standard SQLite syntax. Pay attention to column names and types.
    The id column is the primary key (TEXT).
    incident_date is stored as DATETIME (ISO 8601 format string). Use functions like date(), datetime(), strftime() for date comparisons if needed. E.g., WHERE date(incident_date) = '2025-01-15'.
    Filter based on the details provided in the user's request (query_details).
    If the request is too vague or lacks specifics to form a query, respond using the InvalidSQLRequest schema.
    If the request seems valid, respond using the SQLQuery schema. Include a brief explanation if helpful.
    Examples:
    User Request (query_details): "claim ID CLM-9876543210"
    Output (SQLQuery): {{"sql": "SELECT * FROM claims WHERE id = 'CLM-9876543210';", "explanation": "Selects the claim matching the specified ID."}}
    User Request (query_details): "claims for policy holder John Doe"
    Output (SQLQuery): {{"sql": "SELECT * FROM claims WHERE policy_holder_name = 'John Doe';", "explanation": "Selects all claims for the policy holder named John Doe."}}
    User Request (query_details): "claims with status Approved for Alpha Insurance"
    Output (SQLQuery): {{"sql": "SELECT * FROM claims WHERE status = 'Approved' AND company = 'Alpha Insurance';", "explanation": "Selects approved claims from Alpha Insurance."}}
    User Request (query_details): "claims that happened yesterday"
    Output (SQLQuery): {{"sql": "SELECT * FROM claims WHERE date(incident_date) = date('now', '-1 day');", "explanation": "Selects claims where the incident occurred yesterday."}}
    User Request (query_details): "details about a claim"
    Output (InvalidSQLRequest): {{"error_message": "Please provide more specific details for the claim you want to retrieve, such as the claim ID or policy number."}}
    User Request (query_details): "delete claim 123"
    Output (InvalidSQLRequest): {{"error_message": "Sorry, I can only retrieve claim information. I cannot perform delete operations."}}
    """,
    instrument=True  # Optional
)
