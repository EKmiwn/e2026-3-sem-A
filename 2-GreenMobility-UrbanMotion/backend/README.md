# GreenMobility – Reservation af hotspotparkering – prototype

Kunden reserverer en ledig plads ved et hotspot i 20 minutter, kan annullere eller registrere ankomst. Reservationer udløber automatisk, og administratoren simulerer bilers ankomst og afgang.

Kravgrundlag: [`../Kravspecifikation.MD`](../Kravspecifikation.MD)

## Kør prototypen

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # første gang
pip install -r requirements.txt                       # første gang
python app.py
```

Åbn **http://localhost:5102** – Flask serverer både API'et (`/api/...`) og frontenden fra `../frontend`.
Er porten optaget, vælger serveren selv den næste ledige port og skriver adressen i terminalen
(fx ` * Port 5102 er optaget – bruger port 5103 i stedet`). Du kan også vælge port selv med `PORT=5200 python app.py`.
`frontend/index.html` kan også åbnes direkte fra disken. Så kalder den `http://localhost:5102/api` (attributten `data-api-port` i `index.html`).

Databasen `backend/database.db` (SQLite3) oprettes og fyldes med fiktive testdata fra `seed.sql` ved første start.
Nulstil den med `python database.py --reset`.

## Struktur

```
backend/
  app.py            logiklag: forretningsregler og endepunkter for netop dette projekt
  core.py           fælles for alle prototyper: Flask-app, JSON-fejl, CORS og generisk CRUD
  database.py       fælles for alle prototyper: SQLite3-forbindelse og hjælpefunktioner
  schema.sql        tabeller: customer, hotspot, spot, reservation, event_log
  seed.sql          fiktive testdata
  requirements.txt
frontend/
  index.html        skærmbilleder: Hotspots · Mine reservationer (nedtælling) · Administrator (pladser, reservationer, hændelseslog, CRUD)
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
| `POST` | `/api/admin/reservations/<reservation_id>/expire` | Simulerer at ankomstfristen er overskredet (i stedet for at vente 20 minutter). |
| `GET` | `/api/admin/spots` | Alle pladser med status og eventuel aktiv reservation. |
| `POST` | `/api/admin/spots/<spot_id>/depart` | En bil kører fra pladsen – først nu bliver pladsen ledig igen. |
| `POST` | `/api/admin/spots/<spot_id>/occupy` | Simulér at en bil uden reservation parkerer. |
| `GET` | `/api/customers` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/customers` | Opret (CRUD) |
| `DELETE` | `/api/customers/<item_id>` | Slet (CRUD) |
| `GET` | `/api/customers/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/customers/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/events` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `GET` | `/api/events/<item_id>` | Hent én (CRUD) |
| `GET` | `/api/health` | Systemstatus |
| `GET` | `/api/hotspots` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/hotspots` | Opret (CRUD) |
| `DELETE` | `/api/hotspots/<item_id>` | Slet (CRUD) |
| `GET` | `/api/hotspots/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/hotspots/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/hotspots/overview` | Hotspots med antal ledige, reserverede, optagede og spærrede pladser. |
| `GET` | `/api/reservations` | Reservationer – filtrér på kunde med ?customer_id=1 |
| `POST` | `/api/reservations` | Reservér en ledig plads ved et hotspot i 20 minutter. |
| `GET` | `/api/reservations/<reservation_id>` | Én reservation med hotspot og plads. |
| `POST` | `/api/reservations/<reservation_id>/arrive` | Registrér ankomst: reservationen benyttes, og pladsen bliver optaget. |
| `POST` | `/api/reservations/<reservation_id>/cancel` | Annullér en aktiv reservation og frigiv pladsen. |
| `GET` | `/api/spots` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/spots` | Opret (CRUD) |
| `DELETE` | `/api/spots/<item_id>` | Slet (CRUD) |
| `GET` | `/api/spots/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/spots/<item_id>` | Opdatér (CRUD) |
