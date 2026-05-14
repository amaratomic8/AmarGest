from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    classe = Column(String, nullable=False)
    created_at = Column(DateTime)
    cours = relationship("Cours", back_populates="user", cascade="all, delete")
    devoirs = relationship("Devoir", back_populates="user", cascade="all, delete")
    notes = relationship("Note", back_populates="user", cascade="all, delete")

class Cours(Base):
    __tablename__ = "cours"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    matiere = Column(String, nullable=False)
    professeur = Column(String)
    classe = Column(String, nullable=False)
    salle = Column(String)
    jour = Column(String, nullable=False)
    heure_debut = Column(String, nullable=False)
    heure_fin = Column(String, nullable=False)
    couleur = Column(String, default="#4F46E5")
    user = relationship("User", back_populates="cours")

class Devoir(Base):
    __tablename__ = "devoirs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    titre = Column(String, nullable=False)
    matiere = Column(String, nullable=False)
    description = Column(Text)
    date_remise = Column(String, nullable=False)
    priorite = Column(String, default="normale")
    termine = Column(Boolean, default=False)
    created_at = Column(DateTime)
    user = relationship("User", back_populates="devoirs")

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    titre = Column(String, nullable=False)
    contenu = Column(Text)
    matiere = Column(String)
    couleur = Column(String, default="#FEF3C7")
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    user = relationship("User", back_populates="notes")
