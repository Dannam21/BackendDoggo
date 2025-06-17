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

    imagen_perfil_id = Column(Integer, ForeignKey("imagenes_perfil.id"))
    imagen_perfil = relationship("ImagenPerfil", backref="adoptantes")


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

    mascotas = relationship("Mascota", back_populates="albergue")



#=====MASCOTA=======
from sqlalchemy import Text

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

    imagen = relationship("Imagen")
    albergue = relationship("Albergue", back_populates="mascotas")

#=====IMAGEN=======
class Imagen(Base):
    __tablename__ = "imagenes"
    id = Column(Integer, primary_key=True, index=True)
    ruta = Column(String, nullable=False)



from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class Mensaje(Base):
    __tablename__ = "mensajes"

    id = Column(Integer, primary_key=True, index=True)
    emisor_id = Column(Integer, nullable=False)
    emisor_tipo = Column(String, nullable=False)  # "adoptante" o "albergue"
    receptor_id = Column(Integer, nullable=False)
    receptor_tipo = Column(String, nullable=False)
    contenido = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
