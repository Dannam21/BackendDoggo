from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Float,
    DateTime,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from database import Base

class Usuario(Base):
    __tablename__ = "usuario"
    id         = Column(Integer, primary_key=True, index=True)
    correo     = Column(String, unique=True, index=True)
    telefono   = Column(String)
    contrasena = Column(String)

class Adoptante(Base):
    __tablename__ = "adoptante"
    id           = Column(Integer, ForeignKey("usuario.id"), primary_key=True)
    nombre       = Column(String)
    apellido     = Column(String)
    dni          = Column(String, unique=True)

    respuestas_usuario = relationship(
        "RespuestaUsuario", back_populates="adoptante", cascade="all, delete-orphan"
    )
    donaciones = relationship(
        "Donacion", back_populates="adoptante", cascade="all, delete-orphan"
    )
    etiquetas = relationship(
        "E_Adoptante", back_populates="adoptante", cascade="all, delete-orphan"
    )

class Albergue(Base):
    __tablename__ = "albergue"
    id         = Column(Integer, ForeignKey("usuario.id"), primary_key=True)
    nombre     = Column(String)
    ruc        = Column(String, unique=True)

    mascotas   = relationship("Mascota", back_populates="albergue", cascade="all, delete-orphan")
    donaciones = relationship(
        "Donacion", back_populates="albergue", cascade="all, delete-orphan"
    )

class Mascota(Base):
    __tablename__ = "mascotas"
    id          = Column(Integer, primary_key=True, index=True)
    nombre      = Column(String, index=True)
    especie     = Column(String)
    edad        = Column(Integer)
    albergue_id = Column(Integer, ForeignKey("albergue.id"))

    albergue     = relationship("Albergue", back_populates="mascotas")
    etiquetas    = relationship(
        "E_Mascota", back_populates="mascota", cascade="all, delete-orphan"
    )

class Pregunta(Base):
    __tablename__ = "preguntas"
    id                 = Column(Integer, primary_key=True, index=True)
    texto              = Column(String, nullable=False)

    respuestas_posibles = relationship("Respuesta", back_populates="pregunta", cascade="all, delete-orphan")

class Respuesta(Base):
    __tablename__ = "respuestas"
    id          = Column(Integer, primary_key=True, index=True)
    pregunta_id = Column(Integer, ForeignKey("preguntas.id"))
    valor       = Column(String)

    pregunta = relationship("Pregunta", back_populates="respuestas_posibles")

class RespuestaUsuario(Base):
    __tablename__ = "respuestas_usuario"
    id             = Column(Integer, primary_key=True, index=True)
    adoptante_id   = Column(Integer, ForeignKey("adoptante.id"))
    pregunta_id    = Column(Integer, ForeignKey("preguntas.id"))
    respuesta_id   = Column(Integer, ForeignKey("respuestas.id"))

    adoptante      = relationship("Adoptante", back_populates="respuestas_usuario")
    pregunta       = relationship("Pregunta")
    respuesta      = relationship("Respuesta")
    res_etiquetas  = relationship(
        "Res_Etiqueta", back_populates="respuesta_usuario", cascade="all, delete-orphan"
    )

# --- NUEVAS TABLAS ---

class Donacion(Base):
    __tablename__ = "donacion"

    id           = Column(Integer, primary_key=True, index=True)
    adoptante_id = Column(Integer, ForeignKey("adoptante.id"), nullable=False)
    albergue_id  = Column(Integer, ForeignKey("albergue.id"),  nullable=False)
    fecha        = Column(DateTime, default=datetime.utcnow, nullable=False)
    monto        = Column(Numeric(10, 2), nullable=False)
    comentario   = Column(Text)

    adoptante = relationship("Adoptante", back_populates="donaciones")
    albergue  = relationship("Albergue",  back_populates="donaciones")

class Etiqueta(Base):
    __tablename__ = "etiqueta"

    id           = Column(Integer, primary_key=True, index=True)
    nombre       = Column(String(100), unique=True, nullable=False)
    descripcion  = Column(Text)

    e_adoptantes  = relationship("E_Adoptante", back_populates="etiqueta", cascade="all, delete-orphan")
    e_mascotas    = relationship("E_Mascota",   back_populates="etiqueta", cascade="all, delete-orphan")
    res_etiquetas = relationship("Res_Etiqueta", back_populates="etiqueta", cascade="all, delete-orphan")

class E_Adoptante(Base):
    __tablename__ = "e_adoptante"

    id            = Column(Integer, ForeignKey("etiqueta.id"), primary_key=True)
    adoptante_id  = Column(Integer, ForeignKey("adoptante.id"), nullable=False)

    etiqueta   = relationship("Etiqueta",  back_populates="e_adoptantes")
    adoptante  = relationship("Adoptante", back_populates="etiquetas")

class E_Mascota(Base):
    __tablename__ = "e_mascota"

    id         = Column(Integer, ForeignKey("etiqueta.id"), primary_key=True)
    mascota_id = Column(Integer, ForeignKey("mascotas.id"), nullable=False)

    etiqueta = relationship("Etiqueta", back_populates="e_mascotas")
    mascota  = relationship("Mascota",   back_populates="etiquetas")

class Res_Etiqueta(Base):
    __tablename__ = "res_etiqueta"
    __table_args__ = (
        UniqueConstraint("respuesta_usuario_id", "etiqueta_id", name="uix_resp_etiq"),
    )

    id                    = Column(Integer, primary_key=True, index=True)
    respuesta_usuario_id  = Column(Integer, ForeignKey("respuestas_usuario.id"), nullable=False)
    etiqueta_id           = Column(Integer, ForeignKey("etiqueta.id"),             nullable=False)

    respuesta_usuario = relationship("RespuestaUsuario", back_populates="res_etiquetas")
    etiqueta          = relationship("Etiqueta",         back_populates="res_etiquetas")
