import shutil, os, json
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime
import models, schemas, crud, auth
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from models import Adoptante, Albergue, Mascota, Imagen

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

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


@app.post("/register/albergue")
def register_albergue(user: schemas.AlbergueCreate, db: Session = Depends(get_db)):
    if crud.get_albergue_by_correo(db, user.correo):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    new_albergue = crud.create_albergue(db, user)
    return {"mensaje": "Albergue registrado con éxito", "id": new_albergue.id}


@app.post("/login/adoptante")
def login_adoptante(user: schemas.AdoptanteLogin, db: Session = Depends(get_db)):
    adopt = db.query(models.Adoptante).filter(models.Adoptante.correo == user.correo).first()
    if not adopt or not crud.verify_password(user.contrasena, adopt.contrasena):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token_data = {"sub": str(adopt.id), "rol": "adoptante"}
    token = auth.create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer"}


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


@app.get("/adoptante/me", response_model=schemas.AdoptanteOut, summary="Obtener datos del adoptante autenticado")
def get_adoptante_me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    adoptante_id = int(user["sub"])
    adoptante_obj = db.query(models.Adoptante).filter(models.Adoptante.id == adoptante_id).first()
    if not adoptante_obj:
        raise HTTPException(status_code=404, detail="Adoptante no encontrado")
    return schemas.AdoptanteOut.from_orm_with_etiquetas(adoptante_obj)


@app.get("/mascotas/albergue/{albergue_id}", response_model=list[schemas.MascotaResponse])
def obtener_mascotas_por_albergue(
    albergue_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    # Solo el albergue dueño puede ver su lista
    if user["rol"] != "albergue" or int(user["sub"]) != albergue_id:
        raise HTTPException(status_code=403, detail="Acceso denegado.")

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
        created_at_str = m.created_at.isoformat() if isinstance(m.created_at, datetime) else str(m.created_at)

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
                created_at=created_at_str,
            )
        )
    return resultado


@app.post("/mascotas", response_model=schemas.MascotaResponse)
def crear_mascota(
    mascota: schemas.MascotaCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
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
        genero=nueva.genero,
        especie=nueva.especie,
        descripcion=nueva.descripcion,
        albergue_id=nueva.albergue_id,
        imagen_id=nueva.imagen_id,
        etiquetas=lista_etqs,
        created_at=nueva.created_at.isoformat(),
    )


