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
from schemas import MessageIn, MessageOut, MascotaResponse, AdoptanteUpdate, MatchTotalSimpleOut, MatchTotalCreate
from datetime import datetime
from models import Mensaje as MensajeModel
from auth import create_access_token
from models import Denegacion, MatchTotal  

router = APIRouter()
models.Base.metadata.create_all(bind=engine)
app = FastAPI()
origins = [
    "*",
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

@app.put(
    "/adoptante/{adoptante_id}",
    response_model=schemas.AdoptanteOut,
    summary="Actualizar datos del adoptante autenticado",
    tags=["Adoptante"],
)
def update_adoptante(
    adoptante_id: int,
    datos: AdoptanteUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # 1) Solo el propio adoptante puede editar su perfil
    if user.get("rol") != "adoptante" or int(user["sub"]) != adoptante_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para editar este perfil")

    # 2) Buscamos al adoptante
    adoptante = db.query(models.Adoptante).filter(models.Adoptante.id == adoptante_id).first()
    if not adoptante:
        raise HTTPException(status_code=404, detail="Adoptante no encontrado")

    # 3) Si se quiere cambiar correo, comprobamos que no exista ya
    if datos.correo and datos.correo != adoptante.correo:
        existe = db.query(models.Adoptante).filter(models.Adoptante.correo == datos.correo).first()
        if existe:
            raise HTTPException(status_code=400, detail="Ya existe un adoptante con ese correo")
        adoptante.correo = datos.correo

    # 4) Actualizamos los campos permitidos si vienen en la petición
    if datos.nombre is not None:
        adoptante.nombre = datos.nombre
    if datos.apellido is not None:
        adoptante.apellido = datos.apellido
    if datos.telefono is not None:
        adoptante.telefono = datos.telefono

    # 5) Guardamos los cambios
    db.commit()
    db.refresh(adoptante)

    # 6) Devolvemos el adoptante actualizado (incluyendo etiquetas/pesos si los tienes)
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
    # 1) Verificar adoptante
    adoptante = db.query(models.Adoptante).get(adoptante_id)
    if not adoptante:
        raise HTTPException(status_code=404, detail="Adoptante no encontrado")

    # 2) IDs de mascotas denegadas por este adoptante
    denegadas = db.query(Denegacion.mascota_id)\
                  .filter(Denegacion.adoptante_id == adoptante_id)\
                  .all()
    denied_ids = {m[0] for m in denegadas}

    # 3) Preparar datos de etiquetas y pesos
    etiquetas_dict = parse_etiquetas_dict(adoptante.etiquetas)
    pesos_dict     = parse_etiquetas_dict(adoptante.pesos)

    # 4) Traer mascotas que NO han sido denegadas
    mascotas_db = db.query(models.Mascota)\
                    .filter(~models.Mascota.id.in_(denied_ids))\
                    .all()
    if not mascotas_db:
        return []

    # 5) Construir lista para cálculos
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

    # 6) Vectorizar y ponderar
    feature_names, vec_adopt, vecs_masc = construir_matriz_tags(etiquetas_dict, lista_mascotas)
    pesos_array = np.ones(len(feature_names), dtype=float)
    for etiqueta, peso in pesos_dict.items():
        if etiqueta in feature_names:
            idx = feature_names.index(etiqueta)
            pesos_array[idx] = float(peso)
    vec_adopt_pond = vec_adopt * pesos_array
    vecs_masc_pond = vecs_masc * pesos_array

    # 7) Calcular similitudes y ordenar
    sims = cosine_similarity([vec_adopt_pond], vecs_masc_pond)[0]
    for i, mascota in enumerate(lista_mascotas):
        mascota["similitud"] = round(float(sims[i]), 4)
    lista_mascotas.sort(key=lambda x: x["similitud"], reverse=True)

    # 8) Recortar a top_n si lo piden
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

@app.get("/matches/adoptante/{adoptante_id}")
def listar_matches_adoptante(adoptante_id: int, db: Session = Depends(get_db)):
    matches = (
        db.query(models.Match)
          .options(joinedload(models.Match.mascota))  # carga la relación mascota
          .filter(models.Match.adoptante_id == adoptante_id)
          .all()
    )
    return [
        {
            "mascota": {
                "id": m.mascota.id,
                "nombre": m.mascota.nombre,
                "imagen_id": m.mascota.imagen_id
            },
            "fecha": m.fecha.isoformat()
        }
        for m in matches
    ]

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

@app.get("/matches/albergue/{albergue_id}")
def listar_matches_albergue(
    albergue_id: int,
    db: Session = Depends(get_db)
):
    if not db.query(models.Albergue).get(albergue_id):
        raise HTTPException(status_code=404, detail="Albergue no encontrado")

    matches = (
        db.query(models.Match)
        .join(models.Mascota, models.Match.mascota)                     # une la mascota
        .options(                                                       # carga relaciones útiles
            joinedload(models.Match.adoptante),
            joinedload(models.Match.mascota)
        )
        .filter(models.Mascota.albergue_id == albergue_id)             # filtro por tu albergue
        .all()
    )

    return [
        {
            "adoptante": {
                "id": m.adoptante.id,
                "nombre": m.adoptante.nombre,
                "imagen_perfil_id": m.adoptante.imagen_perfil_id
            },
            "mascota": {
                "id": m.mascota.id,
                "nombre": m.mascota.nombre,
                "imagen_id": m.mascota.imagen_id
            },
            "fecha": m.fecha.isoformat()
        }
        for m in matches
    ]

@app.get("/adopciones/albergue/{albergue_id}", tags=["Adopciones"])
def listar_adopciones_albergue(
    albergue_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # 1) Solo el albergue dueño puede consultar
    if user["rol"] != "albergue" or int(user["sub"]) != albergue_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    # 2) Verificamos que exista
    if not db.query(models.Albergue).get(albergue_id):
        raise HTTPException(status_code=404, detail="Albergue no encontrado")

    # 3) Hacemos JOIN de Adopcion → Mascota y filtramos por albergue
    adopciones = (
        db.query(models.Adopcion)
          .join(models.Mascota, models.Adopcion.mascota)
          .options(joinedload(models.Adopcion.mascota))
          .filter(models.Mascota.albergue_id == albergue_id)
          .all()
    )

    # 4) Serializamos un JSON sencillo
    return [
        {
            "id": a.id,
            "mascota": {
              "id": a.mascota.id,
              "nombre": a.mascota.nombre,
              "imagen_id": a.mascota.imagen_id
            },
            "adoptante_id": a.adoptante_id,
            "fecha": a.fecha.isoformat()
        }
        for a in adopciones
    ]


@app.post("/donar", tags=["Donaciones"])
def donar(donacion: schemas.DonacionCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    adoptante_id = int(user["sub"])

    # Validación
    mascota = db.query(models.Mascota).filter(models.Mascota.id == donacion.mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada")

    nueva_donacion = models.Donacion(
        adoptante_id=adoptante_id,
        mascota_id=donacion.mascota_id,
        monto=donacion.monto
    )
    db.add(nueva_donacion)
    db.commit()
    db.refresh(nueva_donacion)

    return {"mensaje": "Donación realizada con éxito"}

# -----------------------------------
# Endpoints de Adopciones
# -----------------------------------

@app.post("/matches/{adoptante_id}/{mascota_id}/complete", tags=["Adopciones"])
def endpoint_completar_match(
    adoptante_id: int,
    mascota_id: int,
    db: Session = Depends(get_db)
):
    """
    Marcar un match como completado:
    - Crea un registro en la tabla adopciones
    - Elimina todos los matches pendientes de esa mascota
    """
    try:
        adop = crud.completar_match(db, adoptante_id, mascota_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "mensaje": "Adopción confirmada",
        "adopcion": {
            "id": adop.id,
            "adoptante_id": adop.adoptante_id,
            "mascota_id": adop.mascota_id,
            "fecha": adop.fecha.isoformat()
        }
    }

@app.get("/adopciones/adoptante/{adoptante_id}", tags=["Adopciones"])
def listar_adopciones_adoptante(
    adoptante_id: int,
    db: Session = Depends(get_db)
):
    """
    Lista todas las adopciones de un adoptante
    """
    adopciones = crud.get_adopciones_por_adoptante(db, adoptante_id)
    return [
        {
            "id": a.id,
            "mascota_id": a.mascota_id,
            "fecha": a.fecha.isoformat()
        }
        for a in adopciones
    ]

# -----------------------------------
# Endpoints de Denegaciones
# -----------------------------------

@app.post("/matches/{adoptante_id}/{mascota_id}/deny", tags=["Denegaciones"])
def endpoint_denegar_match(
    adoptante_id: int,
    mascota_id: int,
    db: Session = Depends(get_db)
):
    """
    Registra una denegación y borra el match correspondiente
    """
    try:
        neg = crud.denegar_match(db, adoptante_id, mascota_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "mensaje": "Denegación registrada",
        "denegacion": {
            "id": neg.id,
            "adoptante_id": neg.adoptante_id,
            "mascota_id": neg.mascota_id,
            "fecha": neg.fecha.isoformat()
        }
    }

@app.get("/denegaciones/adoptante/{adoptante_id}", tags=["Denegaciones"])
def listar_denegaciones_adoptante(
    adoptante_id: int,
    db: Session = Depends(get_db)
):
    """
    Lista todas las denegaciones hechas por un adoptante
    """
    denegaciones = crud.get_denegaciones_por_adoptante(db, adoptante_id)
    return [
        {
            "id": d.id,
            "mascota_id": d.mascota_id,
            "fecha": d.fecha.isoformat()
        }
        for d in denegaciones
    ]

# 1) Todos los totales de un albergue
@app.post(
    "/match_totales/",
    response_model=MatchTotalSimpleOut,
    tags=["Match Totales"]
)
def crear_match_total(
    data: MatchTotalCreate,
    db: Session = Depends(get_db)
):
    """
    Crea un registro en la tabla match_totales con los IDs que correspondan.
    """
    nuevo = models.MatchTotal(
        albergue_id=data.albergue_id,
        adoptante_id=data.adoptante_id,
        mascota_id=data.mascota_id,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@app.get(
    "/match_totales/albergue/{albergue_id}",
    response_model=list[schemas.MatchTotalSimpleOut],
    tags=["Match Totales"]
)
def total_matches_por_albergue(
    albergue_id: int,
    db: Session = Depends(get_db)
):
    """
    Devuelve todos los registros de match_totales para un determinado albergue.
    """
    mts = (
        db.query(models.MatchTotal)
          .filter(models.MatchTotal.albergue_id == albergue_id)
          .all()
    )
    return mts

# 2) Por adoptante
@app.get(
    "/match_totales/adoptante/{adoptante_id}",
    response_model=list[MatchTotalSimpleOut],
    tags=["Match Totales"]
)
def total_matches_por_adoptante(adoptante_id: int, db: Session = Depends(get_db)):
    return (
        db.query(MatchTotal)
          .filter(MatchTotal.adoptante_id == adoptante_id)
          .all()
    )

# 3) Por mascota
@app.get(
    "/match_totales/mascota/{mascota_id}",
    response_model=list[MatchTotalSimpleOut],
    tags=["Match Totales"]
)
def total_matches_por_mascota(mascota_id: int, db: Session = Depends(get_db)):
    return (
        db.query(MatchTotal)
          .filter(MatchTotal.mascota_id == mascota_id)
          .all()
    )