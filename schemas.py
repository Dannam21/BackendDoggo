from pydantic import BaseModel

# === REGISTRO DE USUARIOS ===
class AdoptanteRegister(BaseModel):
    nombre: str
    apellido: str
    dni: str
    correo: str
    contrasena: str

class AlbergueRegister(BaseModel):
    nombre: str
    ruc: str
    correo: str
    contrasena: str

# === LOGIN ===
class AdoptanteLogin(BaseModel):
    correo: str
    contrasena: str

class AlbergueLogin(BaseModel):
    correo: str
    ruc: str
    contrasena: str

# === CREACIÓN DE ADOPTANTE Y ALBERGUE (para uso interno en CRUD) ===
class AdoptanteCreate(BaseModel):
    nombre: str
    apellido: str
    dni: str

class AlbergueCreate(BaseModel):
    nombre: str
    ruc: str

# === MASCOTA ===
class MascotaCreate(BaseModel):
    nombre: str
    edad: int
    especie: str

class MascotaResponse(BaseModel):
    id: int
    nombre: str
    edad: int
    especie: str
    albergue_id: int

    class Config:
        from_attributes = True
