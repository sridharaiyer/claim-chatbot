from pydantic import BaseModel
from datetime import datetime


class ClaimBase(BaseModel):
    policy_holder_name: str
    policy_number: str
    vehicle_make: str
    vehicle_model: str
    vehicle_year: int
    incident_date: datetime
    incident_description: str
    adjuster_name: str
    status: str
    company: str
    claim_office: str
    point_of_impact: str


class ClaimCreate(ClaimBase):
    pass


class Claim(ClaimBase):
    id: str  # Changed from int to str to match the model's primary key type

    class Config:
        from_attributes = True
