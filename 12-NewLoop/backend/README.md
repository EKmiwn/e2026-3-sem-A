# LoopAAS – New Loop – prototype

Brugere registrerer returnering af New Loop-emballage ved at scanne emballagens kode og optjener LoopPoints (kop 10, skål 15, madboks 20). De ser deres pointsaldo, niveau og badges, indløser rewards hos samarbejdspartnere og ser deres historik. Samarbejdspartneren bekræfter indløsningskoden, og New Loop ser nøgletal og kan tilføje flere partnere og rewards. Brugeren vælges i toppen (simuleret login).

Kravgrundlag: [`../Kravspecifikationer.md`](../Kravspecifikationer.md)

## Kør prototypen

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # første gang
pip install -r requirements.txt                       # første gang
python app.py
```

Åbn **http://localhost:5112** – Flask serverer både API'et (`/api/...`) og frontenden fra `../frontend`.
Er porten optaget, vælger serveren selv den næste ledige port og skriver adressen i terminalen
(fx ` * Port 5112 er optaget – bruger port 5113 i stedet`). Du kan også vælge port selv med `PORT=5200 python app.py`.
`frontend/index.html` kan også åbnes direkte fra disken. Så kalder den `http://localhost:5112/api` (attributten `data-api-port` i `index.html`).

Databasen `backend/database.db` (SQLite3) oprettes og fyldes med fiktive testdata fra `seed.sql` ved første start.
Nulstil den med `python database.py --reset`.

## Struktur

```
backend/
  app.py            logiklag: forretningsregler og endepunkter for netop dette projekt
  core.py           fælles for alle prototyper: Flask-app, JSON-fejl, CORS og generisk CRUD
  database.py       fælles for alle prototyper: SQLite3-forbindelse og hjælpefunktioner
  schema.sql        tabeller: setting, app_user, location, package, return_event, partner, reward, redemption
  seed.sql          fiktive testdata
  requirements.txt
frontend/
  index.html        skærmbilleder: Min side · Returnér · Rewards · Historik · Samarbejdspartner · New Loop
  style.css         fælles stylesheet (projektfarver står i index.html)
  api.js            fælles klient: fetch() + JSON og små DOM-hjælpere
  app.js            præsentationslag for netop dette projekt
```

Klienten og serveren taler kun sammen via HTTP og JSON. Svarene vises i DOM'en, og det seneste
rå JSON-svar kan ses nederst på siden under "Seneste JSON-svar fra API'et".

Fejl returneres altid som JSON: `{"error": "…", "path": "/api/…"}` med statuskode 400, 403, 404, 409 eller 429.

## API

| Metode | Endepunkt | Beskrivelse |
| --- | --- | --- |
| `GET` | `/api/catalog` | Aktive rewards med partner, og hvor mange point brugeren mangler (?user_id=). |
| `GET` | `/api/health` | Systemstatus |
| `GET` | `/api/locations` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/locations` | Opret (CRUD) |
| `DELETE` | `/api/locations/<item_id>` | Slet (CRUD) |
| `GET` | `/api/locations/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/locations/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/packages/open` | Udleverede emballager, der endnu ikke er returneret (eksempelkoder til at afprøve en returnering). |
| `GET` | `/api/partners` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/partners` | Opret (CRUD) |
| `DELETE` | `/api/partners/<item_id>` | Slet (CRUD) |
| `GET` | `/api/partners/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/partners/<item_id>` | Opdatér (CRUD) |
| `POST` | `/api/redemptions` | Indløs en reward: pointsaldoen kontrolleres og reduceres, og brugeren får en kode til partneren. |
| `POST` | `/api/redemptions/verify` | Samarbejdspartneren indtaster koden og markerer rewarden som brugt. |
| `POST` | `/api/returns` | Registrér en returnering ved at scanne emballagens kode. Godkendes den, tildeles LoopPoints med det samme. |
| `GET` | `/api/rewards` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/rewards` | Opret (CRUD) |
| `DELETE` | `/api/rewards/<item_id>` | Slet (CRUD) |
| `GET` | `/api/rewards/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/rewards/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/settings` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/settings` | Opret (CRUD) |
| `DELETE` | `/api/settings/<item_id>` | Slet (CRUD) |
| `GET` | `/api/settings/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/settings/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/stats` | Nøgletal for New Loop: returneringer, returrate, point og rewards pr. partner. |
| `GET` | `/api/users` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/users` | Opret (CRUD) |
| `DELETE` | `/api/users/<item_id>` | Slet (CRUD) |
| `GET` | `/api/users/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/users/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/users/<user_id>/history` | Returneringer og indløsninger samlet, nyeste først, med pointændring. |
| `GET` | `/api/users/<user_id>/profile` | Brugerens profil: pointsaldo, niveau, ugestreak og badges (FR04). |
