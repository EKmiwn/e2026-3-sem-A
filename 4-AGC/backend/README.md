# AGC Biologics – QC Informationshub – prototype

Simulerede Outlook/Teams-connectors afleverer kildeposter. Systemet vurderer relevans med nøgleord, foreslår kategori og resumé og lægger posten i “Til kontrol”. Lederen retter (ny version), godkender og deler et uforanderligt snapshot med medarbejdere, der har adgang. Testbrugeren sendes i headeren `X-User-Id`.

Kravgrundlag: [`../Kravspecifikation.md`](../Kravspecifikation.md)

## Kør prototypen

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # første gang
pip install -r requirements.txt                       # første gang
python app.py
```

Åbn **http://localhost:5104** – Flask serverer både API'et (`/api/...`) og frontenden fra `../frontend`.
Er porten optaget, vælger serveren selv den næste ledige port og skriver adressen i terminalen
(fx ` * Port 5104 er optaget – bruger port 5105 i stedet`). Du kan også vælge port selv med `PORT=5200 python app.py`.
`frontend/index.html` kan også åbnes direkte fra disken. Så kalder den `http://localhost:5104/api` (attributten `data-api-port` i `index.html`).

Databasen `backend/database.db` (SQLite3) oprettes og fyldes med fiktive testdata fra `seed.sql` ved første start.
Nulstil den med `python database.py --reset`.

## Struktur

```
backend/
  app.py            logiklag: forretningsregler og endepunkter for netop dette projekt
  core.py           fælles for alle prototyper: Flask-app, JSON-fejl, CORS og generisk CRUD
  database.py       fælles for alle prototyper: SQLite3-forbindelse og hjælpefunktioner
  schema.sql        tabeller: user, category, category_access, source, info, share, share_recipient, event, test_feed
  seed.sql          fiktive testdata
  requirements.txt
frontend/
  index.html        skærmbilleder: Til kontrol · Søg · Delt med mig · Kilder og testfeed · Administration
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
| `GET` | `/api/categories` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/categories` | Opret (CRUD) |
| `DELETE` | `/api/categories/<item_id>` | Slet (CRUD) |
| `GET` | `/api/categories/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/categories/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/category-access` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/category-access` | Opret (CRUD) |
| `DELETE` | `/api/category-access/<item_id>` | Slet (CRUD) |
| `GET` | `/api/category-access/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/category-access/<item_id>` | Opdatér (CRUD) |
| `POST` | `/api/connectors/<system>` | Simuleret Outlook-/Teams-connector: modtager én kildepost som JSON. |
| `POST` | `/api/connectors/simulate` | Afleverer næste fiktive post fra testfeedet gennem connectoren. |
| `GET` | `/api/events` | Hændelseslog (leder og administrator). |
| `GET` | `/api/feed` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `GET` | `/api/feed/<item_id>` | Hent én (CRUD) |
| `GET` | `/api/health` | Systemstatus |
| `GET` | `/api/info` | Søg i tilladt information: ?q=&category_id=&system=&status= |
| `GET` | `/api/info/<info_id>` | Informationspost med originalkilde, delinger og hændelser. |
| `PUT` | `/api/info/<info_id>` | F06: rettelse øger versionen og ophæver tidligere godkendelse. Originalkilden ændres ikke. |
| `POST` | `/api/info/<info_id>/approve` | Godkend den aktuelle version (kræver expected_version). |
| `POST` | `/api/info/<info_id>/discard` | Fravælg en post, så den ikke vises som normal information. |
| `GET` | `/api/info/<info_id>/recipients` | Medarbejdere, der har adgang til postens kategori. |
| `POST` | `/api/info/<info_id>/share` | F07, BR4, BR5: kun godkendt, aktuel version. Én ugyldig modtager afviser hele delingen. |
| `GET` | `/api/me` | Den indloggede testbruger og dennes kategoriadgang. |
| `POST` | `/api/notes` | F10: manuel note som supplement – gennemgår samme strukturering og kontrol. |
| `GET` | `/api/review-queue` | Til kontrol: udkast, som lederen må se. |
| `GET` | `/api/shared-with-me` | Delinger til den indloggede medarbejder (snapshots). |
| `POST` | `/api/shares/<share_id>/read` | Markér en deling som læst. |
| `GET` | `/api/users` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/users` | Opret (CRUD) |
| `DELETE` | `/api/users/<item_id>` | Slet (CRUD) |
| `GET` | `/api/users/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/users/<item_id>` | Opdatér (CRUD) |
