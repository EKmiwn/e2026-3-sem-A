# Amitylux – Experience Compass – prototype

Start → preferences → check answers → up to three explained suggestions (adjust and see what changed) → compare public/private/customised → structured request with preview and receipt. Staff view with briefs, help requests and catalogue check. UI in English.

Kravgrundlag: [`../kravspecifikation-2.md`](../kravspecifikation-2.md) (K1–K12) · Idé 1 i [`../prototype-ideer.md`](../prototype-ideer.md)

## Kør prototypen

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # første gang
pip install -r requirements.txt                       # første gang
python app.py
```

Åbn **http://localhost:5103** – Flask serverer både API'et (`/api/...`) og frontenden fra `../frontend`.
Er porten optaget, vælger serveren selv den næste ledige port og skriver adressen i terminalen
(fx ` * Port 5103 er optaget – bruger port 5104 i stedet`). Du kan også vælge port selv med `PORT=5200 python app.py`.
`frontend/index.html` kan også åbnes direkte fra disken. Så kalder den `http://localhost:5103/api` (attributten `data-api-port` i `index.html`).

Databasen `backend/database.db` (SQLite3) oprettes og fyldes med fiktive testdata fra `seed.sql` ved første start.
Nulstil den med `python database.py --reset`.

## Struktur

```
backend/
  app.py            endepunkter, katalogkontrol (K9) og brief (K8)
  compass.py        matchmotor uden Flask/SQLite: validering, begrundelser, roller, ændringer
  tests.py          automatiske tests af K1–K12 (python tests.py)
  core.py           fælles for alle prototyper: Flask-app, JSON-fejl, CORS og generisk CRUD
  database.py       fælles for alle prototyper: SQLite3-forbindelse og hjælpefunktioner
  schema.sql        tabeller: destination, product_type, experience, value_claim, addon, inquiry, help_request
  seed.sql          fiktive testdata
  requirements.txt
frontend/
  index.html        seks trin (Start · Preferences · Check · Suggestions · Compare · Request), Staff view, “Talk to a person”
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
| `GET` | `/api/addons` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/addons` | Opret (CRUD) |
| `DELETE` | `/api/addons/<item_id>` | Slet (CRUD) |
| `GET` | `/api/addons/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/addons/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/catalogue` | The approved catalogue in the same card structure as the suggestions (K5, K11). |
| `GET` | `/api/catalogue/audit` | K9: for Amitylux – every row is checked for approval, missing K5 fields and undocumented value claims. |
| `POST` | `/api/compass` | Up to three explained suggestions. Send {"preferences": {...}, "previous": {...}} to see what changed (K3). |
| `GET` | `/api/destinations` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/destinations` | Opret (CRUD) |
| `DELETE` | `/api/destinations/<item_id>` | Slet (CRUD) |
| `GET` | `/api/destinations/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/destinations/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/experiences` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/experiences` | Opret (CRUD) |
| `DELETE` | `/api/experiences/<item_id>` | Slet (CRUD) |
| `GET` | `/api/experiences/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/experiences/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/health` | Systemstatus |
| `GET` | `/api/help-requests` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/help-requests` | K8: 'Talk to a person' from any step. The answers so far are attached, so nothing has to be repeated. |
| `GET` | `/api/help-requests/<item_id>` | Hent én (CRUD) |
| `GET` | `/api/inquiries` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/inquiries` | K8: save the structured request and return a receipt plus the staff brief. |
| `PUT` | `/api/inquiries/<inquiry_id>` | Update the status of an inquiry. |
| `GET` | `/api/inquiries/<inquiry_id>/brief` | Staff brief for one inquiry (K8). |
| `GET` | `/api/inquiries/<item_id>` | Hent én (CRUD) |
| `POST` | `/api/inquiries/preview` | K8: exactly what will be sent – nothing is saved. |
| `GET` | `/api/options` | Answer options for the preference flow (K1) – the same lists the engine validates against. |
| `GET` | `/api/product-types` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/product-types` | Opret (CRUD) |
| `DELETE` | `/api/product-types/<item_id>` | Slet (CRUD) |
| `GET` | `/api/product-types/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/product-types/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/value-claims` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/value-claims` | Opret (CRUD) |
| `DELETE` | `/api/value-claims/<item_id>` | Slet (CRUD) |
| `GET` | `/api/value-claims/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/value-claims/<item_id>` | Opdatér (CRUD) |

