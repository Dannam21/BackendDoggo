from sqlalchemy.orm import Session
import models
import schemas
from passlib.hash import bcrypt

# === USUARIO BASE ===
def get_user_by_email(db: Session, email: str):
    return db.query(models.Usuario).filter(models.Usuario.correo == email).first()

def create_user(db: Session, correo: str, contrasena: str):
    hashed_pw = bcrypt.hash(contrasena)
    user = models.Usuario(correo=correo, contrasena=hashed_pw)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.id

def verify_password(plain_password, hashed_password):
    return bcrypt.verify(plain_password, hashed_password)

# === ADOPTANTE ===
def create_adoptante(db: Session, user_id: int, adoptante: schemas.AdoptanteCreate):
    print("Registrando adoptante:", adoptante.dict())  # <--- DEBUG

    db_adoptante = models.Adoptante(
        id=user_id,
        nombre=adoptante.nombre,
        apellido=adoptante.apellido,
        dni=adoptante.dni
    )
    db.add(db_adoptante)
    db.commit()
    db.refresh(db_adoptante)
    return db_adoptante

# === ALBERGUE ===
def create_albergue(db: Session, user_id: int, albergue: schemas.AlbergueCreate):
    print("Registrando albergue:", albergue.dict())  # <--- DEBUG
    db_albergue = models.Albergue(
        id=user_id,
        nombre=albergue.nombre,
        ruc=albergue.ruc
    )
    db.add(db_albergue)
    db.commit()
    db.refresh(db_albergue)
    return db_albergue

# === MASCOTAS ===
def get_all_mascotas(db: Session):
    return db.query(models.Mascota).all()

def create_mascota(db: Session, mascota: schemas.MascotaCreate, albergue_id: int):
    db_mascota = models.Mascota(
        nombre=mascota.nombre,
        edad=mascota.edad,
        especie=mascota.especie,
        albergue_id=albergue_id
    )
    db.add(db_mascota)
    db.commit()
    db.refresh(db_mascota)
    return db_mascota
