# Learnify – Elevevaluering (Læringsrum 2.0) – prototype

Version 2: login som elev, lærer eller virksomhed med e-mail og adgangskode. Eleven tager hver måned en test om trivsel, læring, møbler, miljø og arbejdsstil med mulighed for at uddybe og ser sin personlige elevprofil. Læreren ser hver elev i sin klasse i procent pr. måned og elevprofilen. Virksomheden filtrerer anonyme besvarelser. Den indloggede bruger sendes i headeren `X-User-Id` som `rolle:id`, fx `elev:6`.

Kravgrundlag: [`../Kravspecifikation.md`](../Kravspecifikation.md) og [`../Ændriger til vores produkt (1).docx`](<../Ændriger til vores produkt (1).docx>)

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
  index.html        skærmbilleder: Login · Forside · Månedens test · Elever · Klassens resultater · Udvikling over tid · Besvarelser · Skoleoverblik · Spørgsmål og elever
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
| `GET` | `/api/company/answers` | Virksomhedens adgang til besvarelser til idéudvikling. Filtrér med ?class_id=&grade=&period=&category= &question_id=&max_value=&with_text=1. Eleverne er anonymiseret (fx "Elev 7.B-3"). |
| `GET` | `/api/health` | Systemstatus |
| `POST` | `/api/login` | Log ind som elev, lærer eller virksomhed med e-mail og adgangskode. |
| `GET` | `/api/me/profile` | Elevens forside: egen profil og udvikling. |
| `GET` | `/api/overview` | Virksomhedens overblik (Læringsrum 2.0): alle klasser med seneste resultat sammenlignet med første måling. |
| `GET` | `/api/questions` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/questions` | Opret (CRUD) |
| `DELETE` | `/api/questions/<item_id>` | Slet (CRUD) |
| `GET` | `/api/questions/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/questions/<item_id>` | Opdatér (CRUD) |
| `POST` | `/api/responses` | Elevens månedlige besvarelse med uddybende tekst pr. svar, ønsker og holdning til klasselokalet. |
| `GET` | `/api/results` | Klassens samlede resultat i en måned: gennemsnit og procenttal (vises ved mindst 3 besvarelser). |
| `GET` | `/api/results/trend` | Sammenlign svar over tid: gennemsnit og andel positive svar pr. kategori pr. måned. |
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
| `GET` | `/api/students/<student_id>/profile` | Lærerens visning af én elev: navn, klasse, profil og besvarelser i procent pr. måned. |
| `GET` | `/api/survey` | Månedens aktive spørgsmål, og om eleven allerede har svaret. |
| `GET` | `/api/teacher/students` | Lærerens overblik: hver elev i klassen med andel positive svar pr. måned og seneste profil. |
