# Min Hessel – Kundeportal – prototype

Kunden ser sine biler på tværs af mærker, servicehistorik, reparationsstatus, aftaler og dokumenter og kan oprette, rette, aflyse og slette værkstedsbookinger. Kravspecifikationen nævner React og Node/Express – prototypen følger holdets fælles Flask + HTML/CSS/JS-struktur med samme tre-lags arkitektur.

Kravgrundlag: [`../kravspecifikation.md`](../kravspecifikation.md)

## Kør prototypen

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # første gang
pip install -r requirements.txt                       # første gang
python app.py
```

Åbn **http://localhost:5110** – Flask serverer både API'et (`/api/...`) og frontenden fra `../frontend`.
Er porten optaget, vælger serveren selv den næste ledige port og skriver adressen i terminalen
(fx ` * Port 5110 er optaget – bruger port 5111 i stedet`). Du kan også vælge port selv med `PORT=5200 python app.py`.
`frontend/index.html` kan også åbnes direkte fra disken. Så kalder den `http://localhost:5110/api` (attributten `data-api-port` i `index.html`).

Databasen `backend/database.db` (SQLite3) oprettes og fyldes med fiktive testdata fra `seed.sql` ved første start.
Nulstil den med `python database.py --reset`.

## Struktur

```
backend/
  app.py            logiklag: forretningsregler og endepunkter for netop dette projekt
  core.py           fælles for alle prototyper: Flask-app, JSON-fejl, CORS og generisk CRUD
  database.py       fælles for alle prototyper: SQLite3-forbindelse og hjælpefunktioner
  schema.sql        tabeller: customer, workshop, car, service_history, booking, repair, document
  seed.sql          fiktive testdata
  requirements.txt
frontend/
  index.html        skærmbilleder: Mine biler · Biloplysninger · Værkstedsbooking · Aftaler og dokumenter · Værksted (medarbejder)
  style.css         fælles stylesheet (projektfarver står i index.html)
  api.js            fælles klient: fetch() + JSON og små DOM-hjælpere
  app.js            præsentationslag for netop dette projekt
```

Klienten og serveren taler kun sammen via HTTP og JSON. Svarene vises i DOM'en, og det seneste
rå JSON-svar kan ses nederst på siden under "Seneste JSON-svar fra API'et".

Fejl returneres altid som JSON: `{"error": "…", "path": "/api/…"}` med statuskode 400, 401, 403, 404 eller 409.

## API

| Metode | Endepunkt | Beskrivelse |
| --- | --- | --- |
| `GET` | `/api/available-times` | Ledige tider på et værksted en given dato: ?workshop_id=1&date=2026-10-12 |
| `GET` | `/api/bookings` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/bookings` | Opret (CRUD) |
| `DELETE` | `/api/bookings/<item_id>` | Slet (CRUD) |
| `GET` | `/api/bookings/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/bookings/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/cars` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/cars` | Opret (CRUD) |
| `GET` | `/api/cars/<car_id>/details` | Biloplysninger, servicehistorik, reparationer og dokumenter for én bil. |
| `DELETE` | `/api/cars/<item_id>` | Slet (CRUD) |
| `GET` | `/api/cars/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/cars/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/customers` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/customers` | Opret (CRUD) |
| `GET` | `/api/customers/<customer_id>/overview` | Kundens biler med næste booking og reparationsstatus, bookinger, dokumenter og notifikationer. |
| `DELETE` | `/api/customers/<item_id>` | Slet (CRUD) |
| `GET` | `/api/customers/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/customers/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/documents` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/documents` | Opret (CRUD) |
| `DELETE` | `/api/documents/<item_id>` | Slet (CRUD) |
| `GET` | `/api/documents/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/documents/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/health` | Systemstatus |
| `GET` | `/api/repair-steps` | Trinene i en reparation, i rækkefølge. |
| `GET` | `/api/repairs` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/repairs` | Opret (CRUD) |
| `DELETE` | `/api/repairs/<item_id>` | Slet (CRUD) |
| `GET` | `/api/repairs/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/repairs/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/service-history` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/service-history` | Opret (CRUD) |
| `DELETE` | `/api/service-history/<item_id>` | Slet (CRUD) |
| `GET` | `/api/service-history/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/service-history/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/workshops` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/workshops` | Opret (CRUD) |
| `DELETE` | `/api/workshops/<item_id>` | Slet (CRUD) |
| `GET` | `/api/workshops/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/workshops/<item_id>` | Opdatér (CRUD) |
