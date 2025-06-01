from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from typing import List
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal, engine
import models, schemas, crud, auth
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
import shutil
from models import Imagen
from models import Mascota
from schemas import MascotaCreate
from fastapi.responses import FileResponse


models.Base.metadata.create_all(bind=engine)
app = FastAPI()

# === CONFIGURACIÓN DE CORS ===
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Puedes usar ["*"] para pruebas si quieres permitir todo
    allow_credentials=True,
    allow_methods=["*"],    # O ["GET", "POST"] si prefieres restringir
    allow_headers=["*"],
)

# === DEPENDENCIAS ===
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # solo se usa para extraer el token

@app.get("/")
def root():
    return {"message": "Bienvenido a la API de Doggo"}

# === REGISTRO DE USUARIOS ===
@app.post("/register/adoptante")
def register_adoptante(user: schemas.AdoptanteRegister, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, user.correo):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    user_id = crud.create_user(db, user.correo, user.contrasena)
    adoptante = crud.create_adoptante(db, user_id, user)
    return {"mensaje": "Adoptante registrado con éxito"}

@app.post("/register/albergue")
def register_albergue(user: schemas.AlbergueRegister, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, user.correo):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    user_id = crud.create_user(db, user.correo, user.contrasena)
    albergue = crud.create_albergue(db, user_id, user)
    return {"mensaje": "Albergue registrado con éxito"}

# === LOGIN ===


@app.post("/login/adoptante")
def login_adoptante(user: schemas.AdoptanteLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, user.correo)
    if not db_user or not crud.verify_password(user.contrasena, db_user.contrasena):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    adoptante = db.query(models.Adoptante).filter(models.Adoptante.id == db_user.id).first()
    if not adoptante:
        raise HTTPException(status_code=403, detail="El usuario no es un adoptante")

    token_data = {"sub": str(db_user.id), "rol": "adoptante"}
    token = auth.create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/login/albergue")
def login_albergue(user: schemas.AlbergueLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, user.correo)
    if not db_user or not crud.verify_password(user.contrasena, db_user.contrasena):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    albergue = db.query(models.Albergue).filter(
        models.Albergue.id == db_user.id,
        models.Albergue.ruc == user.ruc
    ).first()

    if not albergue:
        raise HTTPException(status_code=403, detail="No es un albergue o RUC incorrecto")

    token_data = {"sub": str(db_user.id), "rol": "albergue", "albergue_id": albergue.id}  # incluir albergue_id
    token = auth.create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer", "albergue_id": albergue.id}  # retornamos el albergue_id


# @app.post("/login/albergue")
# def login_albergue(user: schemas.AlbergueLogin, db: Session = Depends(get_db)):
#     db_user = crud.get_user_by_email(db, user.correo)
#     if not db_user or not crud.verify_password(user.contrasena, db_user.contrasena):
#         raise HTTPException(status_code=401, detail="Credenciales incorrectas")

#     albergue = db.query(models.Albergue).filter(
#         models.Albergue.id == db_user.id,
#         models.Albergue.ruc == user.ruc
#     ).first()

#     if not albergue:
#         raise HTTPException(status_code=403, detail="No es un albergue o RUC incorrecto")

#     token_data = {"sub": str(db_user.id), "rol": "albergue"}
#     token = auth.create_access_token(token_data)
#     return {"access_token": token, "token_type": "bearer"}

# === DEPENDENCIA PARA OBTENER USUARIO DESDE TOKEN ===
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = auth.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    return payload

# === ENDPOINTS PROTEGIDOS ===
@app.get("/mascotas")
def obtener_mascotas(db: Session = Depends(get_db), user=Depends(get_current_user)):
    mascotas = db.query(models.Mascota).all()
    return mascotas




