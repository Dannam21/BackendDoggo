from pydantic import BaseModel # type: ignore
from typing import Optional, List
import json


# OUTPUT DEL ALBERGUE 
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

