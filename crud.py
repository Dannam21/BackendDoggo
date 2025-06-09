from sqlalchemy.orm import Session
import models
import schemas
from passlib.hash import bcrypt
import json
import pytz
from datetime import datetime
from models import Mascota
# === ADOPTANTE ===
def create_adoptante(db: Session, adoptante: schemas.AdoptanteRegister):
    hashed_pw = bcrypt.hash(adoptante.contrasena)

    db_adoptante = models.Adoptante(
        nombre=adoptante.nombre,
        apellido=adoptante.apellido,
        dni=adoptante.dni,
        correo=adoptante.correo,
        telefono=getattr(adoptante, "telefono", None),  # si agregaste teléfono
        contrasena=hashed_pw,
        etiquetas=json.dumps(adoptante.etiquetas or [])  # convertimos lista a JSON string
    )
    db.add(db_adoptante)
    db.commit()
    db.refresh(db_adoptante)
    return db_adoptante

# === ALBERGUE ===
def create_albergue(db: Session, albergue: schemas.AlbergueRegister):
    hashed_pw = bcrypt.hash(albergue.contrasena)
    db_albergue = models.Albergue(
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
    return db.query(models.Albergue).filter(models.Albergue.correo == correo).first()

def get_adoptante_by_correo(db: Session, correo: str):
    return db.query(models.Adoptante).filter(models.Adoptante.correo == correo).first()

def get_albergue_by_ruc(db: Session, ruc: str):
    return db.query(models.Albergue).filter(models.Albergue.ruc == ruc).first()

def get_adoptante_by_dni(db: Session, dni: str):
    return db.query(models.Adoptante).filter(models.Adoptante.dni == dni).first()

def encrypt_password(plain_password: str) -> str:
    return bcrypt.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.verify(plain_password, hashed_password)


def create_mascota(db: Session, mascota: schemas.MascotaCreate, albergue_id: int):
    lima_tz = pytz.timezone("America/Lima")
    ahora_lima = datetime.now(lima_tz)

    nueva = models.Mascota(
        nombre=mascota.nombre,
        edad=mascota.edad,
        especie=mascota.especie,
        genero=mascota.genero,  
        descripcion=mascota.descripcion,
        imagen_id=mascota.imagen_id,
        etiquetas=json.dumps(mascota.etiquetas),
        vacunas=json.dumps(mascota.vacunas),  # 👈 Agregado aquí
        albergue_id=albergue_id,
        created_at=ahora_lima, 
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva




def get_all_mascotas(db: Session):
    return db.query(models.Mascota).all()

def get_mascotas_por_albergue(db: Session, albergue_id: int):
    return db.query(models.Mascota).filter(models.Mascota.albergue_id == albergue_id).all()



# === PREGUNTAS ===
from sklearn.neighbors import NearestNeighbors
import numpy as np

def create_pregunta(db: Session, pregunta: schemas.PreguntaCreate):
    db_pregunta = models.Pregunta(texto=pregunta.texto)
    db.add(db_pregunta)
    db.commit()
    db.refresh(db_pregunta)
    return db_pregunta


# == Match == 
def obtener_matches(db: Session, usuario_actual_id: int, k=3):
    # Obtener todos los usuarios que han respondido preguntas
    usuarios = db.query(models.User).all()

    # Filtrar usuarios que tienen respuestas completas
    data = []
    ids = []
    for user in usuarios:
        respuestas = db.query(models.Respuesta).filter_by(user_id=user.id).order_by(models.Respuesta.pregunta_id).all()
        if respuestas:
            vector = [r.valor for r in respuestas]
            if len(vector) == len(db.query(models.Pregunta).all()):
                data.append(vector)
                ids.append(user.id)

    if usuario_actual_id not in ids:
        raise Exception("El usuario actual no tiene respuestas completas")

    # Convertimos a array
    data = np.array(data)

    # Encontramos el índice del usuario actual
    index_usuario = ids.index(usuario_actual_id)

    # Inicializamos el modelo KNN
    knn = NearestNeighbors(n_neighbors=min(k + 1, len(data)), algorithm='auto')  # +1 porque incluirá el mismo usuario
    knn.fit(data)

    distances, indices = knn.kneighbors([data[index_usuario]])

    # Devolvemos los IDs de los usuarios más cercanos (excepto el propio)
    vecinos_ids = [ids[i] for i in indices[0] if ids[i] != usuario_actual_id]

    return vecinos_ids