@app.post("/mascotas")
def agregar_mascota(
    mascota: MascotaCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user["rol"] != "albergue":
        raise HTTPException(status_code=403, detail="Solo los albergues pueden registrar mascotas")
    
    # Verificar si la imagen existe en la base de datos
    imagen = db.query(Imagen).filter(Imagen.id == mascota.imagen_id).first()
    
    if not imagen:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    # Crear la nueva mascota y asociarla con la imagen
    nueva_mascota = Mascota(
        nombre=mascota.nombre,
        edad=mascota.edad,
        especie=mascota.especie,
        descripcion=mascota.descripcion,
        imagen_id=mascota.imagen_id,  # Asociamos el ID de la imagen
        albergue_id=int(user["sub"]),  # Asociamos al albergue
    )

    db.add(nueva_mascota)
    db.commit()
    db.refresh(nueva_mascota)

    return nueva_mascota



@app.get("/mascotas/albergue/{albergue_id}", response_model=list[schemas.MascotaResponse])
def obtener_mascotas_por_albergue(albergue_id: int, db: Session = Depends(get_db)):
    return crud.get_mascotas_por_albergue(db, albergue_id)


# === PREGUNTAS ===

@app.post("/preguntas", response_model=schemas.PreguntaOut)
def crear_pregunta(pregunta: schemas.PreguntaCreate, db: Session = Depends(get_db)):
    return crud.create_pregunta(db, pregunta)

@app.get("/preguntas", response_model=List[schemas.PreguntaOut])
def listar_preguntas(db: Session = Depends(get_db)):
    return db.query(models.Pregunta).all()

@app.post("/respuestas", response_model=schemas.RespuestaOut)
def crear_respuesta(respuesta: schemas.RespuestaCreate, db: Session = Depends(get_db)):
    db_respuesta = models.Respuesta(
        pregunta_id=respuesta.pregunta_id,
        valor=respuesta.valor
    )
    db.add(db_respuesta)
    db.commit()
    db.refresh(db_respuesta)
    return db_respuesta



@app.get("/respuestas/{pregunta_id}", response_model=List[schemas.RespuestaOut])
def listar_respuestas_posibles(pregunta_id: int, db: Session = Depends(get_db)):
    return db.query(models.Respuesta).filter(models.Respuesta.pregunta_id == pregunta_id).all()


@app.post("/respuestas_usuario")
def guardar_respuestas_usuario(
    respuestas: List[schemas.RespuestaUsuarioCreate], 
    db: Session = Depends(get_db), 
    user=Depends(get_current_user)
):
    adoptante_id = user["sub"]
    for r in respuestas:
        db_respuesta = models.RespuestaUsuario(
            adoptante_id=adoptante_id,
            pregunta_id=r.pregunta_id,
            respuesta_id=r.respuesta_id,
        )
        db.add(db_respuesta)
    db.commit()
    return {"message": "Respuestas guardadas"}

@app.get("/matches")
def obtener_matches_usuario(db: Session = Depends(get_db), user=Depends(get_current_user)):
    from crud import obtener_matches
    ids = obtener_matches(db, user.id)
    return [crud.get_user_by_id(db, id) for id in ids]






UPLOAD_DIR = "imagenes"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/imagenes", response_model=dict)
def subir_imagen(image: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = os.path.join(UPLOAD_DIR, image.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    nueva_imagen = Imagen(ruta=file_path)
    db.add(nueva_imagen)
    db.commit()
    db.refresh(nueva_imagen)

    return {"id": nueva_imagen.id, "ruta": nueva_imagen.ruta}


@app.get("/imagenes/{imagen_id}")
def obtener_imagen(imagen_id: int, db: Session = Depends(get_db)):
    # Buscar la imagen en la base de datos
    imagen = db.query(Imagen).filter(Imagen.id == imagen_id).first()

    if not imagen:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    
    # Asegurarse de que el archivo existe en el sistema
    file_path = imagen.ruta
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo de imagen no encontrado")

    # Devolver el archivo de imagen
    return FileResponse(file_path)
