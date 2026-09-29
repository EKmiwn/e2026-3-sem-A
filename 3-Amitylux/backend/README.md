# Amitylux – Experience Finder – prototype

Needs assessment → comparison of public/private/customised → transparent recommendation with reasons → filters → add-ons, guide wishes and contact → receipt and a standardised brief for staff. UI in English (NF-02).

Kravgrundlag: [`../Kravspecifikation.md`](../Kravspecifikation.md)

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
  app.py            logiklag: forretningsregler og endepunkter for netop dette projekt
  core.py           fælles for alle prototyper: Flask-app, JSON-fejl, CORS og generisk CRUD
  database.py       fælles for alle prototyper: SQLite3-forbindelse og hjælpefunktioner
  schema.sql        tabeller: destination, product_type, experience, addon, inquiry, help_request
  seed.sql          fiktive testdata
  requirements.txt
frontend/
  index.html        skærmbilleder: Your trip · Compare · Recommendation + filters · Summary & send · Staff: inquiries · “Talk to a person” on every step
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
| `GET` | `/api/experiences/search` | Filters: destination_id, type, price_level (max), language, group_size, interest. |
| `GET` | `/api/health` | Systemstatus |
| `GET` | `/api/help-requests` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/help-requests` | Opret (CRUD) |
| `DELETE` | `/api/help-requests/<item_id>` | Slet (CRUD) |
| `GET` | `/api/help-requests/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/help-requests/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/inquiries` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/inquiries` | Send a structured request – returns a receipt and the staff brief (F-08). |
| `DELETE` | `/api/inquiries/<inquiry_id>` | Delete an inquiry. |
| `PUT` | `/api/inquiries/<inquiry_id>` | Update the status of an inquiry. |
| `GET` | `/api/inquiries/<inquiry_id>/brief` | Standardised brief for staff (F-15). |
| `GET` | `/api/inquiries/<item_id>` | Hent én (CRUD) |
| `GET` | `/api/product-types` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/product-types` | Opret (CRUD) |
| `DELETE` | `/api/product-types/<item_id>` | Slet (CRUD) |
| `GET` | `/api/product-types/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/product-types/<item_id>` | Opdatér (CRUD) |
| `POST` | `/api/recommendations` | Recommendation: primary type + up to two alternatives, each with reasons (F-03). |
