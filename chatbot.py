# chatbot.py
import streamlit as st
import httpx
import asyncio
from datetime import datetime
import json
import traceback
from typing import List, Dict, Any, Optional

# Import necessary components
from models import (
    Claim, ClaimCreate, PartialClaim, HTTPValidationError,
    Intent, SQLQuery, InvalidSQLRequest, SQLResponse
)
from extraction_agent import extraction_agent
from synthesizer import synthesize_claim
from db_utils import execute_sql, explain_sql
from intent_agent import intent_agent
from sql_agent import sql_agent
from pydantic import ValidationError as PydanticValidationError, TypeAdapter

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000"

# --- Streamlit App ---

st.set_page_config(page_title="Test Claim Generator Bot", layout="wide")
st.title("🤖 Test Claim + Retrieval Bot")
st.caption(
    "I can help you generate test claims or retrieve existing ones from the database.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant",
            "content": "Hello! How can I help you create or find a test claim today?"}
    ]

# --- Helper Functions ---


def display_results_as_table(results: List[Dict[str, Any]]):
    if not results:
        st.info("No matching claims found in the database.")
        return
    try:
        import pandas as pd
        df = pd.DataFrame(results)
        if 'incident_date' in df.columns:
            df['incident_date'] = pd.to_datetime(
                df['incident_date'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
        st.dataframe(df)
    except ImportError:
        st.table(results)


# --- Display Chat History ---
# (Keep this section as it was)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("intent") == "create":
            if "extracted_info" in message and message["extracted_info"]:
                with st.expander("📝 Extracted Info", expanded=False):
                    st.json(message["extracted_info"])
            if "payload" in message and message["payload"]:
                with st.expander("📊 Payload Sent", expanded=False):
                    st.json(message["payload"])
            if "response" in message and message["response"]:
                with st.expander("📄 API Response", expanded=False):
                    st.json(message["response"])
        elif message.get("intent") == "retrieve":
            if "sql_query" in message and message["sql_query"]:
                with st.expander("Generated SQL Query", expanded=True):
                    st.code(message["sql_query"], language="sql")
            if "sql_results" in message:
                with st.expander("💾 Query Results", expanded=True):
                    display_results_as_table(message["sql_results"])
        if "error" in message and message["error"]:
            st.error(message["error"])

# --- Main Processing Logic ---
# Use TypeAdapter for parsing Union types
SQLResponseTypeAdapter = TypeAdapter(SQLResponse)

async def process_input(user_prompt: str):
    intent_info: Optional[Intent] = None
    sql_response: Optional[SQLResponse] = None
    sql_results: Optional[List[Dict[str, Any]]] = None
    extracted_data: Optional[PartialClaim] = None
    extracted_data_dict = None
    full_payload: Optional[ClaimCreate] = None
    full_payload_dict = None
    api_response_dict = None
    error_message = None
    final_content = "Processing..."

    current_assistant_message = {"role": "assistant",
                                 "content": final_content, "intent": None}
    st.session_state.messages.append(current_assistant_message)
    message_placeholder = st.empty()

    try:
        with message_placeholder.chat_message("assistant"):
            with st.status("Processing your request...", expanded=True) as status:
                # 1. Detect Intent
                status.write("🤔 Determining your intent...")
                intent_result = await intent_agent.run(user_prompt)
                raw_intent_output = intent_result.data

                # Parse the data
                if isinstance(raw_intent_output, str):
                    intent_info = Intent.model_validate_json(raw_intent_output)
                elif isinstance(raw_intent_output, dict):
                    intent_info = Intent.model_validate(raw_intent_output)
                elif isinstance(raw_intent_output, Intent):
                    intent_info = raw_intent_output
                else:
                    raise TypeError(
                        f"Unexpected intent output type: {type(raw_intent_output)}")

                current_assistant_message["intent"] = intent_info.action
                status.write(f"✅ Intent detected: **{intent_info.action}**")
                if intent_info.action == "retrieve" and intent_info.query_details:
                    status.write(
                        f"🔍 Retrieval details: {intent_info.query_details}")

                # --- Branch based on Intent ---
                if intent_info.action == "create":
                    status.update(label="Processing claim creation...")
                    # 1a. Extract
                    status.write("🧠 Extracting claim details...")
                    extraction_result = await extraction_agent.run(user_prompt)
                    raw_extract_output = extraction_result.data

                    # Parse the data
                    if isinstance(raw_extract_output, str):
                        extracted_data = PartialClaim.model_validate_json(
                            raw_extract_output)
                    elif isinstance(raw_extract_output, PartialClaim):
                        extracted_data = raw_extract_output
                    else:
                        raise TypeError(
                            f"Unexpected extraction output type: {type(raw_extract_output)}")

                    extracted_data_dict = extracted_data.model_dump(
                        exclude_none=True)
                    status.write(
                        f"📝 Extracted Info: {extracted_data_dict or 'None'}")
                    current_assistant_message["extracted_info"] = extracted_data_dict

                    # 1b. Synthesize
                    status.write("⚙️ Generating test data...")
                    full_payload = synthesize_claim(extracted_data)
                    full_payload_dict = full_payload.model_dump(mode='json')
                    status.write(
                        f"✅ Generated Full Payload: {full_payload_dict}")
                    current_assistant_message["payload"] = full_payload_dict

                    # 1c. Post to API
                    status.write(
                        f"📤 Submitting claim via API to {API_BASE_URL}...")
                    async with httpx.AsyncClient() as client:
                        response = await client.post(f"{API_BASE_URL}/claims/", json=full_payload_dict)
                        if response.status_code == 422:
                            validation_error = HTTPValidationError(
                                **response.json())
                            error_detail = validation_error.model_dump_json(
                                indent=2)
                            raise httpx.HTTPStatusError(
                                f"API Validation Error (422): {error_detail}", request=response.request, response=response)
                        response.raise_for_status()
                        api_response_dict = response.json()
                    status.write(
                        f"✔️ Claim submitted successfully via API! Response: {api_response_dict}")
                    current_assistant_message["response"] = api_response_dict

                    # Parse response and set final message
                    response_claim = Claim(**api_response_dict)
                    final_content = f"Test claim created successfully via API! Claim ID: `{response_claim.id}`."

                elif intent_info.action == "retrieve":
                    status.update(label="Processing claim retrieval...")
                    if not intent_info.query_details:
                        final_content = "Okay, you want to find some claims. Can you be more specific? For example, tell me a claim ID, policy holder name, or status."
                        status.update(label="Need more info",
                                      state="complete", expanded=False)
                        current_assistant_message["content"] = final_content
                        return

                    # 2a. Generate SQL
                    status.write(
                        f"✍️ Generating SQL query for: '{intent_info.query_details}'...")
                    sql_agent_result = await sql_agent.run(intent_info.query_details)
                    raw_sql_output = sql_agent_result.data

                    # Parse the data
                    try:
                        if isinstance(raw_sql_output, str):
                            sql_response = SQLResponseTypeAdapter.validate_json(
                                raw_sql_output)
                        elif isinstance(raw_sql_output, dict):
                            sql_response = SQLResponseTypeAdapter.validate_python(
                                raw_sql_output)
                        elif isinstance(raw_sql_output, (SQLQuery, InvalidSQLRequest)):
                            sql_response = raw_sql_output  # Already parsed
                        else:
                            raise TypeError(
                                f"Unexpected SQL agent output type: {type(raw_sql_output)}")
                    except (PydanticValidationError, json.JSONDecodeError) as parse_error:
                        raise TypeError(
                            "SQL agent returned output that could not be parsed into SQLQuery or InvalidSQLRequest.") from parse_error

                    if isinstance(sql_response, InvalidSQLRequest):
                        status.update(label="SQL Generation Failed",
                                      state="error", expanded=True)
                        final_content = f"Sorry, I couldn't generate a query for that request: {sql_response.error_message}"
                        error_message = final_content
                    elif isinstance(sql_response, SQLQuery):
                        status.write(f"📊 Generated SQL: `{sql_response.sql}`")
                        current_assistant_message["sql_query"] = sql_response.sql

                        # 2b. Validate SQL
                        status.write("🛡️ Validating generated SQL...")
                        plan, explain_error = explain_sql(sql_response.sql)
                        if explain_error:
                            status.update(label="SQL Validation Failed",
                                          state="error", expanded=True)
                            final_content = f"I generated an SQL query, but it failed validation: {explain_error}. Please try rephrasing your request."
                            error_message = final_content
                        else:
                            status.write(
                                f"✅ SQL validation passed (EXPLAIN OK). Plan: {plan}")

                            # 2c. Execute SQL (only if validation passed)
                            status.write(
                                "🔍 Executing query against local database...")
                            sql_results, db_error = execute_sql(
                                sql_response.sql)
                            current_assistant_message["sql_results"] = sql_results

                            if db_error:
                                status.update(
                                    label="SQL Execution Failed", state="error", expanded=True)
                                final_content = f"I generated a valid query, but it failed to execute: {db_error}"
                                error_message = final_content
                            else:
                                status.write(
                                    f"✅ Found {len(sql_results)} matching claim(s).")
                                final_content = f"Okay, I found {len(sql_results)} claim(s) matching your request. See the results below."
                                if sql_response.explanation:
                                    final_content += f"\n\nQuery Explanation: {sql_response.explanation}"

                else:  # Intent is 'unknown'
                    status.update(label="Request unclear",
                                  state="complete", expanded=False)
                    final_content = "I'm not sure how to help with that. I can create test claims or retrieve existing ones. Could you please clarify your request?"

                # Update status to complete if no error occurred earlier
                if not error_message:
                    status.update(label="Processing Complete",
                                  state="complete", expanded=False)

    except httpx.HTTPStatusError as e:
        error_message = f"API Error during claim creation: {e}"
        final_content = "Sorry, there was an error submitting the claim to the API."
        if 'status' in locals():
            status.update(label="API Error", state="error", expanded=True)
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        final_content = "Sorry, an unexpected error occurred while processing your request."
        if 'status' in locals():
            status.update(label="Unexpected Error",
                          state="error", expanded=True)

    finally:
        current_assistant_message["content"] = final_content
        if error_message:
            current_assistant_message["error"] = error_message
        # Rerender the final message bubble
        with message_placeholder.chat_message("assistant"):
            st.markdown(final_content)
            # Display relevant details
            if current_assistant_message.get("intent") == "create":
                if "extracted_info" in current_assistant_message:
                    with st.expander("📝 Extracted Info", expanded=False):
                        st.json(current_assistant_message["extracted_info"])
                if "payload" in current_assistant_message:
                    with st.expander("📊 Payload Sent" + (" (Attempted)" if error_message else ""), expanded=False):
                        st.json(current_assistant_message["payload"])
                if "response" in current_assistant_message:
                    with st.expander("📄 API Response", expanded=False):
                        st.json(current_assistant_message["response"])
            elif current_assistant_message.get("intent") == "retrieve":
                if "sql_query" in current_assistant_message:
                    with st.expander("Generated SQL Query" + (" (Validation Failed)" if error_message and "validation failed" in error_message else ""), expanded=True):
                        st.code(
                            current_assistant_message["sql_query"], language="sql")
                # Show results only if they exist and there wasn't an error during validation/execution specifically for retrieval
                if "sql_results" in current_assistant_message and not (error_message and ("validation failed" in error_message or "failed to execute" in error_message)):
                    with st.expander("💾 Query Results", expanded=True):
                        display_results_as_table(
                            current_assistant_message["sql_results"])
            if error_message:
                st.error(f"Error Details: {error_message}")

# --- Streamlit Input Handling ---
# (Keep this section as it was)
if prompt := st.chat_input("Create a claim or ask to find one..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Run the main processing function
    asyncio.run(process_input(prompt))
    # Rerun to display the latest state and clear the input box
    st.rerun()
