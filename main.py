from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import jwt
import bcrypt
import models, schemas, database

app = FastAPI(title="AmarGest API", description="API pour la gestion de l'emploi du temps étudiant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:80",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
SECRET_KEY = "amargest_secret_key_2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

database.Base.metadata.create_all(bind=database.engine)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les informations d'identification",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# ─── AUTH ───────────────────────────────────────────────────────────────────

@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    db_user = models.User(
        nom=user.nom,
        prenom=user.prenom,
        email=user.email,
        hashed_password=hash_password(user.password),
        classe=user.classe,
        created_at=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    token = create_token({"sub": user.email}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": token, "token_type": "bearer", "user": schemas.UserOut.from_orm(user)}

@app.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user

# ─── COURS ──────────────────────────────────────────────────────────────────

@app.get("/cours", response_model=List[schemas.CoursOut])
def get_cours(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Cours).filter(models.Cours.user_id == user.id).all()

@app.post("/cours", response_model=schemas.CoursOut)
def create_cours(cours: schemas.CoursCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    db_cours = models.Cours(**cours.dict(), user_id=user.id)
    db.add(db_cours)
    db.commit()
    db.refresh(db_cours)
    return db_cours

@app.put("/cours/{cours_id}", response_model=schemas.CoursOut)
def update_cours(cours_id: int, cours: schemas.CoursCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    db_cours = db.query(models.Cours).filter(models.Cours.id == cours_id, models.Cours.user_id == user.id).first()
    if not db_cours:
        raise HTTPException(status_code=404, detail="Cours non trouvé")
    for key, value in cours.dict().items():
        setattr(db_cours, key, value)
    db.commit()
    db.refresh(db_cours)
    return db_cours

@app.delete("/cours/{cours_id}")
def delete_cours(cours_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    db_cours = db.query(models.Cours).filter(models.Cours.id == cours_id, models.Cours.user_id == user.id).first()
    if not db_cours:
        raise HTTPException(status_code=404, detail="Cours non trouvé")
    db.delete(db_cours)
    db.commit()
    return {"message": "Cours supprimé avec succès"}

# ─── DEVOIRS ────────────────────────────────────────────────────────────────

@app.get("/devoirs", response_model=List[schemas.DevoirOut])
def get_devoirs(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Devoir).filter(models.Devoir.user_id == user.id).all()

@app.post("/devoirs", response_model=schemas.DevoirOut)
def create_devoir(devoir: schemas.DevoirCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    db_devoir = models.Devoir(**devoir.dict(), user_id=user.id, termine=False, created_at=datetime.utcnow())
    db.add(db_devoir)
    db.commit()
    db.refresh(db_devoir)
    return db_devoir

@app.put("/devoirs/{devoir_id}", response_model=schemas.DevoirOut)
def update_devoir(devoir_id: int, devoir: schemas.DevoirUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    db_devoir = db.query(models.Devoir).filter(models.Devoir.id == devoir_id, models.Devoir.user_id == user.id).first()
    if not db_devoir:
        raise HTTPException(status_code=404, detail="Devoir non trouvé")
    for key, value in devoir.dict(exclude_none=True).items():
        setattr(db_devoir, key, value)
    db.commit()
    db.refresh(db_devoir)
    return db_devoir

@app.delete("/devoirs/{devoir_id}")
def delete_devoir(devoir_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    db_devoir = db.query(models.Devoir).filter(models.Devoir.id == devoir_id, models.Devoir.user_id == user.id).first()
    if not db_devoir:
        raise HTTPException(status_code=404, detail="Devoir non trouvé")
    db.delete(db_devoir)
    db.commit()
    return {"message": "Devoir supprimé avec succès"}

# ─── NOTES ──────────────────────────────────────────────────────────────────

@app.get("/notes", response_model=List[schemas.NoteOut])
def get_notes(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Note).filter(models.Note.user_id == user.id).order_by(models.Note.updated_at.desc()).all()

@app.post("/notes", response_model=schemas.NoteOut)
def create_note(note: schemas.NoteCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    now = datetime.utcnow()
    db_note = models.Note(**note.dict(), user_id=user.id, created_at=now, updated_at=now)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

@app.put("/notes/{note_id}", response_model=schemas.NoteOut)
def update_note(note_id: int, note: schemas.NoteCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    db_note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.user_id == user.id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note non trouvée")
    for key, value in note.dict().items():
        setattr(db_note, key, value)
    db_note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_note)
    return db_note

@app.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    db_note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.user_id == user.id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note non trouvée")
    db.delete(db_note)
    db.commit()
    return {"message": "Note supprimée avec succès"}

# ─── STATS DASHBOARD ────────────────────────────────────────────────────────

@app.get("/stats")
def get_stats(db: Session = Depends(get_db), user=Depends(get_current_user)):
    total_cours = db.query(models.Cours).filter(models.Cours.user_id == user.id).count()
    total_devoirs = db.query(models.Devoir).filter(models.Devoir.user_id == user.id).count()
    devoirs_termines = db.query(models.Devoir).filter(models.Devoir.user_id == user.id, models.Devoir.termine == True).count()
    devoirs_en_attente = total_devoirs - devoirs_termines
    total_notes = db.query(models.Note).filter(models.Note.user_id == user.id).count()
    
    today = datetime.utcnow().date()
    in_two_days = today + timedelta(days=2)
    devoirs_urgents = db.query(models.Devoir).filter(
        models.Devoir.user_id == user.id,
        models.Devoir.termine == False,
        models.Devoir.date_remise <= str(in_two_days)
    ).all()
    
    return {
        "total_cours": total_cours,
        "total_devoirs": total_devoirs,
        "devoirs_termines": devoirs_termines,
        "devoirs_en_attente": devoirs_en_attente,
        "total_notes": total_notes,
        "devoirs_urgents": [schemas.DevoirOut.from_orm(d) for d in devoirs_urgents]
    }
