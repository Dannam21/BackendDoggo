from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

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

