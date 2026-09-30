# GreenMobility – Reservation af hotspotparkering – prototype

Kunden søger efter et hotspot, reserverer en ledig plads i 20 minutter og kan annullere, bekræfte ankomst eller melde et problem med pladsen.
Er et hotspot fuldt, vises de nærmeste alternativer. Hjælp-knappen giver AI-chat (regelbaseret demo) og kontakt til en medarbejder.
Administratoren har sin egen side, hvor bilers ankomst og afgang simuleres, og hvor kundehenvendelser besvares.

Kravgrundlag: [`../Kravspecifikation.MD`](../Kravspecifikation.MD)

## Kør prototypen

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # første gang
pip install -r requirements.txt                       # første gang
python app.py
```

Åbn **http://localhost:5102** (kundeside) og **http://localhost:5102/admin.html** (administrator) – Flask serverer både API'et (`/api/...`) og frontenden fra `../frontend`.
Kundesiden viser kunde 1. Vælg en anden testkunde med `?kunde=2` eller via *Testkunder* på administratorsiden.
Er porten optaget, vælger serveren selv den næste ledige port og skriver adressen i terminalen
(fx ` * Port 5102 er optaget – bruger port 5103 i stedet`). Du kan også vælge port selv med `PORT=5200 python app.py`.
`frontend/index.html` kan også åbnes direkte fra disken. Så kalder den `http://localhost:5102/api` (attributten `data-api-port` i `index.html`).

Databasen `backend/database.db` (SQLite3) oprettes og fyldes med fiktive testdata fra `seed.sql` ved første start.
Nulstil den med `python database.py --reset`. Kør testene med `python tests.py` (bruger en midlertidig database).

## Struktur

```
backend/
  app.py            logiklag: forretningsregler og endepunkter for netop dette projekt
  core.py           fælles for alle prototyper: Flask-app, JSON-fejl, CORS og generisk CRUD
  database.py       fælles for alle prototyper: SQLite3-forbindelse og hjælpefunktioner
  schema.sql        tabeller: customer, hotspot, spot, reservation, staff, support_case, support_message, event_log
  seed.sql          fiktive testdata
  tests.py          automatiske tests af forretningsreglerne (bl.a. ingen dobbeltbooking)
  requirements.txt
frontend/
  index.html        kundeside: søgning, hotspotliste, aktiv reservation med nedtælling, menu og hjælp
  app.js            præsentationslag for kundesiden
  admin.html        administrator: overblik (tal der stemmer), pladser, reservationer, henvendelser, opsætning
  admin.js          præsentationslag for administratorsiden
  style.css         fælles stylesheet for alle prototyper
  app.css           projektets eget udseende – bruges af begge sider, så farver og knapper er ens
  api.js            fælles klient: fetch() + JSON og små DOM-hjælpere
```

Klienten og serveren taler kun sammen via HTTP og JSON. Svarene vises i DOM'en, og det seneste
rå JSON-svar kan ses nederst på administratorsiden under "Seneste JSON-svar fra API'et".

Fejl returneres altid som JSON: `{"error": "…", "path": "/api/…"}` med statuskode 400, 401, 403, 404 eller 409.

## API

| Metode | Endepunkt | Beskrivelse |
| --- | --- | --- |
| `GET` | `/api/health` | Systemstatus |
| `GET` | `/api/info` | Regler og vilkår, gebyrer, privatlivspolitik, åbningstider, telefon og medarbejdere |
| `GET` | `/api/hotspots/overview` | Hotspots med ledige, reserverede, optagede og spærrede pladser + `consistent`. Søg med `?q=` |
| `GET` | `/api/hotspots/<id>/alternatives` | De nærmeste andre hotspots med ledige pladser |
| `GET` | `/api/reservations` | Reservationer – filtrér på kunde med `?customer_id=1` |
| `POST` | `/api/reservations` | Reservér en ledig plads i 20 minutter (atomisk – ingen dobbeltbooking) |
| `GET` | `/api/reservations/<id>` | Én reservation med hotspot, plads og vejvisning |
| `POST` | `/api/reservations/<id>/arrive` | Bekræft ankomst: pladsen skifter fra reserveret til optaget |
| `POST` | `/api/reservations/<id>/cancel` | Annullér og frigiv pladsen |
| `POST` | `/api/reservations/<id>/report` | Meld problem: `{"type": "PLADS_OPTAGET"}` (ny plads eller gratis annullering) eller `{"type": "KAN_IKKE_FINDE"}` (vejvisning + henvendelse) |
| `POST` | `/api/assistant` | AI-hjælp: `{"text": "…", "customer_id": 1}`. Regelbaseret demo, intet gemmes |
| `GET` | `/api/support` | Henvendelser med beskeder – filtrér med `?customer_id=1` |
| `POST` | `/api/support` | Start chat med medarbejder: `{"customer_id", "text", "staff_id" (valgfri – ellers første ledige)}` |
| `GET` | `/api/support/<id>` | Én henvendelse med beskeder |
| `POST` | `/api/support/<id>/messages` | Skriv i chatten: `{"sender": "KUNDE" \| "MEDARBEJDER", "text"}` |
| `POST` | `/api/support/<id>/close` | Luk henvendelsen |
| `GET` | `/api/admin/spots` | Alle pladser med status og eventuel aktiv reservation |
| `POST` | `/api/admin/spots/<id>/depart` | Simulér at en bil kører – først nu bliver pladsen ledig |
| `POST` | `/api/admin/spots/<id>/occupy` | Simulér at en bil uden reservation parkerer |
| `POST` | `/api/admin/reservations/<id>/expire` | Simulér at ankomstfristen er overskredet |
| `GET` `POST` `PUT` `DELETE` | `/api/customers`, `/api/hotspots`, `/api/spots`, `/api/staff` | CRUD (`/<id>` for én) |
| `GET` | `/api/events` | Hændelseslog |
