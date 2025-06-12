from sqlalchemy.orm import Session # type: ignore

from mascotas import modelos_mascotas, schemas_mascotas
from passlib.hash import bcrypt # type: ignore
import json
import pytz # type: ignore
from datetime import datetime 



def create_mascota(db: Session, mascota: schemas_mascotas.MascotaCreate, albergue_id: int):
    lima_tz = pytz.timezone("America/Lima")
    ahora_lima = datetime.now(lima_tz)

    nueva = modelos_mascotas.Mascota(
        nombre=mascota.nombre,
        edad=mascota.edad,
        especie=mascota.especie,
        descripcion=mascota.descripcion,
        imagen_id=mascota.imagen_id,
        etiquetas=json.dumps(mascota.etiquetas),
        albergue_id=albergue_id,
        created_at=ahora_lima, 
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

def get_all_mascotas(db: Session):
    return db.query(modelos_mascotas.Mascota).all()

def get_mascotas_por_albergue(db: Session, albergue_id: int):
    return db.query(modelos_mascotas.Mascota).filter(modelos_mascotas.Mascota.albergue_id == albergue_id).all()









