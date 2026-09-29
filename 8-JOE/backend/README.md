# Joe & The Juice – Pant på kopper – prototype

Ved køb opkræves pant, og koppen får en unik kop-kode. Ved retur scannes koden i en hvilken som helst butik, og pantet krediteres som point i appen. Samme kop kan kun indløses én gang. Pantbeløb og pointkurs styres centralt i tabellen setting.

Kravgrundlag: [`../Kravspecifikation.md`](../Kravspecifikation.md)

## Kør prototypen

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # første gang
pip install -r requirements.txt                       # første gang
python app.py
```

Åbn **http://localhost:5108** – Flask serverer både API'et (`/api/...`) og frontenden fra `../frontend`.
Er porten optaget, vælger serveren selv den næste ledige port og skriver adressen i terminalen
(fx ` * Port 5108 er optaget – bruger port 5109 i stedet`). Du kan også vælge port selv med `PORT=5200 python app.py`.
`frontend/index.html` kan også åbnes direkte fra disken. Så kalder den `http://localhost:5108/api` (attributten `data-api-port` i `index.html`).

Databasen `backend/database.db` (SQLite3) oprettes og fyldes med fiktive testdata fra `seed.sql` ved første start.
Nulstil den med `python database.py --reset`.

## Struktur

```
backend/
  app.py            logiklag: forretningsregler og endepunkter for netop dette projekt
  core.py           fælles for alle prototyper: Flask-app, JSON-fejl, CORS og generisk CRUD
  database.py       fælles for alle prototyper: SQLite3-forbindelse og hjælpefunktioner
  schema.sql        tabeller: setting, store, customer, drink, sale_order, cup, deposit_transaction
  seed.sql          fiktive testdata
  requirements.txt
frontend/
  index.html        skærmbilleder: Kasse (POS) · Kunde-app · Bæredygtighed · Indstillinger
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
| `GET` | `/api/cups` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `GET` | `/api/cups/<item_id>` | Hent én (CRUD) |
| `GET` | `/api/customers` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/customers` | Opret (CRUD) |
| `POST` | `/api/customers/<customer_id>/redeem` | Point kan kun bruges digitalt i appen – fx som rabat på næste køb. |
| `GET` | `/api/customers/<customer_id>/wallet` | Kundens app: pointsaldo, kopper at aflevere og historik. |
| `DELETE` | `/api/customers/<item_id>` | Slet (CRUD) |
| `GET` | `/api/customers/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/customers/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/drinks` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/drinks` | Opret (CRUD) |
| `DELETE` | `/api/drinks/<item_id>` | Slet (CRUD) |
| `GET` | `/api/drinks/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/drinks/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/health` | Systemstatus |
| `POST` | `/api/orders` | Salg med pant-kop: opkræver pant og udleverer en kop med unik kode. |
| `POST` | `/api/returns` | Retur: scan kop-koden og kreditér point. Samme kop kan kun indløses én gang. |
| `GET` | `/api/settings` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/settings` | Opret (CRUD) |
| `DELETE` | `/api/settings/<item_id>` | Slet (CRUD) |
| `GET` | `/api/settings/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/settings/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/stores` | Hent liste (filtrér med ?felt=værdi) (CRUD) |
| `POST` | `/api/stores` | Opret (CRUD) |
| `DELETE` | `/api/stores/<item_id>` | Slet (CRUD) |
| `GET` | `/api/stores/<item_id>` | Hent én (CRUD) |
| `PUT` | `/api/stores/<item_id>` | Opdatér (CRUD) |
| `GET` | `/api/sustainability` | Bæredygtighedsrapport: udleverede og returnerede kopper, returrate og pr. butik. |
| `GET` | `/api/transactions` | Log over pant-transaktioner. |
