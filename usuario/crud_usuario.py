from sqlalchemy.orm import Session # type: ignore
from passlib.hash import bcrypt # type: ignore
import json
import pytz # type: ignore
from datetime import datetime 
import modelos_usuario
import modelos_match# type: ignore
import schemas_match# type: ignore
import schemas_usuario
# === ADOPTANTE ===
def create_adoptante(db: Session, adoptante: schemas_usuario.AdoptanteRegister):
    hashed_pw = bcrypt.hash(adoptante.contrasena)

    db_adoptante = modelos_usuario.Adoptante(
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


def get_adoptante_by_correo(db: Session, correo: str):
    return db.query(modelos_usuario.Adoptante).filter(modelos_usuario.Adoptante.correo == correo).first()

def get_adoptante_by_dni(db: Session, dni: str):
    return db.query(modelos_usuario.Adoptante).filter(modelos_usuario.Adoptante.dni == dni).first()

def encrypt_password(plain_password: str) -> str:
    return bcrypt.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.verify(plain_password, hashed_password)


# === PREGUNTAS ===
from sklearn.neighbors import NearestNeighbors # type: ignore
import numpy as np # type: ignore

def create_pregunta(db: Session, pregunta: schemas_match.PreguntaCreate):
    db_pregunta = modelos_match.Pregunta(texto=pregunta.texto)
    db.add(db_pregunta)
    db.commit()
    db.refresh(db_pregunta)
    return db_pregunta


# == Match == 
def obtener_matches(db: Session, usuario_actual_id: int, k=3):
    # Obtener todos los usuarios que han respondido preguntas
    usuarios = db.query(modelos_usuario.User).all()

    # Filtrar usuarios que tienen respuestas completas
    data = []
    ids = []
    for user in usuarios:
        respuestas = db.query(modelos_match.Respuesta).filter_by(user_id=user.id).order_by(modelos_match.Respuesta.pregunta_id).all()
        if respuestas:
            vector = [r.valor for r in respuestas]
            if len(vector) == len(db.query(modelos_match.Pregunta).all()):
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
