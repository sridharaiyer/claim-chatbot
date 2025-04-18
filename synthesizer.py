# synthesizer.py
import random
from datetime import datetime, timedelta
from faker import Faker
from models import ClaimCreate, PartialClaim

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
]

DEFAULT_DESCRIPTIONS = [
    "Minor collision in parking lot.",
    "Side-swiped while parked on the street.",
    "Hit a pothole causing tire damage.",
    "Hail damage to roof and hood.",
    "Scratched by unknown object.",
]

DEFAULT_IMPACTS = [
    "Front bumper", "Rear bumper", "Driver side door",
    "Passenger side door", "Windshield", "Roof"
]


def generate_policy_number() -> str:
    return f"POL-{random.randint(100000, 999999)}"


def generate_incident_date() -> datetime:
    # Generate a date between Jan 1, 2025 and Mar 31, 2025
    start_date = datetime(2025, 1, 1, 0, 0, 0)
    end_date = datetime(2025, 3, 31, 23, 59, 59)
    delta = end_date - start_date
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start_date + timedelta(seconds=random_seconds)


def generate_vehicle() -> tuple[str, str, int]:
    return random.choice(DEFAULT_VEHICLES)


def synthesize_claim(partial_claim: PartialClaim) -> ClaimCreate:
    """Fills missing fields in a partial claim to create a complete ClaimCreate object."""

    # Synthesize missing basic info
    name = partial_claim.policy_holder_name or fake.name()
    policy_num = partial_claim.policy_number or generate_policy_number()
    make, model, year = generate_vehicle()
    vehicle_make = partial_claim.vehicle_make or make
    vehicle_model = partial_claim.vehicle_model or model
    vehicle_year = partial_claim.vehicle_year or year

    # Synthesize incident details
    inc_date = partial_claim.incident_date or generate_incident_date()
    inc_desc = partial_claim.incident_description or random.choice(
        DEFAULT_DESCRIPTIONS)
    impact = partial_claim.point_of_impact or random.choice(DEFAULT_IMPACTS)

    # Synthesize administrative details
    adjuster = partial_claim.adjuster_name or random.choice(ADJUSTER_NAMES)
    status = partial_claim.status or random.choice(STATUSES)

    # Synthesize company and office, ensuring consistency
    if partial_claim.company and partial_claim.company in COMPANY_OFFICES:
        company = partial_claim.company
        office = partial_claim.claim_office or random.choice(
            COMPANY_OFFICES[company])
        # Validate if provided office belongs to the provided company
        if partial_claim.claim_office and partial_claim.claim_office not in COMPANY_OFFICES[company]:
            # Override if inconsistent
            office = random.choice(COMPANY_OFFICES[company])
    elif partial_claim.company:  # Company provided but not in our list, or office invalid
        company = random.choice(list(COMPANY_OFFICES.keys()))
        office = random.choice(COMPANY_OFFICES[company])
    else:  # Neither company nor office provided
        company = random.choice(list(COMPANY_OFFICES.keys()))
        office = partial_claim.claim_office or random.choice(
            COMPANY_OFFICES[company])
        # Check if provided office matches *any* office for *any* company - less strict
        found_company = False
        if partial_claim.claim_office:
            for comp, offices in COMPANY_OFFICES.items():
                if partial_claim.claim_office in offices:
                    company = comp
                    office = partial_claim.claim_office
                    found_company = True
                    break
        if not found_company and partial_claim.claim_office:  # Office provided but not found
            # Default to random office for random company
            office = random.choice(COMPANY_OFFICES[company])

    # Construct the full claim
    full_claim = ClaimCreate(
        policy_holder_name=name,
        policy_number=policy_num,
        vehicle_make=vehicle_make,
        vehicle_model=vehicle_model,
        vehicle_year=vehicle_year,
        incident_date=inc_date,
        incident_description=inc_desc,
        adjuster_name=adjuster,
        status=status,
        company=company,
        claim_office=office,
        point_of_impact=impact,
    )

    return full_claim
