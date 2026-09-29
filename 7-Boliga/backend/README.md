# Boliga Insight Hub – prototype

Samler Boliga.dk-data (pris, liggetid, prisfald, AI-vurdering), DinGeo-data og tvangsauktioner for en bolig. AI-sparringspartneren er en regelbaseret prototype, der kun svarer ud fra boligens data og viser kilder – den kan senere skiftes til et LLM uden at ændre API'et.

Kravgrundlag: [`../Kravspecifikation.md`](../Kravspecifikation.md)

## Kør prototypen

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # første gang
pip install -r requirements.txt                       # første gang
python app.py
```

Åbn **http://localhost:5107** – Flask serverer både API'et (`/api/...`) og frontenden fra `../frontend`.
Er porten optaget, vælger serveren selv den næste ledige port og skriver adressen i terminalen
(fx ` * Port 5107 er optaget – bruger port 5108 i stedet`). Du kan også vælge port selv med `PORT=5200 python app.py`.
`frontend/index.html` kan også åbnes direkte fra disken. Så kalder den `http://localhost:5107/api` (attributten `data-api-port` i `index.html`).

Databasen `backend/database.db` (SQLite3) oprettes og fyldes med fiktive testdata fra `seed.sql` ved første start.
Nulstil den med `python database.py --reset`.

## Struktur

```
backend/
  app.py            logiklag: forretningsregler og endepunkter for netop dette projekt
  core.py           fælles for alle prototyper: Flask-app, JSON-fejl, CORS og generisk CRUD
  database.py       fælles for alle prototyper: SQLite3-forbindelse og hjælpefunktioner
  schema.sql        tabeller: property, price_change, geo_data, area_sale, auction, user, saved_property, conversation, message
  seed.sql          fiktive testdata
  requirements.txt
frontend/
  index.html        skærmbilleder: Søg bolig · Insight Hub + AI-chat · Gemte og sammenlign · Boligdata (admin)
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
| `GET` | `/api/compare` | Sammenlign 2–4 boliger: ?ids=1,5 |
| `GET` | `/api/conversations` | Gemt samtale for bruger og bolig: ?user_id=1&property_id=1 |
| `GET` | `/api/geo-data` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/geo-data` | Opret (CRUD) |
| `DELETE` | `/api/geo-data/<item_id>` | Slet (CRUD) |
| `GET` | `/api/geo-data/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/geo-data/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/health` | Systemstatus |
| `GET` | `/api/properties` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/properties` | Opret (CRUD) |
| `DELETE` | `/api/properties/<item_id>` | Slet (CRUD) |
| `GET` | `/api/properties/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/properties/<item_id>` | Opdatér (CRUD) |
| `POST` | `/api/properties/<property_id>/ask` | Stil et spørgsmål til AI-sparringspartneren. Svar og kilder logges. |
| `GET` | `/api/properties/<property_id>/insight` | Samlet data for boligen: Boliga.dk, marked, DinGeo, tvangsauktioner og AI-resumé. |
| `GET` | `/api/properties/search` | Søg boliger: ?q=&max_price=&min_size=&property_type= |
| `GET` | `/api/users` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/users` | Opret (CRUD) |
| `DELETE` | `/api/users/<item_id>` | Slet (CRUD) |
| `GET` | `/api/users/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/users/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/users/<user_id>/saved` | Brugerens gemte boliger. |
| `POST` | `/api/users/<user_id>/saved` | Gem en bolig. |
| `DELETE` | `/api/users/<user_id>/saved/<property_id>` | Fjern en gemt bolig. |
