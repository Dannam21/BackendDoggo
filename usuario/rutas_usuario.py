import shutil, os, json
import numpy as np  # type: ignore
from typing import List, Dict, Tuple
from datetime import datetime
from sqlalchemy.orm import Session  # type: ignore
from database import SessionLocal
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File  # type: ignore
from fastapi.responses import FileResponse  # type: ignore
from fastapi.security import OAuth2PasswordBearer  # type: ignore
from sklearn.preprocessing import MultiLabelBinarizer  # type: ignore
from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
from usuario import auth_usuario, schemas_usuario, modelos_usuario
from usuario import crud_usuario 
from usuario.crud_usuario import get_adoptante_by_correo

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = auth_usuario.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    return payload

# Login
@router.post("/login/adoptante")
def login_adoptante(user: schemas_usuario.AdoptanteLogin, db: Session = Depends(get_db)):
    adopt = db.query(modelos_usuario.Adoptante).filter(modelos_usuario.Adoptante.correo == user.correo).first()
    if not adopt or not crud_usuario.verify_password(user.contrasena, adopt.contrasena):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token_data = {"sub": str(adopt.id), "rol": "adoptante"}
    token = auth_usuario.create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer"}


from usuario import get_adoptante_by_correo
from usuario.crud_usuario import get_adoptante_by_correo

# Register
@router.post("/register/adoptante")
def register_adoptante(user: schemas_usuario.AdoptanteRegister, db: Session = Depends(get_db)):
    if get_adoptante_by_correo(db, user.correo):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    if db.query(modelos_usuario.Adoptante).filter(modelos_usuario.Adoptante.dni == user.dni).first():
        raise HTTPException(status_code=400, detail="El DNI ya está registrado")

    new_adoptante = crud_usuario.create_adoptante(db, user)
    return {"mensaje": "Adoptante registrado con éxito", "id": new_adoptante.id}

# Obtener perfil del adoptante
@router.get("/adoptante/me", response_model=schemas_usuario.AdoptanteOut, summary="Obtener datos del adoptante autenticado")
def get_adoptante_me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    adoptante_id = int(user["sub"])
    adoptante_obj = db.query(modelos_usuario.Adoptante).filter(modelos_usuario.Adoptante.id == adoptante_id).first()
    if not adoptante_obj:
        raise HTTPException(status_code=404, detail="Adoptante no encontrado")
    return schemas_usuario.AdoptanteOut.from_orm_with_etiquetas(adoptante_obj)
