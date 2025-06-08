from pydantic import BaseModel
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
        )


class MascotaCreate(BaseModel):
    nombre: str
    edad: str
    especie: str
    descripcion: Optional[str]
    imagen_id: int
    etiquetas: List[str]

class MascotaResponse(BaseModel):
    id: int
    nombre: str
    edad: str
    especie: str
    descripcion: Optional[str]
    albergue_id: int
    imagen_id: int
    etiquetas: List[str]  
    created_at: str

    class Config:
        from_attributes = True

class AlbergueOut(BaseModel):
    id: int
    nombre: str
    telefono: str
    correo: str

    class Config:
        from_attributes = True



# === CREACIÓN INTERNA (CRUD) ===
class AdoptanteCreate(BaseModel):
    nombre: str
    apellido: str
    dni: str
    correo: str
    contrasena: str
    telefono: Optional[str] = None
    # las etiquetas vendrán por separado al momento de finalizar el cuestionario

class AlbergueCreate(BaseModel):
    nombre: str
    ruc: str
    correo: str
    contrasena: str
    telefono: Optional[str] = None



# === PREGUNTAS Y RESPUESTAS ===
class PreguntaCreate(BaseModel):
    texto: str

class PreguntaOut(BaseModel):
    id: int
    texto: str

    class Config:
        from_attributes = True

class RespuestaCreate(BaseModel):
    pregunta_id: int
    valor: str

class RespuestaOut(BaseModel):
    id: int
    pregunta_id: int
    valor: str

    class Config:
        from_attributes = True

class RespuestaUsuarioCreate(BaseModel):
    adoptante_id: Optional[int] = None
    pregunta_id: int
    respuesta_id: Optional[int] = None

class RespuestaUsuarioOut(BaseModel):
    id: int
    adoptante_id: int
    pregunta_id: int
    respuesta_id: Optional[int]

    class Config:
        from_attributes = True


class MascotaUpdate(BaseModel):
    nombre: str = None
    edad: int = None
    especie: str = None
    descripcion: str = None
    etiquetas: List[str] = []
