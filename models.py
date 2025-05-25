from sqlalchemy import Column, Integer, String, ForeignKey
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
    albergue_id = Column(Integer, ForeignKey("albergue.id"))  # relación con la empresa

    albergue = relationship("Albergue", back_populates="mascotas")
