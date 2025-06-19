import shutil, os, json
import numpy as np # type: ignore
from typing import List, Dict, Any, Tuple
from datetime import datetime
import models, schemas, crud, auth
from sqlalchemy.orm import Session # type: ignore
from database import SessionLocal, engine
from fastapi.responses import FileResponse # type: ignore
from fastapi.security import OAuth2PasswordBearer # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from sklearn.preprocessing import MultiLabelBinarizer # type: ignore
from sklearn.metrics.pairwise import cosine_similarity # type: ignore
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, APIRouter, WebSocket # type: ignore
from models import Adoptante, Albergue, Mascota, Imagen
from sqlalchemy.orm import Session
from schemas import MessageIn, MessageOut, MascotaResponse
from datetime import datetime
from models import Mensaje as MensajeModel
from auth import create_access_token

router = APIRouter()
models.Base.metadata.create_all(bind=engine)
app = FastAPI()
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://choice-lion-saving.ngrok-free.app",
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

# ------------------------------------------------
# Sección: Root
# ------------------------------------------------

@app.get("/",tags=["Root"])
def root():
    return {"message": "Bienvenido a la API de Doggo"}

# ------------------------------------------------
# Sección: Adoptante
# ------------------------------------------------

@app.post("/register/adoptante", tags=["Adoptante"])
def register_adoptante(user: schemas.AdoptanteRegister, db: Session = Depends(get_db)):
    if crud.get_adoptante_by_correo(db, user.correo):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    if db.query(models.Adoptante).filter(models.Adoptante.dni == user.dni).first():
        raise HTTPException(status_code=400, detail="El DNI ya está registrado")
    
    if user.imagen_perfil_id:
        imagen = db.query(models.ImagenPerfil).filter(models.ImagenPerfil.id == user.imagen_perfil_id).first()
        if not imagen:
            raise HTTPException(status_code=400, detail="Imagen no encontrada")

    new_adoptante = crud.create_adoptante(db, user)

    token_data = {
        "sub": str(new_adoptante.id),
        "rol": "adoptante"
    }
    access_token = create_access_token(token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "id": new_adoptante.id,
    }

@app.post("/login/adoptante", tags=["Adoptante"])
def login_adoptante(user: schemas.AdoptanteLogin, db: Session = Depends(get_db)):
    adopt = db.query(models.Adoptante).filter(models.Adoptante.correo == user.correo).first()
    if not adopt or not crud.verify_password(user.contrasena, adopt.contrasena):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token_data = {"sub": str(adopt.id), "rol": "adoptante"}
    token = auth.create_access_token(token_data)

    return {
        "access_token": token,
        "token_type": "bearer",
        "id": adopt.id,
    }

@app.get("/adoptante/me", response_model=schemas.AdoptanteOut, summary="Obtener datos del adoptante autenticado", tags=["Adoptante"])
def get_adoptante_me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    adoptante_id = int(user["sub"])
    adoptante_obj = db.query(models.Adoptante).filter(models.Adoptante.id == adoptante_id).first()
    if not adoptante_obj:
        raise HTTPException(status_code=404, detail="Adoptante no encontrado")
    return schemas.AdoptanteOut.from_orm_with_etiquetas(adoptante_obj)

@app.get("/adoptante/{adoptante_id}", response_model=schemas.AdoptanteOut, summary="Obtener adoptante por ID", tags=["Adoptante"])
def get_adoptante_by_id(adoptante_id: int, db: Session = Depends(get_db)):
    adoptante = (
        db.query(models.Adoptante)
        .options(joinedload(models.Adoptante.imagen_perfil))  # Asegura que imagen_perfil esté cargado
        .filter(models.Adoptante.id == adoptante_id)
        .first()
    )
    
    if not adoptante:
        raise HTTPException(status_code=404, detail="Adoptante no encontrado")
    
    return schemas.AdoptanteOut.from_orm_with_etiquetas(adoptante)

# ------------------------------------------------
# Sección: Albergue
# ------------------------------------------------

@app.post("/register/albergue", tags=["Albergue"])
def register_albergue(user: schemas.AlbergueCreate, db: Session = Depends(get_db)):
    if crud.get_albergue_by_correo(db, user.correo):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    new_albergue = crud.create_albergue(db, user)
    return {"mensaje": "Albergue registrado con éxito", "id": new_albergue.id}

@app.post("/login/albergue", tags=["Albergue"])
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

@app.get("/albergue/me", response_model=schemas.AlbergueOut, summary="Obtener datos del albergue autenticado", tags=["Albergue"])
def get_albergue_me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.get("rol") != "albergue":
        raise HTTPException(status_code=403, detail="Solo los albergues pueden acceder a este recurso")

    albergue_id = int(user["albergue_id"])
    albergue_obj = db.query(models.Albergue).filter(models.Albergue.id == albergue_id).first()
    if not albergue_obj:
        raise HTTPException(status_code=404, detail="Albergue no encontrado")

    return schemas.AlbergueOut.from_orm(albergue_obj)

# ------------------------------------------------
# Sección: Mascotas
# ------------------------------------------------

