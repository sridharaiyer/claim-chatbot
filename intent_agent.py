# intent_agent.py
from pydantic_ai import Agent
from models import Intent
import os


GPT4_MODEL = "openai:gpt-4.1-nano"

# Use a model good at classification/intent recognition (often smaller/faster models work well)
intent_agent = Agent[None, Intent](  # No deps needed, outputs Intent model
    model=os.getenv("PYDANTIC_AI_INTENT_MODEL", GPT4_MODEL),  # Cheaper/faster model
    # output_type=Intent, # Defined via generic
    system_prompt="""
    Your task is to determine the user's intent based on their message regarding an auto insurance claim.
    Classify the intent as one of: 'create', 'retrieve', or 'unknown'.

    - 'create': The user wants to report a new incident or start a new claim. Phrases like "I got into an accident", "Someone hit my car", "Need to file a claim".
    - 'retrieve': The user wants to find existing claim information. Phrases like "What's the status of my claim?", "Find claim 123", "Show me claims for John Doe", "List all approved claims".
    - 'unknown': The intent is unclear, conversational, or not related to creating/retrieving claims.

    If the intent is 'retrieve', extract any specific details mentioned for filtering, such as claim ID, policy holder name, status, company, etc., into the 'query_details' field. If no specific details are mentioned for retrieval (e.g., "show me my claims"), 'query_details' should be null.
    If the intent is 'create' or 'unknown', 'query_details' must be null.

    Respond ONLY with the JSON object matching the 'Intent' schema.

    Examples:
    User: I hit a deer this morning.
    Output: {"action": "create", "query_details": null}

    User: Can you find the claim for policy number POL-123456?
    Output: {"action": "retrieve", "query_details": "policy number POL-123456"}

    User: What's the status of claim CLM-9876543210?
    Output: {"action": "retrieve", "query_details": "claim ID CLM-9876543210"}

    User: Show me all claims handled by Ryan Cooper.
    Output: {"action": "retrieve", "query_details": "adjuster Ryan Cooper"}

    User: List claims for Beta Insurance that are in progress.
    Output: {"action": "retrieve", "query_details": "Beta Insurance claims with status Repair in Progress"}

    User: Thanks!
    Output: {"action": "unknown", "query_details": null}

    User: Tell me about my options.
    Output: {"action": "unknown", "query_details": null}
    """,
    instrument=True  # Optional
)