@app.put("/mascotas/{mascota_id}", response_model=schemas.MascotaResponse)
def editar_mascota(
    mascota_id: int,
    mascota: schemas.MascotaUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    # Solo los albergues pueden editar mascotas
    if user["rol"] != "albergue":
        raise HTTPException(status_code=403, detail="Solo los albergues pueden editar mascotas")

    # Verificamos si la mascota existe
    db_mascota = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    if not db_mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")

    # Verificamos si el albergue que intenta editar es el dueño de la mascota
    if db_mascota.albergue_id != int(user["albergue_id"]):
        raise HTTPException(status_code=403, detail="No tiene permiso para editar esta mascota")

    # Actualizamos los campos de la mascota
    db_mascota.nombre = mascota.nombre if mascota.nombre else db_mascota.nombre
    db_mascota.edad = mascota.edad if mascota.edad else db_mascota.edad
    db_mascota.especie = mascota.especie if mascota.especie else db_mascota.especie
    db_mascota.descripcion = mascota.descripcion if mascota.descripcion else db_mascota.descripcion
    db_mascota.etiquetas = json.dumps(mascota.etiquetas) if mascota.etiquetas else db_mascota.etiquetas

    # Guardamos los cambios
    db.commit()
    db.refresh(db_mascota)

    # Retornamos la mascota actualizada
    return schemas.MascotaResponse(
        id=db_mascota.id,
        nombre=db_mascota.nombre,
        edad=db_mascota.edad,
        genero=db_mascota.genero,
        especie=db_mascota.especie,
        descripcion=db_mascota.descripcion,
        albergue_id=db_mascota.albergue_id,
        imagen_id=db_mascota.imagen_id,
        etiquetas=json.loads(db_mascota.etiquetas) if db_mascota.etiquetas else [],
        created_at=db_mascota.created_at.isoformat(),
    )


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


@app.get("/albergue/me", response_model=schemas.AlbergueOut, summary="Obtener datos del albergue autenticado")
def get_albergue_me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.get("rol") != "albergue":
        raise HTTPException(status_code=403, detail="Solo los albergues pueden acceder a este recurso")

    albergue_id = int(user["albergue_id"])
    albergue_obj = db.query(models.Albergue).filter(models.Albergue.id == albergue_id).first()
    if not albergue_obj:
        raise HTTPException(status_code=404, detail="Albergue no encontrado")

    return schemas.AlbergueOut.from_orm(albergue_obj)

@app.get("/mascotas", response_model=list[schemas.MascotaResponse], summary="Listar todas las mascotas de todos los albergues")
def listar_todas_las_mascotas(db: Session = Depends(get_db)):

    db_mascotas = db.query(models.Mascota).all()
    resultado = []
    for m in db_mascotas:
        lista_etqs = []
        if m.etiquetas:
            try:
                lista_etqs = json.loads(m.etiquetas)
            except Exception:
                lista_etqs = []
        created_at_str = m.created_at.isoformat() if isinstance(m.created_at, datetime) else str(m.created_at)

        resultado.append(
            schemas.MascotaResponse(
                id=m.id,
                nombre=m.nombre,
                edad=m.edad,
                especie=m.especie,
                genero=m.genero,
                descripcion=m.descripcion,
                albergue_id=m.albergue_id,
                imagen_id=m.imagen_id,
                etiquetas=lista_etqs,
                created_at=created_at_str,
            )
        )
    return resultado

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

def construir_matriz_tags(
    adoptante_tags: List[str],
    mascotas: List[Dict],
) -> Tuple[MultiLabelBinarizer, np.ndarray, np.ndarray]:

    listado_conjuntos = [adoptante_tags] + [m["tags"] for m in mascotas]
    mlb = MultiLabelBinarizer()
    mlb.fit(listado_conjuntos)

    vector_adoptante = mlb.transform([adoptante_tags])[0]         
    vectores_mascotas = mlb.transform([m["tags"] for m in mascotas])  

    return mlb, vector_adoptante, vectores_mascotas


def calcular_similitudes(
    vector_adoptante: np.ndarray,
    vectores_mascotas: np.ndarray,
) -> List[float]:
    sims = cosine_similarity([vector_adoptante], vectores_mascotas)[0]
    return [float(s) for s in sims]

from schemas import MascotaResponse
@app.get("/mascotas/{mascota_id}", response_model=MascotaResponse)
def obtener_mascota_por_id(mascota_id: int, db: Session = Depends(get_db)):
    mascota = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")

    if isinstance(mascota.etiquetas, str):
        mascota.etiquetas = json.loads(mascota.etiquetas)

    mascota.created_at = mascota.created_at.isoformat()

    return mascota


@app.get("/recomendaciones/{adoptante_id}")
def obtener_recomendaciones(
    adoptante_id: int,
    top_n: int = 0,
    db: Session = Depends(get_db),
):
    # 1) Buscamos adoptante
    adoptante = db.query(models.Adoptante).filter(models.Adoptante.id == adoptante_id).first()
    if not adoptante:
        raise HTTPException(status_code=404, detail="Adoptante no encontrado")

    # 2) Parseamos tags del adoptante
    adoptante_tags = parsear_etiquetas(adoptante.etiquetas)

    # 3) Obtenemos todas las mascotas
    mascotas_db = db.query(models.Mascota).all()
    if not mascotas_db:
        return []  # Si no hay mascotas, devolvemos lista vacía

    # 4) Construimos lista de dicts de mascotas
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

    # 5) Vectorizamos y calculamos similitudes
    _, vector_adopt, vectores_m = construir_matriz_tags(adoptante_tags, lista_mascotas)
    sims = calcular_similitudes(vector_adopt, vectores_m)

    # 6) Adjuntamos la similitud a cada dict de mascota, ordenamos y recortamos si hace falta
    for idx, mascota in enumerate(lista_mascotas):
        mascota["similitud"] = round(sims[idx], 4)

    lista_mascotas.sort(key=lambda x: x["similitud"], reverse=True)

    if top_n and top_n > 0:
        lista_mascotas = lista_mascotas[:top_n]

    # 7) Devolvemos la lista como JSON
    return lista_mascotas


# === Rutas adicionales (preguntas y respuestas de ejemplo) ===
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
    user = Depends(get_current_user)
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
