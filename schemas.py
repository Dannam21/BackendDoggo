from pydantic import BaseModel # type: ignore
from typing import Optional, List, Dict, Union
import json

# === REGISTRO DE USUARIOS ===
class AdoptanteRegister(BaseModel):
    nombre: str
    apellido: str
    dni: str
    correo: str
    contrasena: str
    etiquetas: Dict[str, Union[str, List[str]]] = {}
    imagen_perfil_id: Optional[int] = None
    telefono: Optional[str] = None
    pesos: Dict[str, float] = {}


class AlbergueRegister(BaseModel):
    nombre: str
    ruc: str
    correo: str
    contrasena: str
    telefono: Optional[str] = None
    pesos: Dict[str, float] = {}

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
    etiquetas: Dict[str, Union[str, List[str]]]
    imagen_perfil_id: int
    pesos: Dict[str, float] 

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_etiquetas(cls, adoptante_obj):
        try:
            etiquetas = json.loads(adoptante_obj.etiquetas) if adoptante_obj.etiquetas else {}
        except:
            etiquetas = {}
        # parseamos pesos
        try:
            pesos = json.loads(adoptante_obj.pesos) if adoptante_obj.pesos else {}
        except:
            pesos = {}
        return cls(
            id=adoptante_obj.id,
            nombre=adoptante_obj.nombre,
            apellido=adoptante_obj.apellido,
            dni=adoptante_obj.dni,
            correo=adoptante_obj.correo,
            telefono=adoptante_obj.telefono,
            etiquetas=etiquetas,
            imagen_perfil_id=adoptante_obj.imagen_perfil_id,
            pesos=pesos,
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
from typing import Literal
from datetime import datetime

class Message(BaseModel):
    emisor_id: int
    emisor_tipo: Literal["adoptante", "albergue"]
    receptor_id: int
    receptor_tipo: Literal["adoptante", "albergue"]
    contenido: str
    timestamp: datetime
    mascota_id: int  # ✅ Se añade el ID de la mascota

from pydantic import BaseModel

class MessageIn(BaseModel):
    receptor_id: int
    receptor_tipo: str
    contenido: str
    mascota_id: int  # ✅ Requerido al enviar un mensaje

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
    mascota_id: int  # ✅ Para mostrar a qué mascota pertenece el mensaje

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




from pydantic import BaseModel

class MatchCreate(BaseModel):
    adoptante_id: int
    mascota_id: int


# Agregar a schemas.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DonacionCreate(BaseModel):
    mascota_id: int
    monto: float
    mensaje: Optional[str] = None

class DonacionResponse(BaseModel):
    id: int
    adoptante_id: int
    mascota_id: int
    albergue_id: int
    monto: float
    mensaje: Optional[str]
    estado: str
    mp_preference_id: Optional[str]
    created_at: datetime
    
    # Información adicional para el frontend
    adoptante_nombre: Optional[str] = None
    mascota_nombre: Optional[str] = None
    albergue_nombre: Optional[str] = None

    class Config:
        from_attributes = True

class PreferenceResponse(BaseModel):
    preference_id: str
    init_point: str
    sandbox_init_point: str

class WebhookNotification(BaseModel):
    action: str
    api_version: str
    data: dict
    date_created: str
    id: int
    live_mode: bool
    type: str
    user_id: str

class ConfiguracionMPCreate(BaseModel):
    access_token: str
    public_key: str
    webhook_url: Optional[str] = None

class ConfiguracionMPResponse(BaseModel):
    id: int
    albergue_id: int
    public_key: str  # Solo devolvemos la public key por seguridad
    activo: bool
    webhook_url: Optional[str]

    class Config:
        from_attributes = True