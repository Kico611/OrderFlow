import os
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import redis
import json
from database import engine, Base, SessionLocal
from models import Item

# Kreiranje baze podataka (ako već ne postoji)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Postavljanje postavki za spajanje na bazu podataka i Redis
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)

# Provjera povezanosti s Redisom
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    redis_client.ping()
except redis.ConnectionError:
    raise HTTPException(status_code=500, detail="Nije moguće povezati se s Redis poslužiteljem")

# Funkcija za dobivanje sesije baze podataka
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pomoćna funkcija za pretvaranje objekta u rječnik (bez metapodataka SQLAlchemy-a)
def item_to_dict(item):
    item_dict = item.__dict__
    if '_sa_instance_state' in item_dict:
        del item_dict['_sa_instance_state']
    return item_dict

@app.get("/")
def read_root():
    # Početna ruta
    return {"message": "Pozdrav svijete"}

@app.post("/items/")
def create_item(name: str, description: str, db: Session = Depends(get_db)):
    # Kreiranje novog itema u bazi podataka
    item = Item(name=name, description=description)
    db.add(item)
    db.commit()
    db.refresh(item)

    # Brisanje predmemorije kako bi se osigurali svježi podaci
    redis_client.delete("items_cache")

    return {
        "item": item_to_dict(item),
        "redis_debug": "items_cache očišćen"
    }

@app.get("/items/")
def read_items(db: Session = Depends(get_db)):
    # Provjera postoji li predmemorirani popis u Redis-u
    cached_items = redis_client.get("items_cache")
    if cached_items:
        return {
            "items": json.loads(cached_items),
            "redis_debug": "Keširanje uspješno!"
        }

    # Ako predmemorija ne postoji, dohvaćanje svih itema iz baze podataka
    items = db.query(Item).all()
    item_list = [item_to_dict(item) for item in items]

    # Spremanje popisa u Redis
    redis_client.set("items_cache", json.dumps(item_list))
    return {
        "items": item_list,
        "redis_debug": "items_cache ažuriran"
    }

@app.get("/items/{item_id}")
def read_item(item_id: int, db: Session = Depends(get_db)):
    # Provjera postoji li pojedinačni item u predmemoriji
    cached_item = redis_client.get(f"item_{item_id}")
    if cached_item:
        return {
            "item": json.loads(cached_item),
            "redis_debug": "Keširanje uspješno!"
        }

    # Ako predmemorija ne postoji, dohvaćanje itema iz baze podataka
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item nije pronađen")

    # Spremanje itema u Redis
    item_dict = item_to_dict(item)
    redis_client.set(f"item_{item_id}", json.dumps(item_dict))
    return {
        "item": item_dict,
        "redis_debug": "Ne postoji u redisu, item predmemoriran u redis"
    }

@app.put("/items/{item_id}")
def update_item(item_id: int, name: str, description: str, db: Session = Depends(get_db)):
    # Ažuriranje postojećeg itema u bazi podataka
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item nije pronađen")

    item.name = name
    item.description = description
    db.commit()
    db.refresh(item)

    # Ažuriranje predmemorije za pojedinačni item i brisanje predmemorije popisa
    item_dict = item_to_dict(item)
    redis_client.set(f"item_{item_id}", json.dumps(item_dict))
    redis_client.delete("items_cache")
    return {
        "item": item_dict,
        "redis_debug": "Predmemorija itema ažurirana, items_cache očišćen"
    }

@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    # Brisanje itema iz baze podataka
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item nije pronađen")

    db.delete(item)
    db.commit()

    # Brisanje predmemorije za pojedinačni item i cijeli popis
    redis_client.delete(f"item_{item_id}")
    redis_client.delete("items_cache")
    return {
        "message": "Item obrisan",
        "redis_debug": "Predmemorija itema obrisana, items_cache očišćen"
    }
