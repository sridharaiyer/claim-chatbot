# chatbot.py
import streamlit as st
import httpx
import asyncio
from datetime import datetime
import json  # Import json for potential parsing errors
import traceback  # Import traceback

# Make sure these imports work by having the files in the same directory
# or adjusting sys.path if needed.
from models import Claim, ClaimCreate, PartialClaim, HTTPValidationError
from extraction_agent import extraction_agent
from synthesizer import synthesize_claim
from pydantic import ValidationError as PydanticValidationError  # For parsing error

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000"  # Your running API URL

# --- Streamlit App ---

st.set_page_config(page_title="Test Claim Generator Bot", layout="wide")
st.title("🤖 Test Claim Generator Bot")
st.caption(
    "I can help you generate test auto insurance claims. Just tell me about the incident.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant",
            "content": "Hello! How can I help you create a test claim today?"}
    ]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Optionally display payload/response if stored
        if "payload" in message and message["payload"]:
            st.write("📊 Payload Sent:")
            st.json(message["payload"], expanded=False)
        if "response" in message and message["response"]:
            st.write("📄 API Response:")
            st.json(message["response"], expanded=False)
        if "extracted_info" in message and message["extracted_info"]:
            st.write("📝 Extracted Info:")
            st.json(message["extracted_info"], expanded=False)
        if "error" in message and message["error"]:
            st.error(message["error"])


# React to user input
if prompt := st.chat_input("Describe the incident..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # --- Agent Processing ---
    async def process_claim():
        extracted_data_dict = None
        full_payload_dict = None
        api_response_dict = None
        error_message = None
        # Placeholder for assistant message
        current_assistant_message = {"role": "assistant", "content": ""}

        try:
            # Add a placeholder message for the assistant while processing
            st.session_state.messages.append(current_assistant_message)
            # Use an empty container to update the message content later
            message_placeholder = st.empty()
            with message_placeholder.chat_message("assistant"):
                # Wrap processing steps within st.status for better UX
                with st.status("Processing your request...", expanded=True) as status_container:

                    # 1. Extract information using the agent
                    status_container.write("🧠 Understanding your request...")
                    extraction_result = await extraction_agent.run(prompt)

                    raw_output = extraction_result.data  # Get the raw output

                    # --- MANUAL PARSING ---
                    if isinstance(raw_output, str):
                        try:
                            # Attempt to parse the JSON string into the Pydantic model
                            extracted_data = PartialClaim.model_validate_json(
                                raw_output)
                            
                        except (json.JSONDecodeError, PydanticValidationError) as parse_error:
                            # Raise an informative error if parsing fails
                            raise TypeError(
                                "Extraction agent returned a string, but it failed to parse as PartialClaim JSON. "
                                f"Parse Error: {parse_error}. String value: {raw_output!r}"
                            ) from parse_error
                    elif isinstance(raw_output, PartialClaim):
                        # Handle the ideal (but currently not observed) case where it's already parsed
                        extracted_data = raw_output
                    else:
                        # Handle unexpected types
                        raise TypeError(
                            "Extraction agent did not return the expected PartialClaim object or a parsable JSON string. "
                            f"Got type: {type(raw_output)}. Value: {raw_output!r}"
                        )
                    # --- END MANUAL PARSING ---

                    # Verify it's now a PartialClaim
                    extracted_data_dict = extracted_data.model_dump(
                        exclude_none=True)
                    status_container.write(
                        f"📝 Extracted Info: {extracted_data_dict or 'None'}")
                    # Store for display
                    current_assistant_message["extracted_info"] = extracted_data_dict

                    # 2. Synthesize missing information
                    status_container.write("⚙️ Generating test data...")
                    full_payload = synthesize_claim(extracted_data)
                    full_payload_dict = full_payload.model_dump(
                        mode='json')  # mode='json' handles datetime
                    # Keep this print
                    status_container.write(
                        f"✅ Generated Full Payload: {full_payload_dict}")
                    # Store for display
                    current_assistant_message["payload"] = full_payload_dict

                    # 3. Post to API
                    status_container.write(
                        f"📤 Submitting claim to {API_BASE_URL}...")
                    async with httpx.AsyncClient() as client:
                        response = await client.post(f"{API_BASE_URL}/claims/", json=full_payload_dict)
                        # Check for validation errors (422) specifically
                        if response.status_code == 422:
                            try:
                                validation_error_data = response.json()
                                validation_error = HTTPValidationError(
                                    **validation_error_data)
                                error_detail = validation_error.model_dump_json(
                                    indent=2)
                            except Exception:
                                error_detail = response.text
                            raise httpx.HTTPStatusError(
                                f"API Validation Error (422): {error_detail}",
                                request=response.request,
                                response=response,
                            )
                        response.raise_for_status()  # Raise exception for other bad status codes (4xx/5xx)
                        api_response_dict = response.json()
                        status_container.write(
                            f"✔️ Claim submitted successfully! Response: {api_response_dict}")
                        # Store for display
                        current_assistant_message["response"] = api_response_dict

                    # Update status to complete
                    status_container.update(
                        label="Processing Complete!", state="complete", expanded=False)

            # Update the placeholder with the final success message outside the status context
            response_claim = Claim(**api_response_dict)
            success_message = f"Claim created successfully! Claim ID: `{response_claim.id}`. See details below."
            # Update content
            current_assistant_message["content"] = success_message

            # Rerender the final message outside the status
            with message_placeholder.chat_message("assistant"):
                st.markdown(success_message)
                if current_assistant_message.get("extracted_info"):
                    st.write("📝 Extracted Info:")
                    st.json(
                        current_assistant_message["extracted_info"], expanded=False)
                if current_assistant_message.get("payload"):
                    st.write("📊 Payload Sent:")
                    st.json(
                        current_assistant_message["payload"], expanded=False)
                if current_assistant_message.get("response"):
                    st.write("📄 API Response:")
                    st.json(
                        current_assistant_message["response"], expanded=False)

        except httpx.HTTPStatusError as e:
            error_message = f"API Error: {e}"
            print(f"API Error: {error_message}")
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
            print(f"Unexpected Error: {error_message}")
            # Print full traceback for unexpected errors
            print(traceback.format_exc())

        finally:
            # If an error occurred, update the placeholder message with the error
            if error_message:
                # Ensure status container exists before updating if error happened early
                if 'status_container' in locals():
                    status_container.update(
                        label="Error Occurred", state="error", expanded=True)
                current_assistant_message["content"] = "Sorry, I couldn't process your request due to an error."
                current_assistant_message["error"] = error_message
                with message_placeholder.chat_message("assistant"):
                    st.error(current_assistant_message["content"])
                    st.error(f"Details: {error_message}")
                    # Optionally show payload even on error
                    if current_assistant_message.get("payload"):
                        st.write("Payload (Attempted):")
                        st.json(
                            current_assistant_message["payload"], expanded=False)

    # Run the async processing
    asyncio.run(process_claim())

    # No explicit rerun needed usually
    # st.rerun()
