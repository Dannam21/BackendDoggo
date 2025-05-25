from fastapi import FastAPI, Depends, HTTPException
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