@app.get("/mascotas/albergue/{albergue_id}", response_model=list[schemas.MascotaResponse], tags=["Mascotas"])
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

        lista_vacunas = []
        if m.vacunas:
            try:
                lista_vacunas = json.loads(m.vacunas)
            except Exception:
                lista_vacunas = []

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
                vacunas=lista_vacunas,
                created_at=created_at_str,
            )
        )
    return resultado

@app.post("/mascotas", response_model=schemas.MascotaResponse, tags=["Mascotas"])
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

    lista_vacunas = []
    if nueva.vacunas:
        try:
            lista_vacunas = json.loads(nueva.vacunas)
        except Exception:
            lista_vacunas = []

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
        vacunas=lista_vacunas,
        created_at=nueva.created_at.isoformat(),
    )

@app.put("/mascotas/{mascota_id}", response_model=schemas.MascotaResponse, tags=["Mascotas"])
def editar_mascota(
    mascota_id: int,
    mascota: schemas.MascotaUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    if user["rol"] != "albergue":
        raise HTTPException(status_code=403, detail="Solo los albergues pueden editar mascotas")

    db_mascota = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    if not db_mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")

    if db_mascota.albergue_id != int(user["albergue_id"]):
        raise HTTPException(status_code=403, detail="No tiene permiso para editar esta mascota")

    # Actualizamos campos (si vienen en la solicitud)
    db_mascota.nombre = mascota.nombre if mascota.nombre else db_mascota.nombre
    db_mascota.edad = mascota.edad if mascota.edad else db_mascota.edad
    db_mascota.especie = mascota.especie if mascota.especie else db_mascota.especie
    db_mascota.descripcion = mascota.descripcion if mascota.descripcion else db_mascota.descripcion
    db_mascota.etiquetas = json.dumps(mascota.etiquetas) if mascota.etiquetas else db_mascota.etiquetas
    db_mascota.vacunas = json.dumps(mascota.vacunas) if mascota.vacunas else db_mascota.vacunas

    db.commit()
    db.refresh(db_mascota)

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
        vacunas=json.loads(db_mascota.vacunas) if db_mascota.vacunas else [],  # 👈 agregado aquí
        created_at=db_mascota.created_at.isoformat(),
    )

@app.get("/mascotas", response_model=list[schemas.MascotaResponse], summary="Listar todas las mascotas de todos los albergues", tags=["Mascotas"])
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

        lista_vacunas = []
        if m.vacunas:
            try:
                lista_vacunas = json.loads(m.vacunas)
            except Exception:
                lista_vacunas = []

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
                vacunas=lista_vacunas,
                created_at=created_at_str,
            )
        )
    return resultado

@app.get("/mascotas/{mascota_id}",response_model=schemas.MascotaResponse,summary="Obtener datos de una mascota por su ID", tags=["Mascotas"])
def obtener_mascota(
    mascota_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Opcional: aquí podrías chequear permisos si quieres
    m = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")

    etiquetas = []
    if m.etiquetas:
        try:
            etiquetas = json.loads(m.etiquetas)
        except:
            etiquetas = []

    # Convertir created_at a string ISO (si lo usas en frontend)
    created_at_str = (
        m.created_at.isoformat()
        if isinstance(m.created_at, datetime)
        else str(m.created_at)
    )

    return schemas.MascotaResponse(
        id=m.id,
        nombre=m.nombre,
        edad=m.edad,
        especie=m.especie,
        descripcion=m.descripcion,
        albergue_id=m.albergue_id,
        imagen_id=m.imagen_id,
        etiquetas=etiquetas,
        created_at=created_at_str,
        genero=m.genero,
        vacunas=json.loads(m.vacunas) if m.vacunas else [],
    )

# ------------------------------------------------
# Sección: Imágenes
# ------------------------------------------------

UPLOAD_DIR = "imagenes"
UPLOAD_DIR_PERFILES2 = "imagenes_perfil"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR_PERFILES2, exist_ok=True)

