from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from database import Base
from sqlalchemy.sql import func # type: ignore
from datetime import datetime


class Adoptante(Base):
    __tablename__ = "adoptante"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    dni = Column(String, unique=True, nullable=False)
    correo = Column(String, unique=True, index=True, nullable=False)
    telefono = Column(String, nullable=True)
    contrasena = Column(String, nullable=False)
    etiquetas = Column(Text, nullable=True)
    pesos           = Column(Text, nullable=True)
    
    imagen_perfil_id = Column(Integer, ForeignKey("imagenes_perfil.id"), nullable=True)
    imagen_perfil = relationship("ImagenPerfil", backref="adoptantes")
    
    
    matches = relationship("Match", back_populates="adoptante", cascade="all, delete-orphan")
    mascotas = relationship("Mascota",secondary="matches",back_populates="adoptantes")
    adopciones = relationship("Adopcion", back_populates="adoptante", cascade="all, delete-orphan")
    denegaciones = relationship("Denegacion", back_populates="adoptante", cascade="all, delete-orphan")

class ImagenPerfil(Base):
    __tablename__ = "imagenes_perfil"
    id = Column(Integer, primary_key=True, index=True)
    ruta = Column(String, nullable=False)   

#=====ALBERGUE=======
class Albergue(Base):
    __tablename__ = "albergue"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    ruc = Column(String, unique=True, nullable=False)
    correo = Column(String, unique=True, index=True, nullable=False)
    telefono = Column(String, nullable=True)
    contrasena = Column(String, nullable=False)
    ubicacion = Column(String, nullable=True)
    
    mascotas = relationship("Mascota", back_populates="albergue")

#=====MASCOTA=======

class Mascota(Base):
    __tablename__ = "mascotas"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    especie = Column(String)
    edad = Column(Integer)
    descripcion = Column(String, nullable=True)
    albergue_id = Column(Integer, ForeignKey("albergue.id"))
    imagen_id = Column(Integer, ForeignKey("imagenes.id"))
    etiquetas = Column(String, nullable=True)
    vacunas = Column(Text, nullable=True)  # NUEVO CAMPO
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    genero = Column(String, nullable=False)
    estado = Column(String, nullable=False)  # "disponible", "adoptado", "en_adopcion", etc.

    imagen = relationship("Imagen")
    albergue = relationship("Albergue", back_populates="mascotas")
    matches    = relationship("Match",    back_populates="mascota", cascade="all, delete-orphan")
    adoptantes = relationship("Adoptante", secondary="matches", back_populates="mascotas")
    adopcion   = relationship("Adopcion", back_populates="mascota",uselist=False, cascade="all, delete-orphan")
    denegaciones = relationship("Denegacion", back_populates="mascota", cascade="all, delete-orphan")

#=====IMAGEN=======
class Imagen(Base):
    __tablename__ = "imagenes"
    id = Column(Integer, primary_key=True, index=True)
    ruta = Column(String, nullable=False)


class Mensaje(Base):
    __tablename__ = "mensajes"

    id = Column(Integer, primary_key=True, index=True)
    emisor_id = Column(Integer, nullable=False)
    emisor_tipo = Column(String, nullable=False)  # "adoptante" o "albergue"
    receptor_id = Column(Integer, nullable=False)
    receptor_tipo = Column(String, nullable=False)
    contenido = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    mascota_id = Column(Integer, ForeignKey("mascotas.id"), nullable=False)

# ===== CALENDARIO BASE =====
class Calendario(Base):
    __tablename__ = "calendario"
    id = Column(Integer, primary_key=True, index=True)
    albergue_id = Column(Integer, ForeignKey("albergue.id"), nullable=False)
    fecha_hora = Column(DateTime(timezone=True), nullable=False)
    asunto = Column(String, nullable=False)
    lugar = Column(String, nullable=False)
    tipo = Column(String, nullable=False)  # "visita" o "evento"
    adoptante_id = Column(Integer, ForeignKey("adoptante.id"), nullable=True)

    # Relaciones
    albergue = relationship("Albergue", backref="calendario")


# ===== CITA VISITA =====
class CitaVisita(Base):
    __tablename__ = "citas_visita"
    id = Column(Integer, ForeignKey("calendario.id"), primary_key=True)
    adoptante_id = Column(Integer, ForeignKey("adoptante.id"), nullable=False)

    # Relaciones
    calendario = relationship("Calendario", backref="visita", uselist=False)
    adoptante = relationship("Adoptante", backref="citas_visita")


# ===== CITA EVENTO =====
class CitaEvento(Base):
    __tablename__ = "citas_evento"
    id = Column(Integer, ForeignKey("calendario.id"), primary_key=True)

    # Relaciones
    calendario = relationship("Calendario", backref="evento", uselist=False)

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    adoptante_id = Column(Integer, ForeignKey("adoptante.id"), primary_key=True)
    mascota_id   = Column(Integer, ForeignKey("mascotas.id"),  primary_key=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    
    adoptante = relationship("Adoptante", back_populates="matches")
    mascota   = relationship("Mascota",   back_populates="matches")

class MatchTotal(Base):
    __tablename__ = "match_totales"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    albergue_id   = Column(Integer, ForeignKey("albergue.id"), nullable=True)
    adoptante_id  = Column(Integer, ForeignKey("adoptante.id"), nullable=True)
    mascota_id    = Column(Integer, ForeignKey("mascotas.id"), nullable=True)
    fecha         = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    albergue  = relationship("Albergue", backref="match_totales")
    adoptante = relationship("Adoptante", backref="match_totales")
    mascota   = relationship("Mascota", backref="match_totales")

class Donacion(Base):
    __tablename__ = "donaciones"
    id = Column(Integer, primary_key=True, index=True)
    adoptante_id = Column(Integer, ForeignKey("adoptante.id"), nullable=False)
    mascota_id = Column(Integer, ForeignKey("mascotas.id"), nullable=False)
    monto = Column(Integer, nullable=False)
    fecha = Column(DateTime, default=func.now())

    adoptante = relationship("Adoptante")
    mascota = relationship("Mascota")
    

class Adopcion(Base):
    __tablename__ = "adopciones"
    id           = Column(Integer, primary_key=True, index=True)
    adoptante_id = Column(Integer, ForeignKey("adoptante.id"), nullable=False)
    mascota_id   = Column(Integer, ForeignKey("mascotas.id"),  nullable=False)
    fecha        = Column(DateTime(timezone=True), server_default=func.now())

    adoptante = relationship("Adoptante", back_populates="adopciones")
    mascota   = relationship("Mascota",   back_populates="adopcion")

class Denegacion(Base):
    __tablename__ = "denegaciones"
    id           = Column(Integer, primary_key=True, index=True)
    adoptante_id = Column(Integer, ForeignKey("adoptante.id"), nullable=False)
    mascota_id   = Column(Integer, ForeignKey("mascotas.id"),  nullable=False)
    fecha        = Column(DateTime(timezone=True), server_default=func.now())

    adoptante = relationship("Adoptante", back_populates="denegaciones")
    mascota   = relationship("Mascota",   back_populates="denegaciones")
