from sqlalchemy import Column, Integer, String, DateTime
from .database import Base
import uuid


class Claim(Base):
    __tablename__ = "claims"

    id = Column(String, primary_key=True, index=True, default=lambda: f"CLM-{str(uuid.uuid4().int)[:10]}")
    policy_holder_name = Column(String)
    policy_number = Column(String, unique=True)
    vehicle_make = Column(String)
    vehicle_model = Column(String)
    vehicle_year = Column(Integer)
    incident_date = Column(DateTime)
    incident_description = Column(String)
    adjuster_name = Column(String)
    status = Column(String)
    company = Column(String)
    claim_office = Column(String)
    point_of_impact = Column(String)
