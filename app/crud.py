from sqlalchemy.orm import Session
from . import models, schemas


def create_claim(db: Session, claim: schemas.ClaimCreate):
    db_claim = models.Claim(**claim.model_dump())
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)
    return db_claim


def get_claim(db: Session, claim_id: int):
    return db.query(models.Claim).filter(models.Claim.id == claim_id).first()


def get_all_claims(db: Session):
    return db.query(models.Claim).all()
