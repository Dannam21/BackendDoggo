from pydantic import BaseModel
from typing import Optional

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
    descripcion:str
    imagen_id: int

class MascotaResponse(BaseModel):
    id: int
    nombre: str
    edad: int
    especie: str
    albergue_id: int
    imagen_id: int
    
    class Config:
        from_attributes = True


# === PREGUNTAS Y RESPUESTAS ===
# Para crear preguntas (igual)
class PreguntaCreate(BaseModel):
    texto: str

class PreguntaOut(BaseModel):
    id: int
    texto: str

    class Config:
        orm_mode = True


# Para las opciones posibles de respuesta (catálogo)
class RespuestaCreate(BaseModel):
    pregunta_id: int
    valor: str

class RespuestaOut(BaseModel):
    id: int
    pregunta_id: int
    valor: str

    class Config:
        orm_mode = True


# Para las respuestas que da el usuario
class RespuestaUsuarioCreate(BaseModel):
    adoptante_id: Optional[int] = None  # opcional, puede obtenerse del token
    pregunta_id: int
    respuesta_id: Optional[int] = None  # cuando elige una respuesta predefinida

class RespuestaUsuarioOut(BaseModel):
    id: int
    adoptante_id: int
    pregunta_id: int
    respuesta_id: Optional[int]
    valor_personalizado: Optional[str]

    class Config:
        orm_mode = True
