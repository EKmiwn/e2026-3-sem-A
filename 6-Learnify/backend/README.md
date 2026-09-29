# Learnify – Elevevaluering (Læringsrum 2.0) – prototype

Elever logger ind og besvarer ugentlige spørgsmål om trivsel, læring, møbler og miljø. Lærere ser samlede, anonyme resultater med procenttal og udvikling over tid. Resultater vises først, når mindst 3 elever har svaret.

Kravgrundlag: [`../Kravspecifikation.md`](../Kravspecifikation.md)

## Kør prototypen

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # første gang
pip install -r requirements.txt                       # første gang
python app.py
```

Åbn **http://localhost:5106** – Flask serverer både API'et (`/api/...`) og frontenden fra `../frontend`.
Er porten optaget, vælger serveren selv den næste ledige port og skriver adressen i terminalen
(fx ` * Port 5106 er optaget – bruger port 5107 i stedet`). Du kan også vælge port selv med `PORT=5200 python app.py`.
`frontend/index.html` kan også åbnes direkte fra disken. Så kalder den `http://localhost:5106/api` (attributten `data-api-port` i `index.html`).

Databasen `backend/database.db` (SQLite3) oprettes og fyldes med fiktive testdata fra `seed.sql` ved første start.
Nulstil den med `python database.py --reset`.

## Struktur

```
backend/
  app.py            logiklag: forretningsregler og endepunkter for netop dette projekt
  core.py           fælles for alle prototyper: Flask-app, JSON-fejl, CORS og generisk CRUD
  database.py       fælles for alle prototyper: SQLite3-forbindelse og hjælpefunktioner
  schema.sql        tabeller: school, class, student, teacher, question, response, answer
  seed.sql          fiktive testdata
  requirements.txt
frontend/
  index.html        skærmbilleder: Login · Besvar · Min udvikling · Resultater · Udvikling over tid · Skoleoverblik · Spørgsmål og elever
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
| `GET` | `/api/classes` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/classes` | Opret (CRUD) |
| `DELETE` | `/api/classes/<item_id>` | Slet (CRUD) |
| `GET` | `/api/classes/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/classes/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/health` | Systemstatus |
| `POST` | `/api/login` | Log ind med brugernavn – returnerer rolle (elev, lærer, administrator). |
| `GET` | `/api/overview` | Virksomheds-/skolevisning (Læringsrum 2.0): alle klasser med seneste resultat og udvikling. |
| `GET` | `/api/questions` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/questions` | Opret (CRUD) |
| `DELETE` | `/api/questions/<item_id>` | Slet (CRUD) |
| `GET` | `/api/questions/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/questions/<item_id>` | Opdatér (CRUD) |
| `POST` | `/api/responses` | Elevens ugentlige besvarelse. Returnerer personlig feedback. |
| `GET` | `/api/results` | Samlet resultat for en klasse (eller hele skolen) i en periode: gennemsnit og procenttal. |
| `GET` | `/api/results/trend` | Sammenlign svar over tid: gennemsnit og andel positive svar pr. kategori pr. uge. |
| `GET` | `/api/schools` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/schools` | Opret (CRUD) |
| `DELETE` | `/api/schools/<item_id>` | Slet (CRUD) |
| `GET` | `/api/schools/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/schools/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/students` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/students` | Opret (CRUD) |
| `DELETE` | `/api/students/<item_id>` | Slet (CRUD) |
| `GET` | `/api/students/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/students/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/students/<student_id>/history` | Elevens egen udvikling over tid pr. kategori. |
| `GET` | `/api/survey` | Aktive spørgsmål og om eleven allerede har svaret i denne uge. |
| `GET` | `/api/teachers` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/teachers` | Opret (CRUD) |
| `DELETE` | `/api/teachers/<item_id>` | Slet (CRUD) |
| `GET` | `/api/teachers/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/teachers/<item_id>` | Opdatér (CRUD) |
