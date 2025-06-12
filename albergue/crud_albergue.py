from sqlalchemy.orm import Session # type: ignore

from albergue import modelos_albergue, schemas_albergue, modelos_albergue
from passlib.hash import bcrypt # type: ignore
import pytz # type: ignore
from datetime import datetime 
from albergue import crud_albergue


# === ALBERGUE ===
def create_albergue(db: Session, albergue: schemas_albergue.AlbergueRegister):
    hashed_pw = bcrypt.hash(albergue.contrasena)
    db_albergue = modelos_albergue.Albergue(
        nombre=albergue.nombre,
        ruc=albergue.ruc,
        correo=albergue.correo,
        contrasena=hashed_pw,
        telefono=albergue.telefono,
    )
    db.add(db_albergue)
    db.commit()
    db.refresh(db_albergue)
    return db_albergue


def get_albergue_by_correo(db: Session, correo: str):
    return db.query(modelos_albergue.Albergue).filter(modelos_albergue.Albergue.correo == correo).first()

def get_albergue_by_ruc(db: Session, ruc: str):
    return db.query(modelos_albergue.Albergue).filter(modelos_albergue.Albergue.ruc == ruc).first()

def encrypt_password(plain_password: str) -> str:
    return bcrypt.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.verify(plain_password, hashed_password)
