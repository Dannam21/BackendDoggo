import modelos_albergue, schemas_albergue, mascotas.crud_mascotas as crud_mascotas, auth
from sqlalchemy.orm import Session # type: ignore
from database import SessionLocal, engine
from fastapi.security import OAuth2PasswordBearer # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File # type: ignore
from modelos_albergue import Albergue
from main import get_current_user
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
@app.post("/register/albergue")
def register_albergue(user: schemas_albergue.AlbergueCreate, db: Session = Depends(get_db)):
    if crud_mascotas.get_albergue_by_correo(db, user.correo):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    new_albergue = crud_mascotas.create_albergue(db, user)
    return {"mensaje": "Albergue registrado con éxito", "id": new_albergue.id}



@app.post("/login/albergue")
def login_albergue(user: schemas_albergue.AlbergueLogin, db: Session = Depends(get_db)):
    db_albergue = crud_mascotas.get_albergue_by_correo(db, user.correo)
    if not db_albergue or not crud_mascotas.verify_password(user.contrasena, db_albergue.contrasena):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token_data = {
        "sub": str(db_albergue.id),
        "rol": "albergue",
        "albergue_id": db_albergue.id
    }
    token = auth.create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer", "albergue_id": db_albergue.id}


@app.get("/albergue/me", response_model=schemas_albergue.AlbergueOut, summary="Obtener datos del albergue autenticado")
def get_albergue_me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.get("rol") != "albergue":
        raise HTTPException(status_code=403, detail="Solo los albergues pueden acceder a este recurso")

    albergue_id = int(user["albergue_id"])
    albergue_obj = db.query(modelos_albergue.Albergue).filter(modelos_albergue.Albergue.id == albergue_id).first()
    if not albergue_obj:
        raise HTTPException(status_code=404, detail="Albergue no encontrado")

    return schemas_albergue.AlbergueOut.from_orm(albergue_obj)