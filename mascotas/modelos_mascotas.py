from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from database import Base
from sqlalchemy.sql import func # type: ignore

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
    imagen = relationship("Imagen")
    albergue = relationship("Albergue", back_populates="mascotas")

#=====IMAGEN=======
class Imagen(Base):
    __tablename__ = "imagenes"
    id = Column(Integer, primary_key=True, index=True)
    ruta = Column(String, nullable=False)

