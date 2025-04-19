# models.py
from typing import Annotated, Optional, List, Union, Any, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from annotated_types import MinLen  # Import MinLen

# --- API Schema Models ---


class ClaimCreate(BaseModel):
    policy_holder_name: str = Field(title="Policy Holder Name")
    policy_number: str = Field(title="Policy Number")
    vehicle_make: str = Field(title="Vehicle Make")
    vehicle_model: str = Field(title="Vehicle Model")
    vehicle_year: int = Field(title="Vehicle Year")
    incident_date: datetime = Field(title="Incident Date")
    incident_description: str = Field(title="Incident Description")
    adjuster_name: str = Field(title="Adjuster Name")
    status: str = Field(title="Status")
    company: str = Field(title="Company")
    claim_office: str = Field(title="Claim Office")
    point_of_impact: str = Field(title="Point Of Impact")


class Claim(ClaimCreate):
    # This should match the DB schema's primary key type (String)
    id: str = Field(title="Id")

# --- Extraction Model ---


class PartialClaim(BaseModel):
    """Model to hold extracted claim details, all optional."""
    policy_holder_name: Optional[str] = Field(None, title="Policy Holder Name")
    policy_number: Optional[str] = Field(None, title="Policy Number")
    vehicle_make: Optional[str] = Field(None, title="Vehicle Make")
    vehicle_model: Optional[str] = Field(None, title="Vehicle Model")
    vehicle_year: Optional[int] = Field(None, title="Vehicle Year")
    incident_date: Optional[datetime] = Field(None, title="Incident Date")
    incident_description: Optional[str] = Field(
        None, title="Incident Description")
    adjuster_name: Optional[str] = Field(None, title="Adjuster Name")
    status: Optional[str] = Field(None, title="Status")
    company: Optional[str] = Field(None, title="Company")
    claim_office: Optional[str] = Field(None, title="Claim Office")
    point_of_impact: Optional[str] = Field(None, title="Point Of Impact")

# --- API Error Models (from OpenAPI spec) ---


class ValidationError(BaseModel):
    loc: List[Union[str, int]] = Field(title="Location")
    msg: str = Field(title="Message")
    type: str = Field(title="Error Type")


class HTTPValidationError(BaseModel):
    detail: Optional[List[ValidationError]] = Field(None, title="Detail")

# --- Intent Detection Model ---


class Intent(BaseModel):
    action: Literal["create", "retrieve", "unknown"] = Field(
        description="The user's intent: create a new claim, retrieve existing claims, or unknown.")
    query_details: Optional[str] = Field(
        None, description="Specific details mentioned by the user for retrieval (e.g., 'claim ID CLM-123', 'claims for John Doe', 'claims with status Approved'). Null if the intent is 'create' or 'unknown'.")

# --- SQL Generation Models ---


class SQLQuery(BaseModel):
    """Response when SQL could be successfully generated for retrieval."""
    sql: Annotated[str, MinLen(1)] = Field(
        description="The generated SQLite SELECT query.")
    explanation: Optional[str] = Field(
        None, description="Brief explanation of the SQL query generated.")

    @field_validator('sql')
    @classmethod
    def ensure_select_statement(cls, v: str) -> str:
        # Basic check to ensure it's likely a SELECT query
        if not v.strip().upper().startswith('SELECT'):
            raise ValueError('Generated query must be a SELECT statement.')
        # Add more checks if needed (e.g., prevent DELETE/UPDATE/INSERT)
        forbidden_keywords = ["DELETE", "UPDATE",
                              "INSERT", "DROP", "ALTER", "CREATE", "TRUNCATE"]
        if any(keyword in v.upper() for keyword in forbidden_keywords):
            raise ValueError(
                f"Query contains forbidden keywords like {forbidden_keywords}.")
        return v


class InvalidSQLRequest(BaseModel):
    """Response when the user's retrieval request is unclear or lacks info."""
    error_message: str = Field(
        description="Explanation why SQL could not be generated.")


SQLResponse = Union[SQLQuery, InvalidSQLRequest]
