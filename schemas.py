from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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

# DONACIÓN
class DonacionCreate(BaseModel):
    albergue_id: int
    monto: float
    comentario: str | None = None

class DonacionOut(DonacionCreate):
    id: int
    adoptante_id: int
    fecha: datetime
    class Config:
        orm_mode = True

# ETIQUETA
class EtiquetaCreate(BaseModel):
    nombre: str
    descripcion: str | None = None

class EtiquetaOut(EtiquetaCreate):
    id: int
    class Config:
        orm_mode = True

# ETIQUETA ADOPTANTE / MASCOTA
class EtiquetaAdoptanteCreate(BaseModel):
    id: int           # hereda de etiqueta
    nombre: str
    descripcion: str | None = None
    adoptante_id: int

class EtiquetaMascotaCreate(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None
    mascota_id: int

# RES_ETIQUETA
class ResEtiquetaCreate(BaseModel):
    respuesta_usuario_id: int
    etiqueta_id: int

class ResEtiquetaOut(ResEtiquetaCreate):
    id: int
    class Config:
        orm_mode = True