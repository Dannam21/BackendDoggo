from sqlalchemy.orm import Session  # type: ignore
from database import SessionLocal
from fastapi.security import OAuth2PasswordBearer  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi import FastAPI, Depends, HTTPException  # type: ignore

# Asegúrate de que estos módulos exporten "router" no "app"
from usuario import auth_usuario, rutas_usuario
from mascotas import rutas_mascotas
from albergue import rutas_albergue
from match import rutas_match

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    payload = auth_usuario.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    return payload


@app.get("/")
def root():
    return {"message": "Bienvenido a la API de Doggo"}


# Cambiar de .app a .router aquí:
app.include_router(rutas_usuario.router)
app.include_router(rutas_mascotas.router)
app.include_router(rutas_albergue.router)
app.include_router(rutas_match.router)
