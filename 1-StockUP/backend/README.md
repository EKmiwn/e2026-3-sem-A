# StockUP – Strandvejsristeriet – prototype

Lager af grønne kaffesække (80 kg) og salgsklare poser. Ristning trækker altid 25 kg, sække får status PAA_LAGER → I_BRUG → REST → TOM, og alle ændringer logges i en append-only bevægelseslog.

Kravgrundlag: [`../README.md`](../README.md)

## Kør prototypen

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # første gang
pip install -r requirements.txt                       # første gang
python app.py
```

Åbn **http://localhost:5101** – Flask serverer både API'et (`/api/...`) og frontenden fra `../frontend`.
Er porten optaget, vælger serveren selv den næste ledige port og skriver adressen i terminalen
(fx ` * Port 5101 er optaget – bruger port 5102 i stedet`). Du kan også vælge port selv med `PORT=5200 python app.py`.
`frontend/index.html` kan også åbnes direkte fra disken. Så kalder den `http://localhost:5101/api` (attributten `data-api-port` i `index.html`).

Databasen `backend/database.db` (SQLite3) oprettes og fyldes med fiktive testdata fra `seed.sql` ved første start.
Nulstil den med `python database.py --reset`.

## Struktur

```
backend/
  app.py            logiklag: forretningsregler og endepunkter for netop dette projekt
  core.py           fælles for alle prototyper: Flask-app, JSON-fejl, CORS og generisk CRUD
  database.py       fælles for alle prototyper: SQLite3-forbindelse og hjælpefunktioner
  schema.sql        tabeller: green_coffee, sack, product, roast, sale, movement
  seed.sql          fiktive testdata
  requirements.txt
frontend/
  index.html        skærmbilleder: Dashboard · Registrér ristning/salg/modtag sæk · CRUD for råkaffe og varer · Bevægelser
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
| `GET` | `/api/dashboard` | Nøgletal, sække, varer og seneste bevægelser i ét kald. |
| `GET` | `/api/green-coffees` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/green-coffees` | Opret (CRUD) |
| `DELETE` | `/api/green-coffees/<item_id>` | Slet (CRUD) |
| `GET` | `/api/green-coffees/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/green-coffees/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/health` | Systemstatus |
| `GET` | `/api/movements` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `GET` | `/api/movements/<item_id>` | Hent én (CRUD) |
| `GET` | `/api/products` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/products` | Opret (CRUD) |
| `DELETE` | `/api/products/<item_id>` | Slet (CRUD) |
| `GET` | `/api/products/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/products/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/roasts` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/roasts` | Registrér ristning: trækker 25 kg fra sækken og lægger poser til varen. |
| `GET` | `/api/roasts/<item_id>` | Hent én (CRUD) |
| `DELETE` | `/api/roasts/<roast_id>` | Fortryd ristning – kun hvis poserne ikke allerede er solgt. |
| `GET` | `/api/sacks` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/sacks` | Opret (CRUD) |
| `DELETE` | `/api/sacks/<item_id>` | Slet (CRUD) |
| `GET` | `/api/sacks/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/sacks/<item_id>` | Opdatér (CRUD) |
| `POST` | `/api/sacks/<sack_id>/close` | Afslut restmængde under 25 kg – sækken tømmes og bliver TOM. |
| `GET` | `/api/sacks/roastable` | Sække med mindst 25 kg tilbage. |
| `GET` | `/api/sales` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/sales` | Registrér salg af poser. |
| `GET` | `/api/sales/<item_id>` | Hent én (CRUD) |
