from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from database import Base
from sqlalchemy.sql import func # type: ignore

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

    respuestas_usuario = relationship("RespuestaUsuario", back_populates="adoptante")

class Albergue(Base):
    __tablename__ = "albergue"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    ruc = Column(String, unique=True, nullable=False)
    correo = Column(String, unique=True, index=True, nullable=False)
    telefono = Column(String, nullable=True)
    contrasena = Column(String, nullable=False)

    mascotas = relationship("Mascota", back_populates="albergue")



class Mascota(Base):
    __tablename__ = "mascotas"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    especie = Column(String)
    edad = Column(String)
    descripcion = Column(String, nullable=True)
    albergue_id = Column(Integer, ForeignKey("albergue.id"))
    imagen_id = Column(Integer, ForeignKey("imagenes.id"))
    etiquetas = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    imagen = relationship("Imagen")
    albergue = relationship("Albergue", back_populates="mascotas")

class Imagen(Base):
    __tablename__ = "imagenes"
    id = Column(Integer, primary_key=True, index=True)
    ruta = Column(String, nullable=False)






## POR VERIFICAR Y CORREGIR


class Pregunta(Base):
    __tablename__ = "preguntas"
    id = Column(Integer, primary_key=True, index=True)
    texto = Column(String, nullable=False)

    respuestas_posibles = relationship("Respuesta", back_populates="pregunta")

class Respuesta(Base):
    __tablename__ = "respuestas"
    id = Column(Integer, primary_key=True, index=True)
    pregunta_id = Column(Integer, ForeignKey("preguntas.id"))
    valor = Column(String, nullable=False)

    pregunta = relationship("Pregunta", back_populates="respuestas_posibles")

class RespuestaUsuario(Base):
    __tablename__ = "respuestas_usuario"
    id = Column(Integer, primary_key=True, index=True)
    adoptante_id = Column(Integer, ForeignKey("adoptante.id"))
    pregunta_id = Column(Integer, ForeignKey("preguntas.id"))
    respuesta_id = Column(Integer, ForeignKey("respuestas.id"))

    adoptante = relationship("Adoptante", back_populates="respuestas_usuario")
    pregunta = relationship("Pregunta")
    respuesta = relationship("Respuesta")

