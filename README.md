# 🛒 OrderFlow

Aplikacija za upravljanje narudžbama proizvoda, izrađena koristeći **FastAPI** i **Docker**.  
Deployana na **Oracle Cloud** infrastrukturi.

### 🔗 Live Demo
👉 [OrderFlow - API Dokumentacija (Swagger UI)](http://130.162.235.231:8000/docs)

---

## 📋 Opis

**OrderFlow** omogućuje:
- Upravljanje korisnicima, proizvodima, kategorijama, narudžbama i stavkama narudžbi.
- Korištenje REST API-ja za kreiranje, dohvaćanje, ažuriranje i brisanje podataka.
- Brzu i efikasnu obradu narudžbi kroz jednostavno sučelje za API dokumentaciju (Swagger UI).
---

## 🛠️ Tehnologije korištene

- **FastAPI** (Python web framework za brze API-je)
- **Docker** (kontejnerizacija aplikacije)
- **Uvicorn** (ASGI server za pokretanje FastAPI aplikacije)
- **SQLAlchemy** (ORM za rad s bazom podataka)
- **PostgreSQL** (relacijska baza podataka)
- **Pydantic** (validacija podataka)
- **Swagger UI** (automatska dokumentacija API-ja)
- **Oracle Cloud Infrastructure** (hostanje aplikacije)

---

## 🚀 Pokretanje projekta lokalno

### Opcija 1: Pokretanje pomoću Dockera

1. Kloniraj repozitorij:
   ```bash
   git clone https://github.com/Kico611/OrderFlow.git
   ```

2. Uđi u direktorij projekta:
   ```bash
   cd OrderFlow
   ```

3. Pokreni aplikaciju s Docker Compose:
   ```bash
   docker-compose up --build
   ```

4. Aplikacija će biti dostupna na:
   ```
   http://localhost:8000/docs
   ```

> Napomena: Docker Compose automatski podiže i FastAPI aplikaciju i PostgreSQL bazu podataka.

---

### Opcija 2: Pokretanje lokalno bez Dockera

1. Pokreni lokalnu PostgreSQL bazu i kreiraj bazu podataka npr. `orderflow`.

2. Postavi `DATABASE_URL` varijablu u `.env` fajlu:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/orderflow
   ```

3. Instaliraj potrebne Python pakete:
   ```bash
   pip install -r requirements.txt
   ```

4. Pokreni aplikaciju:
   ```bash
   uvicorn app.main:app --reload
   ```

5. Otvori Swagger dokumentaciju:
   ```
   http://localhost:8000/docs
   ```

---
## 📑 Funkcionalnosti

- ✅ CRUD operacije za korisnike, proizvode, kategorije, narudžbe i stavke narudžbi
- ✅ API dokumentacija putem Swagger UI
- ✅ Relacijska baza podataka (PostgreSQL)
- ✅ Dockerizirana aplikacija spremna za produkcijsko okruženje
- ✅ Jednostavno skaliranje i deployment na cloud (Oracle Cloud)

---


