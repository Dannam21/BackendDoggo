from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from fastapi.security import OAuth2PasswordBearer

from albergue import modelos_albergue, schemas_albergue
from usuario import auth_usuario, schemas_usuario
from albergue import crud_albergue
from usuario.auth_usuario import get_current_user

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register/albergue")
def register_albergue(user: schemas_albergue.AlbergueCreate, db: Session = Depends(get_db)):
    if crud_albergue.get_albergue_by_correo(db, user.correo):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    new_albergue = crud_albergue.create_albergue(db, user)
    return {"mensaje": "Albergue registrado con éxito", "id": new_albergue.id}


@router.post("/login/albergue")
def login_albergue(user: schemas_usuario.AlbergueLogin, db: Session = Depends(get_db)):
    db_albergue = crud_albergue.get_albergue_by_correo(db, user.correo)
    if not db_albergue or not crud_albergue.verify_password(user.contrasena, db_albergue.contrasena):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token_data = {
        "sub": str(db_albergue.id),
        "rol": "albergue",
        "albergue_id": db_albergue.id
    }
    token = auth_usuario.create_access_token(token_data)
    return {
        "access_token": token,
        "token_type": "bearer",
        "albergue_id": db_albergue.id
    }


@router.get("/albergue/me", response_model=schemas_albergue.AlbergueOut, summary="Obtener datos del albergue autenticado")
def get_albergue_me(user = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.get("rol") != "albergue":
        raise HTTPException(status_code=403, detail="Solo los albergues pueden acceder a este recurso")

    albergue_id = int(user["albergue_id"])
    albergue_obj = db.query(modelos_albergue.Albergue).filter(modelos_albergue.Albergue.id == albergue_id).first()
    if not albergue_obj:
        raise HTTPException(status_code=404, detail="Albergue no encontrado")

    return schemas_albergue.AlbergueOut.from_orm(albergue_obj)
