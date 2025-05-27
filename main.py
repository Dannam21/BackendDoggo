from fastapi import FastAPI, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal, engine
import models, schemas, crud, auth

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

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

    token_data = {"sub": str(db_user.id), "rol": "albergue"}
    token = auth.create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer"}

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
def agregar_mascota(mascota: schemas.MascotaCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user["rol"] != "albergue":
        raise HTTPException(status_code=403, detail="Solo los albergues pueden registrar mascotas")
    nueva_mascota = models.Mascota(**mascota.dict(), albergue_id=int(user["sub"]))
    db.add(nueva_mascota)
    db.commit()
    db.refresh(nueva_mascota)
    return nueva_mascota


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

# === DONACIONES ===

@app.post("/donaciones", response_model=schemas.DonacionOut, status_code=status.HTTP_201_CREATED)
def crear_donacion(
    don: schemas.DonacionCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    # Solo adoptantes pueden donar
    if user["rol"] != "adoptante":
        raise HTTPException(status_code=403, detail="Solo los adoptantes pueden hacer donaciones")
    # adoptante_id viene del token
    return crud.create_donacion(db, don, adoptante_id=int(user["sub"]))

@app.get("/donaciones", response_model=List[schemas.DonacionOut])
def listar_donaciones(db: Session = Depends(get_db), user = Depends(get_current_user)):
    # podrías filtrar solo las propias si quisieras
    return crud.get_all_donaciones(db)


# === ETIQUETAS GENERALES ===

@app.post("/etiquetas", response_model=schemas.EtiquetaOut, status_code=status.HTTP_201_CREATED)
def crear_etiqueta(et: schemas.EtiquetaCreate, db: Session = Depends(get_db)):
    return crud.create_etiqueta(db, et)

@app.get("/etiquetas", response_model=List[schemas.EtiquetaOut])
def listar_etiquetas(db: Session = Depends(get_db)):
    return crud.get_all_etiquetas(db)


# === ETIQUETAS ESPECÍFICAS ===

@app.post("/etiquetas/adoptante", response_model=schemas.EtiquetaOut, status_code=status.HTTP_201_CREATED)
def etiquetar_adoptante(
    et: schemas.EtiquetaAdoptanteCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    # solo adoptante puede etiquetarse a sí mismo
    if user["rol"] != "adoptante" or int(user["sub"]) != et.adoptante_id:
        raise HTTPException(403, "No puedes etiquetar a otro adoptante")
    return crud.create_e_adoptante(db, et)

@app.post("/etiquetas/mascota", response_model=schemas.EtiquetaOut, status_code=status.HTTP_201_CREATED)
def etiquetar_mascota(
    et: schemas.EtiquetaMascotaCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    # solo el albergue dueño de la mascota puede etiquetar
    if user["rol"] != "albergue":
        raise HTTPException(403, "Solo albergues pueden etiquetar mascotas")
    return crud.create_e_mascota(db, et)


# === ASOCIACIÓN RESPUESTA ↔ ETIQUETA ===

@app.post("/res_etiqueta", response_model=schemas.ResEtiquetaOut, status_code=status.HTTP_201_CREATED)
def asociar_res_etiqueta(
    re: schemas.ResEtiquetaCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    # validaciones opcionales: que la respuesta_usuario pertenezca al adoptante
    return crud.create_res_etiqueta(db, re)

@app.get("/res_etiqueta", response_model=List[schemas.ResEtiquetaOut])
def listar_res_etiquetas(db: Session = Depends(get_db)):
    return crud.get_all_res_etiqueta(db)
