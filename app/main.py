from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app import models, schemas, crud, database
from sqlalchemy.orm import Session
from fastapi import Depends

app = FastAPI()
database.Base.metadata.create_all(bind=database.engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/claims/", response_model=schemas.Claim)
def create_claim(claim: schemas.ClaimCreate, db: Session = Depends(database.get_db)):
    return crud.create_claim(db=db, claim=claim)


@app.get("/claims/{claim_id}", response_model=schemas.Claim)
def read_claim(claim_id: str, db: Session = Depends(database.get_db)):
    db_claim = crud.get_claim(db, claim_id=claim_id)
    if db_claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return db_claim


@app.get("/claims/", response_model=list[schemas.Claim])
def list_claims(db: Session = Depends(database.get_db)):
    return crud.get_all_claims(db)
