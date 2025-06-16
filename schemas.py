from pydantic import BaseModel # type: ignore
from typing import Optional, List
import json

# === REGISTRO DE USUARIOS ===
class AdoptanteRegister(BaseModel):
    nombre: str
    apellido: str
    dni: str
    correo: str
    contrasena: str
    etiquetas: List[str] = []
    imagen_perfil_id: int



class AlbergueRegister(BaseModel):
    nombre: str
    ruc: str
    correo: str
    contrasena: str
    telefono: Optional[str] = None

# === LOGIN ===
class AdoptanteLogin(BaseModel):
    correo: str
    contrasena: str

class AlbergueLogin(BaseModel):
    correo: str
    contrasena: str

# === OUTPUT DEL ADOPTANTE ===
class AdoptanteOut(BaseModel):
    id: int
    nombre: str
    apellido: str
    dni: str
    correo: str
    telefono: Optional[str]
    etiquetas: List[str]
    imagen_perfil_id: int

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_etiquetas(cls, adoptante_obj):
        raw = adoptante_obj.etiquetas
        lista = []
        if raw:
            try:
                lista = json.loads(raw)
            except Exception:
                lista = []
        return cls(
            id=adoptante_obj.id,
            nombre=adoptante_obj.nombre,
            apellido=adoptante_obj.apellido,
            dni=adoptante_obj.dni,
            correo=adoptante_obj.correo,
            telefono=adoptante_obj.telefono,
            etiquetas=lista,
            imagen_perfil_id=adoptante_obj.imagen_perfil_id,
        )

class AdoptanteCreate(BaseModel):
    nombre: str
    apellido: str
    dni: str
    correo: str
    contrasena: str
    telefono: Optional[str] = None
    imagen_perfil_id: int

#=====MASCOTA=======
class MascotaCreate(BaseModel):
    nombre: str
    edad: int
    especie: str
    descripcion: Optional[str]
    imagen_id: int
    etiquetas: List[str]
    genero: str
    vacunas: List[str] = []  # NUEVO CAMPO


class MascotaResponse(BaseModel):
    id: int
    nombre: str
    edad: int
    especie: str
    descripcion: Optional[str]
    albergue_id: int
    imagen_id: int
    etiquetas: List[str]
    vacunas: List[str]
    created_at: str
    genero: Optional[str]

    class Config:
        from_attributes = True


class MascotaUpdate(BaseModel):
    nombre: Optional[str] = None
    edad: Optional[int] = None
    especie: Optional[str] = None
    descripcion: Optional[str] = None
    etiquetas: List[str] = []
    vacunas: List[str] = []  # NUEVO CAMPO


# === OUTPUT DEL ALBERGUE ===
class AlbergueOut(BaseModel):
    id: int
    nombre: str
    telefono: str
    correo: str

    class Config:
        from_attributes = True

class AlbergueCreate(BaseModel):
    nombre: str
    ruc: str
    correo: str
    contrasena: str
    telefono: Optional[str] = None


from pydantic import BaseModel
from typing import Literal, Union
from datetime import datetime

class Message(BaseModel):
    emisor_id: int
    emisor_tipo: Literal["adoptante", "albergue"]
    receptor_id: int
    receptor_tipo: Literal["adoptante", "albergue"]
    contenido: str
    timestamp: datetime

from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

# Modelo para recibir el mensaje sin timestamp (input)
class MessageIn(BaseModel):
    receptor_id: int
    receptor_tipo: str
    contenido: str

# schemas.py

from pydantic import BaseModel
from datetime import datetime

class MessageOut(BaseModel):
    emisor_id: int
    emisor_tipo: str
    receptor_id: int
    receptor_tipo: str
    contenido: str
    timestamp: datetime

    class Config:
        orm_mode = True



from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# Base para crear una cita en calendario
class CalendarioBase(BaseModel):
    fecha_hora: datetime
    asunto: str
    lugar: str
    albergue_id: int


# Para retornar una cita del calendario
class CalendarioOut(CalendarioBase):
    id: int

    class Config:
        orm_mode = True


# Para registrar una cita de visita
class CitaVisitaCreate(BaseModel):
    calendario: CalendarioBase
    adoptante_id: int


# Para registrar una cita de evento
class CitaEventoCreate(BaseModel):
    calendario: CalendarioBase


class CalendarioOut(BaseModel):
    id: int
    fecha_hora: datetime
    asunto: str
    lugar: str
    tipo: str
    albergue_id: int
    adoptante_id: Optional[int] = None  # ← AÑADE ESTA LÍNEA

    class Config:
        orm_mode = True
