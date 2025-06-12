from pydantic import BaseModel # type: ignore
from typing import Optional, List
import json

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

