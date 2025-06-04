from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil, os
import json
import models, schemas, crud, auth
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

# === CONFIGURACIÓN CORS ===
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === DEPENDENCIAS ===
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = auth.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    return payload

@app.get("/")
def root():
    return {"message": "Bienvenido a la API de Doggo"}

@app.post("/register/adoptante")
def register_adoptante(user: schemas.AdoptanteRegister, db: Session = Depends(get_db)):
    if crud.get_adoptante_by_correo(db, user.correo):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    if db.query(models.Adoptante).filter(models.Adoptante.dni == user.dni).first():
        raise HTTPException(status_code=400, detail="El DNI ya está registrado")

    new_adoptante = crud.create_adoptante(db, user)
    return {"mensaje": "Adoptante registrado con éxito", "id": new_adoptante.id}

# === REGISTRO DE ALBERGUE ===
@app.post("/register/albergue")
def register_albergue(user: schemas.AlbergueCreate, db: Session = Depends(get_db)):
    if crud.get_albergue_by_correo(db, user.correo):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    new_albergue = crud.create_albergue(db, user)
    return {"mensaje": "Albergue registrado con éxito", "id": new_albergue.id}

# === LOGIN ADOPTANTE ===
@app.post("/login/adoptante")
def login_adoptante(user: schemas.AdoptanteLogin, db: Session = Depends(get_db)):
    adopt = db.query(models.Adoptante).filter(models.Adoptante.correo == user.correo).first()
    if not adopt or not crud.verify_password(user.contrasena, adopt.contrasena):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token_data = {"sub": str(adopt.id), "rol": "adoptante"}
    token = auth.create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer"}

# === LOGIN ALBERGUE ===
@app.post("/login/albergue")
def login_albergue(user: schemas.AlbergueLogin, db: Session = Depends(get_db)):
    db_albergue = crud.get_albergue_by_correo(db, user.correo)  
    if not db_albergue or not crud.verify_password(user.contrasena, db_albergue.contrasena):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token_data = {
        "sub": str(db_albergue.id),
        "rol": "albergue",
        "albergue_id": db_albergue.id
    }
    token = auth.create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer", "albergue_id": db_albergue.id}

# === ENDPOINT PROTEGIDO: OBTENER DATOS DEL ADOPTANTE ===
@app.get("/adoptante/me", response_model=schemas.AdoptanteOut, summary="Obtener datos del adoptante autenticado")
def get_adoptante_me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    adoptante_id = int(user["sub"])
    adoptante_obj = db.query(models.Adoptante).filter(models.Adoptante.id == adoptante_id).first()
    if not adoptante_obj:
        raise HTTPException(status_code=404, detail="Adoptante no encontrado")

    return schemas.AdoptanteOut.from_orm_with_etiquetas(adoptante_obj)

@app.get("/mascotas/albergue/{albergue_id}",response_model=list[schemas.MascotaResponse])
def obtener_mascotas_por_albergue(albergue_id: int,db: Session = Depends(get_db),user=Depends(get_current_user),):
    if user["rol"] != "albergue" or int(user["sub"]) != albergue_id:
        raise HTTPException(status_code=403, detail="Acceso denegado. Solo el albergue propietario puede ver sus mascotas.")
    db_mascotas = (
        db.query(models.Mascota)
        .filter(models.Mascota.albergue_id == albergue_id)
        .all()
    )

    resultado = []
    for m in db_mascotas:
        lista_etqs = []
        if m.etiquetas:
            try:
                lista_etqs = json.loads(m.etiquetas)
            except Exception:
                lista_etqs = []
        resultado.append(
            schemas.MascotaResponse(
                id=m.id,
                nombre=m.nombre,
                edad=m.edad,
                especie=m.especie,
                descripcion=m.descripcion,
                albergue_id=m.albergue_id,
                imagen_id=m.imagen_id,
                etiquetas=lista_etqs,
            )
        )
    return resultado

@app.post("/mascotas", response_model=schemas.MascotaResponse)
def crear_mascota( mascota: schemas.MascotaCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user["rol"] != "albergue":
        raise HTTPException(status_code=403, detail="Solo los albergues pueden registrar mascotas")

    albergue_id = int(user["albergue_id"])
    imagen_obj = db.query(models.Imagen).filter(models.Imagen.id == mascota.imagen_id).first()
    if not imagen_obj:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    nueva = crud.create_mascota(db, mascota, albergue_id)

    lista_etqs = []
    if nueva.etiquetas:
        try:
            lista_etqs = json.loads(nueva.etiquetas)
        except Exception:
            lista_etqs = []

    return schemas.MascotaResponse(
        id=nueva.id,
        nombre=nueva.nombre,
        edad=nueva.edad,
        especie=nueva.especie,
        descripcion=nueva.descripcion,
        albergue_id=nueva.albergue_id,
        imagen_id=nueva.imagen_id,
        etiquetas=lista_etqs,
    )
    



# POR VERIFICAR Y CORREGIR

@app.post("/preguntas", response_model=schemas.PreguntaOut)
def crear_pregunta(pregunta: schemas.PreguntaCreate, db: Session = Depends(get_db)):
    return crud.create_pregunta(db, pregunta)

@app.get("/preguntas", response_model=list[schemas.PreguntaOut])
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

@app.get("/respuestas/{pregunta_id}", response_model=list[schemas.RespuestaOut])
def listar_respuestas_posibles(pregunta_id: int, db: Session = Depends(get_db)):
    return db.query(models.Respuesta).filter(models.Respuesta.pregunta_id == pregunta_id).all()

@app.post("/respuestas_usuario")
def guardar_respuestas_usuario(
    respuestas: list[schemas.RespuestaUsuarioCreate],
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    adoptante_id = int(user["sub"])
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
    ids = obtener_matches(db, int(user["sub"]))
    return [crud.get_user_by_id(db, id_) for id_ in ids]

# === UPLOAD DE IMÁGENES ===
UPLOAD_DIR = "imagenes"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/imagenes", response_model=dict)
def subir_imagen(image: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = os.path.join(UPLOAD_DIR, image.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    nueva_imagen = models.Imagen(ruta=file_path)
    db.add(nueva_imagen)
    db.commit()
    db.refresh(nueva_imagen)
    return {"id": nueva_imagen.id, "ruta": nueva_imagen.ruta}

@app.get("/imagenes/{imagen_id}")
def obtener_imagen(imagen_id: int, db: Session = Depends(get_db)):
    imagen = db.query(models.Imagen).filter(models.Imagen.id == imagen_id).first()
    if not imagen:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    file_path = imagen.ruta
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo de imagen no encontrado")
    return FileResponse(file_path)
