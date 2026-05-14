from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    nom: str
    prenom: str
    email: str
    password: str
    classe: str

class UserOut(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str
    classe: str
    created_at: Optional[datetime]
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

class CoursCreate(BaseModel):
    matiere: str
    professeur: Optional[str] = ""
    classe: str
    salle: Optional[str] = ""
    jour: str
    heure_debut: str
    heure_fin: str
    couleur: Optional[str] = "#4F46E5"

class CoursOut(CoursCreate):
    id: int
    user_id: int
    class Config:
        orm_mode = True

class DevoirCreate(BaseModel):
    titre: str
    matiere: str
    description: Optional[str] = ""
    date_remise: str
    priorite: Optional[str] = "normale"

class DevoirUpdate(BaseModel):
    titre: Optional[str]
    matiere: Optional[str]
    description: Optional[str]
    date_remise: Optional[str]
    priorite: Optional[str]
    termine: Optional[bool]

class DevoirOut(DevoirCreate):
    id: int
    user_id: int
    termine: bool
    created_at: Optional[datetime]
    class Config:
        orm_mode = True

class NoteCreate(BaseModel):
    titre: str
    contenu: Optional[str] = ""
    matiere: Optional[str] = ""
    couleur: Optional[str] = "#FEF3C7"

class NoteOut(NoteCreate):
    id: int
    user_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    class Config:
        orm_mode = True
