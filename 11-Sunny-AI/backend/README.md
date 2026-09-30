# Sunny AI – beslutningsstøtte til ugeplan og opslag – prototype

En simuleret Uniconta-adapter leverer snapshots med varer, lager og ordrer. Planmotoren validerer data, beregner disponibelt lager, fordeler produktionen på ugens dage og viser råvaremangler. Planlæggeren justerer prioritet og kapacitet, som giver en ny planversion, og godkender derefter lokalt. En regelbaseret demoassistent svarer ud fra de samme tal. Demobrugeren sendes i headeren `X-User-Id`, men bruges kun som navn på godkendelser. Det er ikke et login.

Kravgrundlag: [`../kravspecifikation.md`](../kravspecifikation.md)

## Kør prototypen

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # første gang
pip install -r requirements.txt                       # første gang
python app.py
```

Åbn **http://localhost:5111**. Flask serverer både API'et (`/api/...`) og frontenden fra `../frontend`.
Er porten optaget, vælger serveren selv den næste ledige port og skriver adressen i terminalen
(fx ` * Port 5111 er optaget – bruger port 5112 i stedet`). Du kan også vælge port selv med `PORT=5200 python app.py`.
`frontend/index.html` kan også åbnes direkte fra disken. Så kalder den `http://localhost:5111/api` (attributten `data-api-port` i `index.html`).

Databasen `backend/database.db` (SQLite3) oprettes og fyldes med fiktive testdata fra `seed.sql` ved første start.
Nulstil den med `python database.py --reset` eller med knappen *Nulstil demo* under Datastatus.

## Test

```bash
python tests.py
```

Kører accepttestene T01–T10 og N04 fra kravspecifikationen på en midlertidig database. Testene bruger kun Pythons standardbibliotek.

## Struktur

```
backend/
  app.py            logiklag: datakildeadapter, planversioner, godkendelse, assistent og endepunkter
  planner.py        logiklag: planmotoren (datavalidering og R01–R08) uden Flask og SQLite
  tests.py          automatiske accepttests T01–T10 og N04
  core.py           fælles for alle prototyper: Flask-app, JSON-fejl, CORS og generisk CRUD
  database.py       fælles for alle prototyper: SQLite3-forbindelse og hjælpefunktioner
  schema.sql        tabeller: bruger, indstilling, snapshot, vare, produktionsrate, lagerbatch, ordrelinje,
                    produktionsstatus, ressourcebehov, kapacitetsdag, planversion, planlinje, haendelse
  seed.sql          fiktive testdata (testuge 5.–9. oktober 2026)
  requirements.txt
frontend/
  index.html        skærmbilleder: Overblik · Ugeplan · Lager og ordrer · Spørg Sunny AI · Datastatus
  style.css         fælles stylesheet (projektfarver står i index.html)
  api.js            fælles klient: fetch() + JSON og små DOM-hjælpere
  app.js            præsentationslag for netop dette projekt
```

Klienten og serveren taler kun sammen via HTTP og JSON. Svarene vises i DOM'en, og det seneste
rå JSON-svar kan ses nederst på siden under "Seneste JSON-svar fra API'et".

Fejl returneres altid som JSON: `{"error": "…", "path": "/api/…"}` med statuskode 400, 404 eller 409.

**Mængder er heltal i tusindedele af varens basisenhed:** `20000` stk-tusindedele = 20 stk, `500` L-tusindedele = 0,5 L. Tid er hele minutter.

## API

| Metode | Endepunkt | Beskrivelse |
| --- | --- | --- |
| `POST` | `/api/assistant` | Afgrænsede spørgsmål på dansk. Body: `{"spoergsmaal": "…", "vare_id": 4}` (`vare_id` valgfri ved tvetydigt varenavn) |
| `PUT` | `/api/clock` | Fastlås demo-uret: `{"beregningstidspunkt": "2026-10-05 09:00"}`. Eksisterende planer bliver forældede (R08) |
| `GET` | `/api/events` | Hændelseslog: snapshots, beregninger, godkendelser og ændringer af demo-uret |
| `GET` | `/api/health` | Systemstatus |
| `GET` | `/api/items` | Hent liste (filtrér med ?felt=værdi) (CRUD, skrivebeskyttet) |
| `GET` | `/api/items/<item_id>` | Hent én (CRUD, skrivebeskyttet) |
| `GET` | `/api/items/<item_id>/details` | Vare med batches, disponibelt lager og ordrer, der bruger den |
| `GET` | `/api/orders` | Ordrelinjer i det aktuelle snapshot. Søg med `?q=` (ordre-, vare- eller kildenummer, navn), filtrér med `?status=` |
| `GET` | `/api/orders/<line_id>` | Ordrelinje med ressourcebehov og forklaring fra den aktuelle plan (F10) |
| `GET` | `/api/overview` | Nøgletal og forhold, der kræver handling, fra samme plan som Ugeplan og assistent |
| `GET` | `/api/plans` | Versionshistorik for en uge: `?uge_start=YYYY-MM-DD` |
| `POST` | `/api/plans` | F07, F11: beregn et planforslag som ny version. Tidligere versioner for ugen bliver forældede |
| `GET` | `/api/plans/<plan_id>` | Én planversion med parametre, resultat og hændelser |
| `POST` | `/api/plans/<plan_id>/approve` | F12, R08: godkend præcis denne version. Body: `{"request_id": "…", "accepter_uplanlagte": true}` |
| `GET` | `/api/plans/<plan_id>/calendar.ics` | F16 (Should): kalenderfil med godkendte planlinjer. Sendes ikke automatisk |
| `GET` | `/api/plans/current` | Seneste gyldige plan for ugen, ellers et foreløbigt forslag, der ikke gemmes |
| `POST` | `/api/reset` | Genskab demoens startdata. Kræver `{"bekraeft": true}` |
| `GET` | `/api/snapshots` | Hent liste (CRUD, skrivebeskyttet) |
| `GET` | `/api/snapshots/<item_id>` | Hent én (CRUD, skrivebeskyttet) |
| `POST` | `/api/source/import` | Simuleret Uniconta-adapter: nyt snapshot, evt. med en demoændring (se nedenfor) |
| `GET` | `/api/status` | Datakilde, snapshot-tidspunkt, alder og antal forhold, der kræver kontrol |
| `GET` | `/api/stock` | Lagerbatches med disponibel mængde og grund, hvis batchen ikke kan bruges (R02). Søg med `?q=` |
| `GET` | `/api/users` | Demobrugere (CRUD, skrivebeskyttet) |
| `GET` | `/api/users/<item_id>` | Hent én (CRUD, skrivebeskyttet) |
| `GET` | `/api/validation` | F02, F04, F05: kendte dataproblemer i det aktuelle snapshot med anbefalet handling |

### Demoændringer i kildedata (`POST /api/source/import`)

| `type` | Felter | Bruges til |
|---|---|---|
| `genindlaes` | – | Samme data med nyt kildetidspunkt |
| `udloeb_batch` | `batchnummer` | T02: batchen får udløbsdato dagen før beregningsdatoen |
| `uafklaret_faerdigmelding` | `vare_id` | T03: varens beholdning bliver usikker |
| `afklar` | – | Fjerner alle uafklarede færdigmeldinger |
| `ny_ordre` | `ordre_id`, `vare_id`, `antal`, `leveringsdato`, `prioritet`, `saesonmaerke` | T05: ny ordrelinje. Ressourcebehovet kopieres fra en linje med samme vare. Findes ingen, er det ukendt |
