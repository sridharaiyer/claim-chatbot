# models.py
from typing import Optional, List, Union, Any
from pydantic import BaseModel, Field
from datetime import datetime

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
    id: str = Field(title="Id")  # Added by the API upon creation

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
