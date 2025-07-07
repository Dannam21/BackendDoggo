from sqlalchemy.orm import Session # type: ignore
import models
import schemas
from passlib.hash import bcrypt # type: ignore
import json
from pytz import timezone

import pytz # type: ignore
from datetime import datetime 
from models import Mascota, Calendario, CitaVisita, CitaEvento, Match, Adopcion, Denegacion

# === ADOPTANTE ===
def create_adoptante(db: Session, adoptante: schemas.AdoptanteRegister):
    hashed_pw = bcrypt.hash(adoptante.contrasena)
    etiquetas = json.dumps(adoptante.etiquetas) if adoptante.etiquetas is not None else None
    pesos     = json.dumps(adoptante.pesos)     if adoptante.pesos     is not None else None
    
    db_adoptante = models.Adoptante(
        nombre=adoptante.nombre,
        apellido=adoptante.apellido,
        dni=adoptante.dni,
        correo=adoptante.correo,
        telefono=getattr(adoptante, "telefono", None),
        contrasena=hashed_pw,
        etiquetas=etiquetas,      
        imagen_perfil_id=adoptante.imagen_perfil_id,
        pesos=pesos,    
    )
    db.add(db_adoptante)
    db.commit()
    db.refresh(db_adoptante)
    return db_adoptante

# === ALBERGUE ===
def create_albergue(db: Session, albergue: schemas.AlbergueRegister):
    hashed_pw = bcrypt.hash(albergue.contrasena)
    db_albergue = models.Albergue(
        nombre=albergue.nombre,
        ruc=albergue.ruc,
        correo=albergue.correo,
        contrasena=hashed_pw,
        telefono=albergue.telefono,
        direccion=albergue.direccion,
        latitud=albergue.latitud,
        longitud=albergue.longitud,
    )
    db.add(db_albergue)
    db.commit()
    db.refresh(db_albergue)
    return db_albergue


def get_albergue_by_correo(db: Session, correo: str):
    return db.query(models.Albergue).filter(models.Albergue.correo == correo).first()

def get_adoptante_by_correo(db: Session, correo: str):
    return db.query(models.Adoptante).filter(models.Adoptante.correo == correo).first()

def get_albergue_by_ruc(db: Session, ruc: str):
    return db.query(models.Albergue).filter(models.Albergue.ruc == ruc).first()

def get_adoptante_by_dni(db: Session, dni: str):
    return db.query(models.Adoptante).filter(models.Adoptante.dni == dni).first()

def encrypt_password(plain_password: str) -> str:
    return bcrypt.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.verify(plain_password, hashed_password)


def create_mascota(db: Session, mascota: schemas.MascotaCreate, albergue_id: int):
    lima_tz = pytz.timezone("America/Lima")
    ahora_lima = datetime.now(lima_tz)

    nueva = models.Mascota(
        nombre=mascota.nombre,
        edad_valor=mascota.edad_valor or 0,  # 👈 default 0
        edad_unidad=mascota.edad_unidad or "meses",  # 👈 default "meses"
        especie=mascota.especie,
        genero=mascota.genero,  
        descripcion=mascota.descripcion,
        imagen_id=mascota.imagen_id,
        etiquetas=json.dumps(mascota.etiquetas),
        vacunas=json.dumps(mascota.vacunas),  # 👈 Agregado aquí
        estado=mascota.estado or "En adopción",
        albergue_id=albergue_id,
        created_at=ahora_lima, 
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva




def get_all_mascotas(db: Session):
    return db.query(models.Mascota).all()

def get_mascotas_por_albergue(db: Session, albergue_id: int):
    return db.query(models.Mascota).filter(models.Mascota.albergue_id == albergue_id).all()

def crear_cita_visita(db: Session, data: schemas.CitaVisitaCreate):
    lima = timezone("America/Lima")
    data_dict = data.calendario.dict()
    data_dict["tipo"] = "visita"

    #  Verificación de datos recibidos
    print("Verificacion:", data)
    print("DATA BRUTA:", data)
    print("calendario:", data_dict)
    print("adoptante_id:", data.adoptante_id)

    data_dict["adoptante_id"] = data.adoptante_id  

    if data_dict["fecha_hora"].tzinfo is None:
        data_dict["fecha_hora"] = lima.localize(data_dict["fecha_hora"])

    cita = Calendario(**data_dict)
    db.add(cita)
    db.flush()

    visita = CitaVisita(id=cita.id, adoptante_id=data.adoptante_id)
    db.add(visita)
    db.commit()
    db.refresh(cita)
    return cita

def crear_cita_evento(db: Session, data: schemas.CitaEventoCreate):
    cita = Calendario(**data.calendario.dict(), tipo="evento")
    db.add(cita)
    db.flush()

    evento = CitaEvento(id=cita.id)
    db.add(evento)
    db.commit()
    db.refresh(cita)
    return cita

def obtener_citas_por_albergue(db: Session, albergue_id: int):
    return db.query(Calendario).filter(Calendario.albergue_id == albergue_id).all()

def denegar_match(db: Session, adoptante_id: int, mascota_id: int):
    deleted = db.query(Match).filter_by(
        adoptante_id=adoptante_id,
        mascota_id=mascota_id
    ).delete()
    db.commit()
    return deleted  # 0 o 1

def completar_match(db: Session, adoptante_id: int, mascota_id: int):
    match = db.query(Match).filter_by(
        adoptante_id=adoptante_id,
        mascota_id=mascota_id
    ).first()
    if not match:
        raise Exception("Match no encontrado")

    nueva_adop = Adopcion(
        adoptante_id=adoptante_id,
        mascota_id=mascota_id
    )
    db.add(nueva_adop)
    db.flush()  

    db.query(Match).filter_by(mascota_id=mascota_id).delete()

    db.commit()
    db.refresh(nueva_adop)
    return nueva_adop


def get_adopciones_por_adoptante(db: Session, adoptante_id: int):
    """Lista todas las adopciones de un adoptante."""
    return db.query(Adopcion).filter(Adopcion.adoptante_id == adoptante_id).all()

def get_adopcion_por_mascota(db: Session, mascota_id: int):
    """Devuelve la adopción de una mascota (si ya fue adoptada)."""
    return db.query(Adopcion).filter(Adopcion.mascota_id == mascota_id).first()


def denegar_match(db: Session, adoptante_id: int, mascota_id: int):
    """
    Registra la denegación y luego borra el match.
    """
    # 1) Crear registro de Denegacion
    neg = Denegacion(
        adoptante_id=adoptante_id,
        mascota_id=mascota_id
    )
    db.add(neg)
    # 2) Borrar el match concreto
    borrados = db.query(Match).filter_by(
        adoptante_id=adoptante_id,
        mascota_id=mascota_id
    ).delete()

    if borrados == 0:
        db.rollback()
        raise Exception("No se encontró match para denegar")

    db.commit()
    db.refresh(neg)
    return neg