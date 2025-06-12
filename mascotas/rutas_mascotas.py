from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import SessionLocal
from fastapi.responses import FileResponse
from usuario.auth_usuario import get_current_user

from mascotas import modelos_mascotas, schemas_mascotas, crud_mascotas

import json, os, shutil
from datetime import datetime

router = APIRouter()

UPLOAD_DIR = "imagenes"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/mascotas/albergue/{albergue_id}", response_model=list[schemas_mascotas.MascotaResponse])
def obtener_mascotas_por_albergue(albergue_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    if user["rol"] != "albergue" or int(user["sub"]) != albergue_id:
        raise HTTPException(status_code=403, detail="Acceso denegado.")
    
    db_mascotas = db.query(modelos_mascotas.Mascota).filter(modelos_mascotas.Mascota.albergue_id == albergue_id).all()
    resultado = []
    for m in db_mascotas:
        resultado.append(schemas_mascotas.MascotaResponse(
            id=m.id,
            nombre=m.nombre,
            edad=m.edad,
            especie=m.especie,
            genero=m.genero,
            descripcion=m.descripcion,
            albergue_id=m.albergue_id,
            imagen_id=m.imagen_id,
            etiquetas=json.loads(m.etiquetas) if m.etiquetas else [],
            vacunas=json.loads(m.vacunas) if m.vacunas else [],
            created_at=m.created_at.isoformat() if isinstance(m.created_at, datetime) else str(m.created_at),
        ))
    return resultado


@router.get("/mascotas", response_model=list[schemas_mascotas.MascotaResponse], summary="Listar todas las mascotas")
def listar_todas_las_mascotas(db: Session = Depends(get_db)):
    db_mascotas = db.query(modelos_mascotas.Mascota).all()
    resultado = []
    for m in db_mascotas:
        resultado.append(schemas_mascotas.MascotaResponse(
            id=m.id,
            nombre=m.nombre,
            edad=m.edad,
            especie=m.especie,
            genero=m.genero,
            descripcion=m.descripcion,
            albergue_id=m.albergue_id,
            imagen_id=m.imagen_id,
            etiquetas=json.loads(m.etiquetas) if m.etiquetas else [],
            vacunas=json.loads(m.vacunas) if m.vacunas else [],
            created_at=m.created_at.isoformat() if isinstance(m.created_at, datetime) else str(m.created_at),
        ))
    return resultado


@router.get("/mascotas/{mascota_id}", response_model=schemas_mascotas.MascotaResponse)
def obtener_mascota(mascota_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    m = db.query(modelos_mascotas.Mascota).filter(modelos_mascotas.Mascota.id == mascota_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")

    return schemas_mascotas.MascotaResponse(
        id=m.id,
        nombre=m.nombre,
        edad=m.edad,
        especie=m.especie,
        genero=m.genero,
        descripcion=m.descripcion,
        albergue_id=m.albergue_id,
        imagen_id=m.imagen_id,
        etiquetas=json.loads(m.etiquetas) if m.etiquetas else [],
        vacunas=json.loads(m.vacunas) if m.vacunas else [],
        created_at=m.created_at.isoformat() if isinstance(m.created_at, datetime) else str(m.created_at),
    )


@router.post("/mascotas", response_model=schemas_mascotas.MascotaResponse)
def crear_mascota(mascota: schemas_mascotas.MascotaCreate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    if user["rol"] != "albergue":
        raise HTTPException(status_code=403, detail="Solo los albergues pueden registrar mascotas")

    albergue_id = int(user["albergue_id"])
    imagen_obj = db.query(modelos_mascotas.Imagen).filter(modelos_mascotas.Imagen.id == mascota.imagen_id).first()
    if not imagen_obj:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    nueva = crud_mascotas.create_mascota(db, mascota, albergue_id)

    return schemas_mascotas.MascotaResponse(
        id=nueva.id,
        nombre=nueva.nombre,
        edad=nueva.edad,
        especie=nueva.especie,
        genero=nueva.genero,
        descripcion=nueva.descripcion,
        albergue_id=nueva.albergue_id,
        imagen_id=nueva.imagen_id,
        etiquetas=json.loads(nueva.etiquetas) if nueva.etiquetas else [],
        vacunas=json.loads(nueva.vacunas) if nueva.vacunas else [],
        created_at=nueva.created_at.isoformat()
    )


@router.put("/mascotas/{mascota_id}", response_model=schemas_mascotas.MascotaResponse)
def editar_mascota(mascota_id: int, mascota: schemas_mascotas.MascotaUpdate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    if user["rol"] != "albergue":
        raise HTTPException(status_code=403, detail="Solo los albergues pueden editar mascotas")

    db_mascota = db.query(modelos_mascotas.Mascota).filter(modelos_mascotas.Mascota.id == mascota_id).first()
    if not db_mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")

    if db_mascota.albergue_id != int(user["albergue_id"]):
        raise HTTPException(status_code=403, detail="No tiene permiso para editar esta mascota")

    db_mascota.nombre = mascota.nombre if mascota.nombre else db_mascota.nombre
    db_mascota.edad = mascota.edad if mascota.edad else db_mascota.edad
    db_mascota.especie = mascota.especie if mascota.especie else db_mascota.especie
    db_mascota.descripcion = mascota.descripcion if mascota.descripcion else db_mascota.descripcion
    db_mascota.etiquetas = json.dumps(mascota.etiquetas) if mascota.etiquetas else db_mascota.etiquetas
    db_mascota.vacunas = json.dumps(mascota.vacunas) if mascota.vacunas else db_mascota.vacunas

    db.commit()
    db.refresh(db_mascota)

    return schemas_mascotas.MascotaResponse(
        id=db_mascota.id,
        nombre=db_mascota.nombre,
        edad=db_mascota.edad,
        especie=db_mascota.especie,
        genero=db_mascota.genero,
        descripcion=db_mascota.descripcion,
        albergue_id=db_mascota.albergue_id,
        imagen_id=db_mascota.imagen_id,
        etiquetas=json.loads(db_mascota.etiquetas) if db_mascota.etiquetas else [],
        vacunas=json.loads(db_mascota.vacunas) if db_mascota.vacunas else [],
        created_at=db_mascota.created_at.isoformat()
    )


@router.post("/imagenes", response_model=dict)
def subir_imagen(image: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = os.path.join(UPLOAD_DIR, image.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    nueva_imagen = modelos_mascotas.Imagen(ruta=file_path)
    db.add(nueva_imagen)
    db.commit()
    db.refresh(nueva_imagen)
    return {"id": nueva_imagen.id, "ruta": nueva_imagen.ruta}


@router.get("/imagenes/{imagen_id}")
def obtener_imagen(imagen_id: int, db: Session = Depends(get_db)):
    imagen = db.query(modelos_mascotas.Imagen).filter(modelos_mascotas.Imagen.id == imagen_id).first()
    if not imagen:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    file_path = imagen.ruta
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo de imagen no encontrado")

    return FileResponse(file_path)
