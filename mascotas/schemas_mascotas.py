from pydantic import BaseModel # type: ignore
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel
from typing import List, Optional


#=====MASCOTA=======
class GeneroEnum(str, Enum):
    macho = "Macho"
    hembra = "Hembra"


class MascotaCreate(BaseModel):
    nombre: str
    edad: int
    especie: str
    descripcion: Optional[str]
    imagen_id: int
    etiquetas: List[str]
    genero: GeneroEnum 
    vacunas: List[str] = []  


class MascotaResponse(BaseModel):
    id: int
    nombre: str
    edad: int
    especie: str
    descripcion: Optional[str]
    albergue_id: int
    albergue_nombre: Optional[str] = None 
    imagen_id: int
    etiquetas: List[str]
    vacunas: List[str]
    created_at: str
    genero: Optional[GeneroEnum] = None

    class Config:
        from_attributes = True


class MascotaUpdate(BaseModel):
    nombre: Optional[str] = None
    edad: Optional[int] = None
    especie: Optional[str] = None
    descripcion: Optional[str] = None
    etiquetas: List[str] = []
    vacunas: List[str] = []  # NUEVO CAMPO

