from sqlalchemy import Column, Integer, String, ForeignKey, Float
from database import Base
from sqlalchemy.orm import relationship


class Usuario(Base):
    __tablename__ = "usuario"
    id = Column(Integer, primary_key=True, index=True)
    correo = Column(String, unique=True, index=True)
    telefono = Column(String)
    contrasena = Column(String)
    


class Adoptante(Base):
    __tablename__ = "adoptante"
    id = Column(Integer, ForeignKey("usuario.id"), primary_key=True)
    nombre = Column(String)
    apellido = Column(String)
    dni = Column(String, unique=True)

    respuestas_usuario = relationship("RespuestaUsuario", back_populates="adoptante")


class Albergue(Base):
    __tablename__ = "albergue"
    id = Column(Integer, ForeignKey("usuario.id"), primary_key=True)
    nombre = Column(String)
    ruc = Column(String, unique=True)
    
    mascotas = relationship("Mascota", back_populates="albergue")


class Mascota(Base):
    __tablename__ = "mascotas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    especie = Column(String)  
    edad = Column(Integer)
    descripcion = Column(String, nullable=True)
    albergue_id = Column(Integer, ForeignKey("albergue.id"))  # Relación con la empresa
    imagen_id = Column(Integer, ForeignKey("imagenes.id"))

    imagen = relationship("Imagen")
    albergue = relationship("Albergue", back_populates="mascotas")


class Pregunta(Base):
    __tablename__ = "preguntas"
    id = Column(Integer, primary_key=True, index=True)
    texto = Column(String, nullable=False)
    respuestas_posibles = relationship("Respuesta", back_populates="pregunta")


class Respuesta(Base):
    __tablename__ = "respuestas"
    id = Column(Integer, primary_key=True, index=True)
    pregunta_id = Column(Integer, ForeignKey("preguntas.id"))
    valor = Column(String)  # Por ejemplo: "Si", "No", "Prefiero lugares tranquilos", etc.

    pregunta = relationship("Pregunta", back_populates="respuestas_posibles")


class RespuestaUsuario(Base):
    __tablename__ = "respuestas_usuario"
    id = Column(Integer, primary_key=True, index=True)
    adoptante_id = Column(Integer, ForeignKey("adoptante.id"))
    pregunta_id = Column(Integer, ForeignKey("preguntas.id"))
    respuesta_id = Column(Integer, ForeignKey("respuestas.id"))  # referencia la respuesta predefinida elegida

    adoptante = relationship("Adoptante", back_populates="respuestas_usuario")
    pregunta = relationship("Pregunta")
    respuesta = relationship("Respuesta")



class Imagen(Base):
    __tablename__ = "imagenes"

    id = Column(Integer, primary_key=True, index=True)
    ruta = Column(String, nullable=False)


