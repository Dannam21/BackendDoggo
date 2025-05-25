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
