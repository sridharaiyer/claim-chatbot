# synthesizer.py
import random
from datetime import datetime, timedelta
from faker import Faker
from models import ClaimCreate, PartialClaim
from typing import Optional

fake = Faker()

ADJUSTER_NAMES = [
    "Ryan Cooper", "Olivia Harris", "Daniel Brooks", "Chloe Bennett",
    "Ethan Carter", "Mia Foster", "Noah Evans", "Ava Green",
    "Liam Jenkins", "Isabella King"
]

STATUSES = ["Submitted", "Approved", "Rejected", "Repair in Progress"]

COMPANY_OFFICES = {
    "Alpha Insurance": ["Chicago Office", "Los Angeles Office", "New York Office"],
    "Beta Insurance": ["Houston Office", "Miami Office", "Phoenix Office"],
    "Delta Insurance": ["Atlanta Office", "Dallas Office", "San Francisco Office"],
    "Gamma Insurance": ["Boston Office", "Denver Office", "Seattle Office"]
}

DEFAULT_VEHICLES = [
    ("Toyota", "Camry", 2020), 
    ("Honda", "Civic", 2021), 
    ("Ford", "F-150", 2019),
    ("Chevrolet", "Malibu", 2022), 
    ("Nissan", "Altima", 2018), 
    ("BMW", "3 Series", 2020),
    ("Mercedes-Benz", "C-Class", 2021), 
    ("Tesla","Model 3", 2023), ("Subaru", "Outback", 2019)
]

INCIDENT_IMPACT_MAPPING = [
    ("Rear-ended at a traffic signal", "Rear bumper"),
    ("Hit a parked car while reversing", "Rear bumper"),
    ("Backed into a pole", "Rear bumper"),
    ("Minor collision in parking lot, front impact", "Front bumper"),
    ("Hit a deer crossing the road", "Front bumper"),
    ("Collision with debris on highway", "Front bumper/Underbody"),
    ("Side-swiped driver side while parked", "Driver side"),
    ("T-boned on the driver side at intersection", "Driver side"),
    ("Another car merged into driver side lane", "Driver side"),
    ("Side-swiped passenger side", "Passenger side"),
    ("Scraped passenger side against wall", "Passenger side"),
    ("Object fell on roof", "Roof"),
    ("Hail damage", "Roof/Hood/Trunk"),
    ("Windshield cracked by rock from truck", "Windshield"),
    ("Hit a pothole causing tire/wheel damage", "Wheel/Suspension"),
    ("Skidded on ice and hit guardrail", "Front/Side"),
    ("Hydroplaned into a ditch", "Underbody/Side"),
    ("Vandalism - keyed along the side", "Driver side/Passenger side"),
    ("Attempted theft, broken window", "Driver side window/Passenger side window"),
    ("Fender bender in slow traffic", "Front bumper/Rear bumper")
]

DEFAULT_IMPACTS = list(set(item[1] for item in INCIDENT_IMPACT_MAPPING))


def generate_policy_number() -> str:
    return f"POL-{random.randint(100000, 999999)}"


def generate_incident_date() -> datetime:
    start_date = datetime(2025, 1, 1, 0, 0, 0)
    end_date = datetime(2025, 3, 31, 23, 59, 59)
    delta = end_date - start_date
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start_date + timedelta(seconds=random_seconds)


def generate_vehicle() -> tuple[str, str, int]:
    return random.choice(DEFAULT_VEHICLES)


def generate_incident_and_impact() -> tuple[str, str]:
    return random.choice(INCIDENT_IMPACT_MAPPING)


def synthesize_claim(partial_claim: PartialClaim) -> ClaimCreate:
    """Fills missing fields in a partial claim to create a complete ClaimCreate object."""

    name = partial_claim.policy_holder_name or fake.name()
    policy_num = partial_claim.policy_number or generate_policy_number()
    make, model, year = generate_vehicle()
    vehicle_make = partial_claim.vehicle_make or make
    vehicle_model = partial_claim.vehicle_model or model
    vehicle_year = partial_claim.vehicle_year or year

    inc_date = partial_claim.incident_date or generate_incident_date()

    # Synthesize description and impact
    extracted_desc = partial_claim.incident_description
    extracted_impact = partial_claim.point_of_impact  # Check if extracted

    inc_desc: str
    impact: str

    if extracted_desc:
        inc_desc = extracted_desc
        # Prioritize extracted impact, then match description, then fallback
        if extracted_impact:
            impact = extracted_impact
        else:
            # Try to match extracted description to get impact
            matched = False
            for desc_map, impact_map in INCIDENT_IMPACT_MAPPING:
                if desc_map.lower() in inc_desc.lower() or inc_desc.lower() in desc_map.lower():
                    impact = impact_map
                    matched = True
                    break
            if not matched:
                impact = random.choice(DEFAULT_IMPACTS)  # Fallback if no match
    else:
        # If no description extracted, generate both description and a matching impact
        generated_desc, generated_impact = generate_incident_and_impact()
        inc_desc = generated_desc
        # Prioritize extracted impact (unlikely here), then use the generated matching impact
        if extracted_impact:
            impact = extracted_impact
        else:
            impact = generated_impact

    # Synthesize administrative details
    adjuster = partial_claim.adjuster_name or random.choice(ADJUSTER_NAMES)
    status = partial_claim.status or random.choice(STATUSES)

    # Synthesize company and office (logic remains the same)
    company = partial_claim.company
    office = partial_claim.claim_office

    if company and company in COMPANY_OFFICES:
        if not office or office not in COMPANY_OFFICES[company]:
            office = random.choice(COMPANY_OFFICES[company])
    elif company:
        company = random.choice(list(COMPANY_OFFICES.keys()))
        office = random.choice(COMPANY_OFFICES[company])
    else:
        company = random.choice(list(COMPANY_OFFICES.keys()))
        if not office:
            office = random.choice(COMPANY_OFFICES[company])
        else:
            found_company_for_office = False
            for comp, offices in COMPANY_OFFICES.items():
                if office in offices:
                    company = comp
                    found_company_for_office = True
                    break
            if not found_company_for_office:
                office = random.choice(COMPANY_OFFICES[company])

    # Construct the full claim
    full_claim = ClaimCreate(
        policy_holder_name=name, policy_number=policy_num, vehicle_make=vehicle_make,
        vehicle_model=vehicle_model, vehicle_year=vehicle_year, incident_date=inc_date,
        incident_description=inc_desc, adjuster_name=adjuster, status=status,
        company=company, claim_office=office, point_of_impact=impact,  # Use finalized impact
    )
    return full_claim
