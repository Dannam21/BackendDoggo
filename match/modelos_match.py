from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from database import Base
from sqlalchemy.sql import func # type: ignore

#=====PREGUNTAS Y RESPUESTAS=======
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

