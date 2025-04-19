# extraction_agent.py
from pydantic_ai import Agent
from models import PartialClaim
import os
from dotenv import load_dotenv

# Configure the agent for extraction
# Use a capable model like GPT-4 or Claude 3.5 Sonnet for better extraction

# Example model, can be replaced with any other supported model
GPT4_MODEL = "openai:gpt-4.1-nano"

# Load environment variables from a .env file if it exists
load_dotenv()

# Get the OpenAI API key from the environment or global variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or globals().get("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise EnvironmentError(
        "OPENAI_API_KEY is not set. Please set it as a global variable or in the .env file.")

# Corrected: Use generic type parameter for output_type
extraction_agent = Agent[None, PartialClaim](  # Specify None for DepsT, PartialClaim for OutputT
    # model='openai:gpt-4o', # Or 'anthropic:claude-3-5-sonnet-latest' etc.
    # Set default, but allow override via env var
    model=os.getenv("PYDANTIC_AI_EXTRACTION_MODEL", GPT4_MODEL),
    # output_type=PartialClaim, # REMOVED: This was causing the TypeError
    system_prompt="""
    You are an AI assistant helping to extract information for an auto insurance claim.
    Analyze the user's message and extract ONLY the details they explicitly mention regarding the claim.
    Extract details like:
    - policy_holder_name
    - policy_number
    - vehicle_make, vehicle_model, vehicle_year
    - incident_date (infer datetime for relative terms like 'yesterday'/'this morning' within the last 24 hours; assume 2025 for partial dates like 'January 15th')
    - incident_description
    - adjuster_name
    - status
    - company
    - claim_office
    - point_of_impact (e.g., 'front bumper', 'driver side door')

    Use the provided 'PartialClaim' schema for the output.
    Do NOT invent or fill in any details that are not present in the user's text. Output null or omit fields that are not mentioned.

    Example 1:
    User: I wrecked my car this morning by hitting a tree, damaged the front bumper.
    Output: {"incident_description": "Hit a tree this morning", "point_of_impact": "front bumper"}

    Example 2:
    User: Hi, I’m Mark Rivera. My 2019 Chevy Malibu got rear-ended yesterday. The damage is to the back.
    Output: {"policy_holder_name": "Mark Rivera", "vehicle_make": "Chevrolet", "vehicle_model": "Malibu", "vehicle_year": 2019, "incident_description": "Rear-ended yesterday", "point_of_impact": "back"}

    Example 3:
    User: Someone scratched the front passenger side door in the parking lot. I didn’t see who did it. The car is a 2022 Honda Civic.
    Output: {"vehicle_make": "Honda", "vehicle_model": "Civic", "vehicle_year": 2022, "incident_description": "Scratched in the parking lot. Didn't see who did it", "point_of_impact": "front passenger side door"}
    """,
    instrument=True  # Optional: Enable Logfire tracing if configured
)
