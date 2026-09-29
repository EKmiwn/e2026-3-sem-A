# Solum – Vidensdeling og fejlfinding – prototype

Medarbejderen vælger maskine og symptom, får rangerede trin-for-trin-guides (tilpasset erfaringsniveau og løsningsrate) og logger om fejlen blev løst. Erfarne medarbejdere skriver vidensartikler, og driftsledelsen ser et kompetenceoverblik.

Kravgrundlag: [`../Kravspecifikation-Vidensdeling-App-Solum-Samlet.md`](../Kravspecifikation-Vidensdeling-App-Solum-Samlet.md)

## Kør prototypen

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # første gang
pip install -r requirements.txt                       # første gang
python app.py
```

Åbn **http://localhost:5105** – Flask serverer både API'et (`/api/...`) og frontenden fra `../frontend`.
Er porten optaget, vælger serveren selv den næste ledige port og skriver adressen i terminalen
(fx ` * Port 5105 er optaget – bruger port 5106 i stedet`). Du kan også vælge port selv med `PORT=5200 python app.py`.
`frontend/index.html` kan også åbnes direkte fra disken. Så kalder den `http://localhost:5105/api` (attributten `data-api-port` i `index.html`).

Databasen `backend/database.db` (SQLite3) oprettes og fyldes med fiktive testdata fra `seed.sql` ved første start.
Nulstil den med `python database.py --reset`.

## Struktur

```
backend/
  app.py            logiklag: forretningsregler og endepunkter for netop dette projekt
  core.py           fælles for alle prototyper: Flask-app, JSON-fejl, CORS og generisk CRUD
  database.py       fælles for alle prototyper: SQLite3-forbindelse og hjælpefunktioner
  schema.sql        tabeller: employee, machine, competence, article, fault_log
  seed.sql          fiktive testdata
  requirements.txt
frontend/
  index.html        skærmbilleder: Maskiner · Fejlfinding · Bidrag med viden · Kompetenceoverblik · Fejllog
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
| `GET` | `/api/articles` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/articles` | Opret (CRUD) |
| `DELETE` | `/api/articles/<item_id>` | Slet (CRUD) |
| `GET` | `/api/articles/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/articles/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/articles/search` | Søg guides uden at logge en fejl: ?machine_id=1&q=stopper&employee_id=3 |
| `GET` | `/api/competence-matrix` | Kompetenceoverblik: medarbejdere × maskiner. |
| `GET` | `/api/competences` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/competences` | Opret (CRUD) |
| `DELETE` | `/api/competences/<item_id>` | Slet (CRUD) |
| `GET` | `/api/competences/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/competences/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/employees` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/employees` | Opret (CRUD) |
| `DELETE` | `/api/employees/<item_id>` | Slet (CRUD) |
| `GET` | `/api/employees/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/employees/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/faults` | Seneste fejl i loggen. |
| `POST` | `/api/faults` | FejlRegistreret: medarbejder vælger maskine + symptom. Returnerer rangerede guides (GuideVist). |
| `POST` | `/api/faults/<fault_id>/resolve` | FejlLøst / FejlUløst. Uløst giver en liste over kolleger at eskalere til. |
| `GET` | `/api/health` | Systemstatus |
| `GET` | `/api/machines` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/machines` | Opret (CRUD) |
| `DELETE` | `/api/machines/<item_id>` | Slet (CRUD) |
| `GET` | `/api/machines/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/machines/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/machines/<machine_id>/details` | Maskineskærm: hyppige fejl (historiske fejlmønstre), kompetente kolleger og guides. |
| `GET` | `/api/machines/overview` | Startskærm: maskiner med antal godkendte operatører og sårbarhed ved fravær. |