@app.post("/imagenesProfile", response_model=dict, tags=["Imágenes"])
def subir_imagen_profile(image: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = os.path.join(UPLOAD_DIR_PERFILES2, image.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    nueva_imagen = models.ImagenPerfil(ruta=file_path)
    db.add(nueva_imagen)
    db.commit()
    db.refresh(nueva_imagen)
    return {"id": nueva_imagen.id, "ruta": nueva_imagen.ruta}

@app.get("/imagenesProfile/{imagen_id}", tags=["Imágenes"])
def obtener_imagen(imagen_id: int, db: Session = Depends(get_db)):
    imagen = db.query(models.ImagenPerfil).filter(models.ImagenPerfil.id == imagen_id).first()
    if not imagen:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    file_path = imagen.ruta

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo de imagen no encontrado")

    return FileResponse(file_path)

@app.post("/imagenes", response_model=dict, tags=["Imágenes"])
def subir_imagen(image: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = os.path.join(UPLOAD_DIR, image.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    nueva_imagen = models.Imagen(ruta=file_path)
    db.add(nueva_imagen)
    db.commit()
    db.refresh(nueva_imagen)
    return {"id": nueva_imagen.id, "ruta": nueva_imagen.ruta}

@app.get("/imagenes/{imagen_id}", tags=["Imágenes"])
def obtener_imagen(imagen_id: int, db: Session = Depends(get_db)):
    imagen = db.query(models.Imagen).filter(models.Imagen.id == imagen_id).first()
    if not imagen:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    file_path = imagen.ruta

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo de imagen no encontrado")

    return FileResponse(file_path)

# ------------------------------------------------
# Sección: Recomendaciones
# ------------------------------------------------

def parse_etiquetas_dict(etiquetas_json: str) -> Dict[str, Any]:
    try:
        return json.loads(etiquetas_json) if etiquetas_json else {}
    except:
        return {}

def construir_matriz_tags(
    adoptante_tag_dict: Dict[str, Any],
    mascotas: List[Dict[str, Any]],
) -> Tuple[List[str], np.ndarray, np.ndarray]:
    adoptante_tags = []
    for v in adoptante_tag_dict.values():
        if isinstance(v, list):
            adoptante_tags.extend(v)
        elif isinstance(v, str):
            adoptante_tags.append(v)

    lista_tags_mascotas = [m["tags"] for m in mascotas]

    conjuntos = [adoptante_tags] + lista_tags_mascotas

    mlb = MultiLabelBinarizer()
    mlb.fit(conjuntos)

    vector_adoptante = mlb.transform([adoptante_tags])[0]
    vectores_mascotas = mlb.transform(lista_tags_mascotas)

    return mlb.classes_.tolist(), vector_adoptante, vectores_mascotas

@app.get("/recomendaciones/{adoptante_id}", tags=["Recomendaciones"])
def obtener_recomendaciones(
    adoptante_id: int,
    top_n: int = 0,
    db: Session = Depends(get_db),
):
    adoptante = db.query(models.Adoptante).get(adoptante_id)
    if not adoptante:
        raise HTTPException(status_code=404, detail="Adoptante no encontrado")

    etiquetas_dict = parse_etiquetas_dict(adoptante.etiquetas)
    pesos_dict    = parse_etiquetas_dict(adoptante.pesos)

    mascotas_db = db.query(models.Mascota).all()
    if not mascotas_db:
        return []

    lista_mascotas = []
    for m in mascotas_db:
        try:
            tags = json.loads(m.etiquetas) if m.etiquetas else []
        except:
            tags = []
        lista_mascotas.append({
            "id": m.id,
            "nombre": m.nombre,
            "especie": m.especie,
            "edad": m.edad,
            "descripcion": m.descripcion,
            "albergue_id": m.albergue_id,
            "imagen_id": m.imagen_id,
            "tags": tags,
        })

    feature_names, vec_adopt, vecs_masc = construir_matriz_tags(etiquetas_dict, lista_mascotas)

    pesos_array = np.ones(len(feature_names), dtype=float)
    for etiqueta, peso in pesos_dict.items():
        if etiqueta in feature_names:
            idx = feature_names.index(etiqueta)
            pesos_array[idx] = float(peso)

    vec_adopt_pond = vec_adopt * pesos_array
    vecs_masc_pond = vecs_masc * pesos_array

    sims = cosine_similarity([vec_adopt_pond], vecs_masc_pond)[0]

    for i, mascota in enumerate(lista_mascotas):
        mascota["similitud"] = round(float(sims[i]), 4)
    lista_mascotas.sort(key=lambda x: x["similitud"], reverse=True)

    if top_n and top_n > 0:
        lista_mascotas = lista_mascotas[:top_n]

    return lista_mascotas

@app.get("/matches", tags=["Recomendaciones"])
def obtener_matches_usuario(db: Session = Depends(get_db), user=Depends(get_current_user)):
    from crud import obtener_matches
    ids = obtener_matches(db, int(user["sub"]))
    return [crud.get_user_by_id(db, id_) for id_ in ids]

# ------------------------------------------------
# Sección: Mensajes
# ------------------------------------------------

@app.post("/adoptante/mensajes/enviar", response_model=MessageOut, tags=["Mensajes"])
def enviar_mensaje(
    mensaje: MessageIn,
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user)
):
    print("Payload del token:", user_data)  # 👈 Esto es clave
    emisor_id = user_data["sub"]             # 💥 Aquí está el error si no existe
    emisor_tipo = user_data["rol"]

    nuevo_mensaje = MensajeModel(
        emisor_id=emisor_id,
        emisor_tipo=emisor_tipo,
        receptor_id=mensaje.receptor_id,
        receptor_tipo=mensaje.receptor_tipo,
        contenido=mensaje.contenido,
        timestamp=datetime.utcnow()
    )
    db.add(nuevo_mensaje)
    db.commit()
    db.refresh(nuevo_mensaje)
    return nuevo_mensaje

@app.get("/mensajes/conversacion", response_model=List[MessageOut], tags=["Mensajes"])
def obtener_conversacion(id1: int, tipo1: str, id2: int, tipo2: str, db: Session = Depends(get_db)):
    mensajes = db.query(MensajeModel).filter(
    ((MensajeModel.emisor_id == id1) & (MensajeModel.receptor_id == id2) &
     (MensajeModel.emisor_tipo == tipo1) & (MensajeModel.receptor_tipo == tipo2))
    |
    ((MensajeModel.emisor_id == id2) & (MensajeModel.receptor_id == id1) &
     (MensajeModel.emisor_tipo == tipo2) & (MensajeModel.receptor_tipo == tipo1))
    ).order_by(MensajeModel.timestamp).all()
    return mensajes


from typing import Optional

@app.get("/mensajes3/conversacion", response_model=List[MessageOut], tags=["Mensajes"])
def obtener_conversacion(
    id1: int,
    tipo1: str,
    id2: int,
    tipo2: str,
    mascota_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(MensajeModel).filter(
        (
            (MensajeModel.emisor_id == id1) & (MensajeModel.receptor_id == id2) &
            (MensajeModel.emisor_tipo == tipo1) & (MensajeModel.receptor_tipo == tipo2)
        ) |
        (
            (MensajeModel.emisor_id == id2) & (MensajeModel.receptor_id == id1) &
            (MensajeModel.emisor_tipo == tipo2) & (MensajeModel.receptor_tipo == tipo1)
        )
    )

    if mascota_id is not None:
        query = query.filter(MensajeModel.mascota_id == mascota_id)

    mensajes = query.order_by(MensajeModel.timestamp).all()
    return mensajes



from fastapi import WebSocket

@app.websocket("/ws/chat/{user_id}")
async def chat(websocket: WebSocket, user_id: int):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        # Aquí podrías procesar el mensaje, guardarlo y reenviarlo a otros sockets conectados
        await websocket.send_text(f"Mensaje recibido de {user_id}: {data}")

from sqlalchemy.orm import joinedload

@app.get("/albergue/{albergue_id}", response_model=schemas.AlbergueOut, summary="Obtener albergue por ID")
def get_albergue_by_id(albergue_id: int, db: Session = Depends(get_db)):
    albergue = db.query(models.Albergue).filter(models.Albergue.id == albergue_id).first()
    if not albergue:
        raise HTTPException(status_code=404, detail="Albergue no encontrado")
    return albergue

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models import Mensaje, Adoptante, Albergue
from database import get_db


@app.get("/mensajes/contactos", tags=["Mensajes"])
def obtener_contactos_conversados(emisor_id: int, emisor_tipo: str, db: Session = Depends(get_db)):
    mensajes = db.query(Mensaje).filter(
        ((Mensaje.emisor_id == emisor_id) & (Mensaje.emisor_tipo == emisor_tipo)) |
        ((Mensaje.receptor_id == emisor_id) & (Mensaje.receptor_tipo == emisor_tipo))
    ).all()

    contactos = {}
    for msg in mensajes:
        if msg.emisor_id == emisor_id and msg.emisor_tipo == emisor_tipo:
            key = (msg.receptor_id, msg.receptor_tipo)
        else:
            key = (msg.emisor_id, msg.emisor_tipo)
        contactos[key] = True

    resultado = []
    for (id_contacto, tipo_contacto) in contactos:
        if tipo_contacto == "adoptante":
            user = db.query(Adoptante).filter_by(id=id_contacto).first()
        else:
            user = db.query(Albergue).filter_by(id=id_contacto).first()

        if user:
            resultado.append({
                "userId": user.id,
                "userType": tipo_contacto,
                "name": getattr(user, "nombre", "Sin nombre"),
                "avatar": getattr(user, "avatar_url", "https://i.pravatar.cc/150")
            })

    return resultado


@app.get("/mensajes3/contactos", tags=["Mensajes"])
def obtener_contactos_conversados(emisor_id: int, emisor_tipo: str, db: Session = Depends(get_db)):
    mensajes = db.query(Mensaje).filter(
        ((Mensaje.emisor_id == emisor_id) & (Mensaje.emisor_tipo == emisor_tipo)) |
        ((Mensaje.receptor_id == emisor_id) & (Mensaje.receptor_tipo == emisor_tipo))
    ).all()

    contactos = set()  # Usamos un set para evitar duplicados exactos
    resultado = []

    for msg in mensajes:
        if msg.emisor_id == emisor_id and msg.emisor_tipo == emisor_tipo:
            contacto_id = msg.receptor_id
            contacto_tipo = msg.receptor_tipo
        else:
            contacto_id = msg.emisor_id
            contacto_tipo = msg.emisor_tipo

        # Clave única por usuario y mascota
        key = (contacto_id, contacto_tipo, msg.mascota_id)
        if key not in contactos:
            contactos.add(key)

            if contacto_tipo == "adoptante":
                user = db.query(Adoptante).filter_by(id=contacto_id).first()
            else:
                user = db.query(Albergue).filter_by(id=contacto_id).first()

            if user:
                resultado.append({
                    "userId": user.id,
                    "userType": contacto_tipo,
                    "mascota_id": msg.mascota_id,  # 👈 Incluye mascota
                    "name": getattr(user, "nombre", "Sin nombre"),
                    "avatar": getattr(user, "avatar_url", "https://i.pravatar.cc/150")
                })

    return resultado


# chat_ws.py
from fastapi import WebSocket, WebSocketDisconnect, Depends, APIRouter, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Mensaje
from schemas import MessageIn, MessageOut
from datetime import datetime

active_connections = {}

def get_user_key(user_id: int, user_type: str):
    return f"{user_type}:{user_id}"

@app.websocket("/ws/chat/{emisor_tipo}/{emisor_id}")
async def websocket_chat(
    websocket: WebSocket,
    emisor_id: int,
    emisor_tipo: str,
    db: Session = Depends(get_db)
):
    await websocket.accept()

    key = get_user_key(emisor_id, emisor_tipo)
    active_connections[key] = websocket

    try:
        while True:
            data = await websocket.receive_json()

            msg_in = MessageIn(**data)

            # Guardamos el mensaje en la base de datos con mascota_id
            mensaje_db = Mensaje(
                emisor_id=emisor_id,
                emisor_tipo=emisor_tipo,
                receptor_id=msg_in.receptor_id,
                receptor_tipo=msg_in.receptor_tipo,
                contenido=msg_in.contenido,
                mascota_id=msg_in.mascota_id,  # ✅ GUARDAR mascota_id AQUÍ
                timestamp=datetime.utcnow()
            )
            db.add(mensaje_db)
            db.commit()
            db.refresh(mensaje_db)

            # Preparamos la respuesta
            message_out = {
                "emisor_id": emisor_id,
                "emisor_tipo": emisor_tipo,
                "receptor_id": msg_in.receptor_id,
                "receptor_tipo": msg_in.receptor_tipo,
                "contenido": msg_in.contenido,
                "timestamp": mensaje_db.timestamp.isoformat(),
                "mascota_id": msg_in.mascota_id  # ✅ también puedes incluirlo en la respuesta
            }

            # Enviar al receptor si está conectado
            receptor_key = get_user_key(msg_in.receptor_id, msg_in.receptor_tipo)
            if receptor_key in active_connections:
                await active_connections[receptor_key].send_json(message_out)

            # También al emisor (echo)
            await websocket.send_json(message_out)

    except WebSocketDisconnect:
        del active_connections[key]


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import schemas, crud

router = APIRouter(prefix="/calendario", tags=["Calendario"])


@app.post("/calendario/visita", response_model=schemas.CalendarioOut)
def crear_visita(data: schemas.CitaVisitaCreate, db: Session = Depends(get_db)):
    return crud.crear_cita_visita(db, data)


@app.post("/calendario/evento", response_model=schemas.CalendarioOut)
def crear_evento(data: schemas.CitaEventoCreate, db: Session = Depends(get_db)):
    return crud.crear_cita_evento(db, data)


@app.get("/calendario/albergue/{albergue_id}", response_model=list[schemas.CalendarioOut])
def listar_citas_albergue(albergue_id: int, db: Session = Depends(get_db)):
    return crud.obtener_citas_por_albergue(db, albergue_id)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Calendario
from schemas import CalendarioOut
from datetime import datetime, timedelta

@app.get("/calendario/dia/{fecha}", response_model=list[CalendarioOut])
def obtener_citas_por_fecha(fecha: str, db: Session = Depends(get_db)):
    try:
        fecha_inicio = datetime.strptime(fecha, "%Y-%m-%d")
        fecha_fin = fecha_inicio + timedelta(days=1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido (esperado: YYYY-MM-DD)")

    citas = db.query(Calendario).filter(
        Calendario.fecha_hora >= fecha_inicio,
        Calendario.fecha_hora < fecha_fin
    ).all()

    return citas


from schemas import MatchCreate

@app.post("/matches/")
def crear_match(match: MatchCreate, db: Session = Depends(get_db)):
    nuevo_match = models.Match(
        adoptante_id=match.adoptante_id,
        mascota_id=match.mascota_id
    )
    db.add(nuevo_match)
    db.commit()
    db.refresh(nuevo_match)
    return {"mensaje": "Match guardado", "match": nuevo_match}

@app.get("/matches/{adoptante_id}")
def listar_matches(adoptante_id: int, db: Session = Depends(get_db)):
    matches = db.query(models.Match).filter(models.Match.adoptante_id == adoptante_id).all()
    return matches

@app.get("/usuario/mascotas/{mascota_id}", response_model=MascotaResponse)
def obtener_mascota_por_id(mascota_id: int, db: Session = Depends(get_db)):
    mascota = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")

    # Convertir campos string a lista si es necesario
    if isinstance(mascota.etiquetas, str):
        mascota.etiquetas = json.loads(mascota.etiquetas)
    if isinstance(mascota.vacunas, str):
        mascota.vacunas = json.loads(mascota.vacunas)

    # Convertir datetime a string ISO
    mascota.created_at = mascota.created_at.isoformat()

    return mascota


# Asegúrate de tener algo como esto en FastAPI
@app.get("/matches/albergue/{albergue_id}")
def listar_matches_albergue(albergue_id: int, db: Session = Depends(get_db)):
    matches = db.query(models.Match).filter(models.Match.id == albergue_id).all()
    return matches


# main.py (o donde tengas los endpoints de Adoptante)
@app.post("/donar", tags=["Donaciones"])
def donar(donacion: schemas.DonacionCreate2, user=Depends(get_current_user), db: Session = Depends(get_db)):
    adoptante_id = int(user["sub"])

    # Validación
    mascota = db.query(models.Mascota).filter(models.Mascota.id == donacion.mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")

    nueva_donacion = models.Donacion2(
        adoptante_id=adoptante_id,
        mascota_id=donacion.mascota_id,
        monto=donacion.monto
    )
    db.add(nueva_donacion)
    db.commit()
    db.refresh(nueva_donacion)

    return {"mensaje": "Donación realizada con éxito"}





# Agrega estas importaciones al inicio de tu archivo main.py
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from pydantic import BaseModel
from typing import Optional
import os
import mercadopago  # type: ignore # Import MercadoPago SDK

from models import Donacion  # Asegúrate de tener el modelo Donacion definido

# Cargar variables de entorno
# Configurar MercadoPago
MERCADOPAGO_ACCESS_TOKEN =  ""
print("Access Token de MercadoPago:", MERCADOPAGO_ACCESS_TOKEN)  # 💥 Verifica que este token sea correcto
sdk = mercadopago.SDK(MERCADOPAGO_ACCESS_TOKEN)
# ------------------------------------------------
# Modelos Pydantic para Donaciones
# ------------------------------------------------

class DonacionCreate(BaseModel):
    amount: float
    dogId: int
    dogName: str
    description: Optional[str] = None

class DonacionResponse(BaseModel):
    preferenceId: str
    initPoint: str
    externalReference: str

class WebhookData(BaseModel):
    id: str
    live_mode: bool
    type: str
    date_created: str
    application_id: str
    user_id: str
    version: str
    api_version: str
    action: str
    data: dict


# ------------------------------------------------
# Endpoints de Donaciones
# ------------------------------------------------

@app.post("/crear-donacion", response_model=DonacionResponse, tags=["Donaciones"])
def crear_donacion(
    donacion: DonacionCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Crear preferencia de pago para donación"""
    
    # Validaciones
    if donacion.amount < 1:  # Mínimo 1 sol
        raise HTTPException(status_code=400, detail="El monto mínimo es S/ 1.00")
    
    if user["rol"] != "adoptante":
        raise HTTPException(status_code=403, detail="Solo los adoptantes pueden hacer donaciones")
    
    # Verificar que la mascota existe
    mascota = db.query(models.Mascota).filter(models.Mascota.id == donacion.dogId).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")
    
    # Obtener datos del adoptante
    adoptante_id = int(user["sub"])
    adoptante = db.query(models.Adoptante).filter(models.Adoptante.id == adoptante_id).first()
    if not adoptante:
        raise HTTPException(status_code=404, detail="Adoptante no encontrado")
    
    # Generar referencia externa única
    external_reference = f"{adoptante_id}-{donacion.dogId}-{uuid.uuid4().hex[:8]}"
    
    try:
        # Crear preferencia de MercadoPago
        preference_data = {
            "items": [
                {
                    "title": f"Donación para {donacion.dogName}",
                    "quantity": 1,
                    "unit_price": float(donacion.amount),
                    "currency_id": "PEN",
                    "description": donacion.description or f"Donación para ayudar a {donacion.dogName}"
                }
            ],
            "payer": {
                "name": adoptante.nombre,
                "surname": adoptante.apellido,
                "email": adoptante.correo,
                "phone": {
                    "area_code": "51",
                    "number": adoptante.telefono or "999999999"
                },
                "address": {
                    "street_name": "Lima",
                    "street_number": 123,
                    "zip_code": "15001"
                }
            },
            "back_urls": {
                "success": f"{os.getenv('FRONTEND_URL', 'https://choice-lion-saving.ngrok-free.app:5173')}/donacion/exito",
                "failure": f"{os.getenv('FRONTEND_URL', 'https://choice-lion-saving.ngrok-free.app:5173')}/donacion/error",
                "pending": f"{os.getenv('FRONTEND_URL', 'https://choice-lion-saving.ngrok-free.app:5173')}/donacion/pendiente"
            },
            # "auto_return": "approved",
            "external_reference": external_reference,
            "notification_url": f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/webhook/mercadopago",
            "statement_descriptor": "DOGGO DONACION",
            "metadata": {
                "user_id": adoptante_id,
                "mascota_id": donacion.dogId,
                "mascota_nombre": donacion.dogName
            }
        }
        
        # Crear preferencia en MercadoPago
        print("Preference data:", preference_data)
        preference_response = sdk.preference().create(preference_data)
        print("Preference data:", preference_data)

        
        if preference_response["status"] != 201:
            print("Error de MercadoPago:", preference_response["response"])  # 💥 más info aquí
            raise HTTPException(status_code=500, detail="Error al crear preferencia de pago")
        
        preference = preference_response["response"]
        
        # Guardar donación en base de datos
        nueva_donacion = Donacion(
            user_id=adoptante_id,
            mascota_id=donacion.dogId,
            amount=donacion.amount,
            preference_id=preference["id"],
            external_reference=external_reference,
            status="pending"
        )
        
        db.add(nueva_donacion)
        db.commit()
        db.refresh(nueva_donacion)
        
        return DonacionResponse(
            preferenceId=preference["id"],
            initPoint=preference["sandbox_init_point"],
            externalReference=external_reference
        )
        
    except Exception as e:
        db.rollback()
        print(f"Error al crear donación: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/webhook/mercadopago", tags=["Donaciones"])
async def webhook_mercadopago(
    webhook_data: dict,
    db: Session = Depends(get_db)
):
    """Webhook para recibir notificaciones de MercadoPago"""
    
    try:
        # Verificar que es una notificación de pago
        if webhook_data.get("type") != "payment":
            return {"status": "ignored"}
        
        payment_id = webhook_data.get("data", {}).get("id")
        if not payment_id:
            return {"status": "no_payment_id"}
        
        # Obtener información del pago desde MercadoPago
        payment_response = sdk.payment().get(payment_id)
        
        if payment_response["status"] != 200:
            print(f"Error al obtener pago {payment_id}: {payment_response}")
            return {"status": "error"}
        
        payment_data = payment_response["response"]
        external_reference = payment_data.get("external_reference")
        
        if not external_reference:
            print(f"Pago sin referencia externa: {payment_id}")
            return {"status": "no_reference"}
        
        # Buscar donación en base de datos
        donacion = db.query(Donacion).filter(
            Donacion.external_reference == external_reference
        ).first()
        
        if not donacion:
            print(f"Donación no encontrada para referencia: {external_reference}")
            return {"status": "donation_not_found"}
        
        # Actualizar estado de la donación
        donacion.payment_id = payment_id
        donacion.mp_status = payment_data.get("status")
        donacion.mp_status_detail = payment_data.get("status_detail")
        donacion.transaction_amount = payment_data.get("transaction_amount")
        donacion.net_received_amount = payment_data.get("transaction_details", {}).get("net_received_amount")
        donacion.payer_email = payment_data.get("payer", {}).get("email")
        donacion.payment_method_id = payment_data.get("payment_method_id")
        donacion.updated_at = datetime.utcnow()
        
        # Mapear estado de MercadoPago a estado interno
        mp_status = payment_data.get("status")
        if mp_status == "approved":
            donacion.status = "approved"
        elif mp_status == "rejected":
            donacion.status = "rejected"
        elif mp_status == "cancelled":
            donacion.status = "cancelled"
        elif mp_status in ["pending", "in_process"]:
            donacion.status = "pending"
        else:
            donacion.status = "unknown"
        
        # Guardar detalles de comisiones si están disponibles
        if "fee_details" in payment_data:
            donacion.fee_details = json.dumps(payment_data["fee_details"])
        
        db.commit()
        
        # Si el pago fue aprobado, podrías enviar notificaciones
        if mp_status == "approved":
            await enviar_notificacion_donacion_exitosa(donacion, db)
        
        return {"status": "processed"}
        
    except Exception as e:
        print(f"Error en webhook: {str(e)}")
        db.rollback()
        return {"status": "error", "message": str(e)}

@app.get("/donaciones/mis-donaciones", tags=["Donaciones"])
def obtener_mis_donaciones(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Obtener donaciones del usuario autenticado"""
    
    if user["rol"] != "adoptante":
        raise HTTPException(status_code=403, detail="Solo los adoptantes pueden ver sus donaciones")
    
    adoptante_id = int(user["sub"])
    
    donaciones = db.query(Donacion).filter(
        Donacion.user_id == adoptante_id
    ).order_by(Donacion.created_at.desc()).all()
    
    resultado = []
    for donacion in donaciones:
        # Obtener datos de la mascota
        mascota = db.query(models.Mascota).filter(models.Mascota.id == donacion.mascota_id).first()
        
        resultado.append({
            "id": donacion.id,
            "amount": donacion.amount,
            "status": donacion.status,
            "mp_status": donacion.mp_status,
            "payment_id": donacion.payment_id,
            "created_at": donacion.created_at.isoformat(),
            "mascota": {
                "id": mascota.id if mascota else None,
                "nombre": mascota.nombre if mascota else "Mascota no encontrada",
                "imagen_id": mascota.imagen_id if mascota else None
            },
            "transaction_amount": donacion.transaction_amount,
            "net_received_amount": donacion.net_received_amount
        })
    
    return resultado

@app.get("/donaciones/estado/{external_reference}", tags=["Donaciones"])
def consultar_estado_donacion(
    external_reference: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Consultar estado de una donación específica"""
    
    if user["rol"] != "adoptante":
        raise HTTPException(status_code=403, detail="Solo los adoptantes pueden consultar donaciones")
    
    adoptante_id = int(user["sub"])
    
    donacion = db.query(Donacion).filter(
        Donacion.external_reference == external_reference,
        Donacion.user_id == adoptante_id
    ).first()
    
    if not donacion:
        raise HTTPException(status_code=404, detail="Donación no encontrada")
    
    # Obtener datos de la mascota
    mascota = db.query(models.Mascota).filter(models.Mascota.id == donacion.mascota_id).first()
    
    return {
        "id": donacion.id,
        "amount": donacion.amount,
        "status": donacion.status,
        "mp_status": donacion.mp_status,
        "mp_status_detail": donacion.mp_status_detail,
        "payment_id": donacion.payment_id,
        "created_at": donacion.created_at.isoformat(),
        "updated_at": donacion.updated_at.isoformat(),
        "mascota": {
            "id": mascota.id if mascota else None,
            "nombre": mascota.nombre if mascota else "Mascota no encontrada",
            "imagen_id": mascota.imagen_id if mascota else None
        },
        "transaction_amount": donacion.transaction_amount,
        "net_received_amount": donacion.net_received_amount,
        "payer_email": donacion.payer_email,
        "payment_method_id": donacion.payment_method_id
    }

# ------------------------------------------------
# Estadísticas de Donaciones (Para Albergues)
# ------------------------------------------------

@app.get("/albergue/donaciones/estadisticas", tags=["Donaciones"])
def obtener_estadisticas_donaciones(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Obtener estadísticas de donaciones para el albergue"""
    
    if user["rol"] != "albergue":
        raise HTTPException(status_code=403, detail="Solo los albergues pueden ver estadísticas")
    
    albergue_id = int(user["albergue_id"])
    
    # Obtener mascotas del albergue
    mascotas_ids = db.query(models.Mascota.id).filter(
        models.Mascota.albergue_id == albergue_id
    ).all()
    mascota_ids_list = [m[0] for m in mascotas_ids]
    
    if not mascota_ids_list:
        return {
            "total_donaciones": 0,
            "monto_total": 0,
            "donaciones_aprobadas": 0,
            "monto_neto_recibido": 0,
            "donaciones_por_mascota": []
        }
    
    # Estadísticas generales
    donaciones_query = db.query(Donacion).filter(
        Donacion.mascota_id.in_(mascota_ids_list)
    )
    
    total_donaciones = donaciones_query.count()
    donaciones_aprobadas = donaciones_query.filter(Donacion.status == "approved").count()
    
    # Montos
    monto_total = db.query(
        func.sum(Donacion.amount)
    ).filter(
        Donacion.mascota_id.in_(mascota_ids_list)
    ).scalar() or 0
    
    monto_neto = db.query(
        func.sum(Donacion.net_received_amount)
    ).filter(
        Donacion.mascota_id.in_(mascota_ids_list),
        Donacion.status == "approved"
    ).scalar() or 0
    
    # Donaciones por mascota
    donaciones_por_mascota = db.query(
        models.Mascota.id,
        models.Mascota.nombre,
        func.count(Donacion.id).label("total_donaciones"),
        func.sum(Donacion.amount).label("monto_total"),
        func.sum(Donacion.net_received_amount).label("monto_neto")
    ).outerjoin(
        Donacion, models.Mascota.id == Donacion.mascota_id
    ).filter(
        models.Mascota.albergue_id == albergue_id
    ).group_by(
        models.Mascota.id, models.Mascota.nombre
    ).all()
    
    estadisticas_mascotas = []
    for mascota_stat in donaciones_por_mascota:
        estadisticas_mascotas.append({
            "mascota_id": mascota_stat.id,
            "nombre": mascota_stat.nombre,
            "total_donaciones": mascota_stat.total_donaciones or 0,
            "monto_total": float(mascota_stat.monto_total or 0),
            "monto_neto": float(mascota_stat.monto_neto or 0)
        })
    
    return {
        "total_donaciones": total_donaciones,
        "monto_total": float(monto_total),
        "donaciones_aprobadas": donaciones_aprobadas,
        "monto_neto_recibido": float(monto_neto),
        "donaciones_por_mascota": estadisticas_mascotas
    }

# ------------------------------------------------
# Función auxiliar para notificaciones
# ------------------------------------------------

async def enviar_notificacion_donacion_exitosa(donacion: Donacion, db: Session):
    """Enviar notificación cuando una donación es exitosa"""
    try:
        # Obtener datos del adoptante y mascota
        adoptante = db.query(models.Adoptante).filter(models.Adoptante.id == donacion.user_id).first()
        mascota = db.query(models.Mascota).filter(models.Mascota.id == donacion.mascota_id).first()
        
        if adoptante and mascota:
            # Aquí puedes implementar el envío de email, notificación push, etc.
            print(f"✅ Donación exitosa: {adoptante.nombre} donó S/ {donacion.amount} para {mascota.nombre}")
            
            # Ejemplo: enviar email de confirmación
            # await enviar_email_confirmacion(adoptante.correo, donacion, mascota)
            
    except Exception as e:
        print(f"Error enviando notificación: {str(e)}")

# No olvides agregar la importación de func si no la tienes
from sqlalchemy import func