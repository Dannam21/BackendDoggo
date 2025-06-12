from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi import File, UploadFile
from fastapi.responses import FileResponse

import json
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime

from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity

from database import SessionLocal
from usuario.auth_usuario import get_current_user
from usuario import modelos_usuario
from mascotas import crud_mascotas, modelos_mascotas
from mascotas.schemas_mascotas import MascotaResponse
from match import schemas_match, modelos_match


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def parsear_etiquetas(texto: str) -> List[str]:
    if not texto:
        return []
    try:
        lista = json.loads(texto)
        if isinstance(lista, list):
            return [str(tag).strip() for tag in lista]
    except Exception:
        pass
    return [tag.strip() for tag in texto.split(",") if tag.strip()]


def construir_matriz_tags(adoptante_tags: List[str], mascotas: List[Dict]) -> Tuple[MultiLabelBinarizer, np.ndarray, np.ndarray]:
    listado_conjuntos = [adoptante_tags] + [m["tags"] for m in mascotas]
    mlb = MultiLabelBinarizer()
    mlb.fit(listado_conjuntos)

    vector_adoptante = mlb.transform([adoptante_tags])[0]
    vectores_mascotas = mlb.transform([m["tags"] for m in mascotas])

    return mlb, vector_adoptante, vectores_mascotas


def calcular_similitudes(vector_adoptante: np.ndarray, vectores_mascotas: np.ndarray) -> List[float]:
    sims = cosine_similarity([vector_adoptante], vectores_mascotas)[0]
    return [float(s) for s in sims]


@router.get("/usuario/mascotas/{mascota_id}", response_model=MascotaResponse)
def obtener_mascota_por_id(mascota_id: int, db: Session = Depends(get_db)):
    mascota = db.query(modelos_mascotas.Mascota).filter(modelos_mascotas.Mascota.id == mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")

    if isinstance(mascota.etiquetas, str):
        mascota.etiquetas = json.loads(mascota.etiquetas)
    if isinstance(mascota.vacunas, str):
        mascota.vacunas = json.loads(mascota.vacunas)

    mascota.created_at = mascota.created_at.isoformat()
    return mascota


@router.get("/recomendaciones/{adoptante_id}")
def obtener_recomendaciones(adoptante_id: int, top_n: int = 0, db: Session = Depends(get_db)):
    adoptante = db.query(modelos_usuario.Adoptante).filter(modelos_usuario.Adoptante.id == adoptante_id).first()
    if not adoptante:
        raise HTTPException(status_code=404, detail="Adoptante no encontrado")

    adoptante_tags = parsear_etiquetas(adoptante.etiquetas)
    mascotas_db = db.query(modelos_mascotas.Mascota).all()
    if not mascotas_db:
        return []

    lista_mascotas = []
    for m in mascotas_db:
        tags_m = parsear_etiquetas(m.etiquetas)
        lista_mascotas.append({
            "id": m.id,
            "nombre": m.nombre,
            "especie": m.especie,
            "edad": m.edad,
            "descripcion": m.descripcion,
            "albergue_id": m.albergue_id,
            "imagen_id": m.imagen_id,
            "tags": tags_m,
        })

    _, vector_adopt, vectores_m = construir_matriz_tags(adoptante_tags, lista_mascotas)
    sims = calcular_similitudes(vector_adopt, vectores_m)

    for idx, mascota in enumerate(lista_mascotas):
        mascota["similitud"] = round(sims[idx], 4)

    lista_mascotas.sort(key=lambda x: x["similitud"], reverse=True)
    if top_n and top_n > 0:
        lista_mascotas = lista_mascotas[:top_n]

    return lista_mascotas


@router.post("/preguntas", response_model=schemas_match.PreguntaOut)
def crear_pregunta(pregunta: schemas_match.PreguntaCreate, db: Session = Depends(get_db)):
    return crud_mascotas.create_pregunta(db, pregunta)


@router.get("/preguntas", response_model=List[schemas_match.PreguntaOut])
def listar_preguntas(db: Session = Depends(get_db)):
    return db.query(modelos_match.Pregunta).all()


@router.post("/respuestas", response_model=schemas_match.RespuestaOut)
def crear_respuesta(respuesta: schemas_match.RespuestaCreate, db: Session = Depends(get_db)):
    db_respuesta = modelos_match.Respuesta(
        pregunta_id=respuesta.pregunta_id,
        valor=respuesta.valor
    )
    db.add(db_respuesta)
    db.commit()
    db.refresh(db_respuesta)
    return db_respuesta


@router.get("/respuestas/{pregunta_id}", response_model=List[schemas_match.RespuestaOut])
def listar_respuestas_posibles(pregunta_id: int, db: Session = Depends(get_db)):
    return db.query(modelos_match.Respuesta).filter(modelos_match.Respuesta.pregunta_id == pregunta_id).all()


@router.post("/respuestas_usuario")
def guardar_respuestas_usuario(
    respuestas: List[schemas_match.RespuestaUsuarioCreate],
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    adoptante_id = int(user["sub"])
    for r in respuestas:
        db_respuesta = modelos_match.RespuestaUsuario(
            adoptante_id=adoptante_id,
            pregunta_id=r.pregunta_id,
            respuesta_id=r.respuesta_id,
        )
        db.add(db_respuesta)
    db.commit()
    return {"message": "Respuestas guardadas"}


@router.get("/matches")
def obtener_matches_usuario(db: Session = Depends(get_db), user=Depends(get_current_user)):
    from mascotas.crud_mascotas import obtener_matches
    ids = obtener_matches(db, int(user["sub"]))
    return [crud_mascotas.get_user_by_id(db, id_) for id_ in ids]
