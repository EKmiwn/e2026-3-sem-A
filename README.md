# Hold A – prototyper

Hver gruppemappe indeholder en prototype bygget ud fra gruppens kravspecifikation:

- `backend/`: Python Flask API med en SQLite3-database
- `frontend/`: HTML, CSS og JavaScript, der henter JSON fra API'et

| # | Projekt | Prototype | Lokal port | Server | Dokumentation |
|---|---|---|---|---|---|
| 1 | StockUP | Lager af kaffesække og kaffeposer (ristning, salg, bevægelseslog) | 5101 | :8001 | [DOCS](1-StockUP/DOCS.md) · [API](1-StockUP/backend/README.md) |
| 2 | GreenMobility | Reservation af hotspotparkering med 20 min. frist | 5102 | :8002 | [DOCS](2-GreenMobility-UrbanMotion/DOCS.md) · [API](2-GreenMobility-UrbanMotion/backend/README.md) |
| 3 | Amitylux | Oplevelsesvælger, anbefaling og forespørgsels-brief (engelsk UI) | 5103 | :8003 | [DOCS](3-Amitylux/DOCS.md) · [API](3-Amitylux/backend/README.md) |
| 4 | AGC | QC-informationshub: connectors, relevans, kontrol, godkendelse og deling | 5104 | :8004 | [DOCS](4-AGC/DOCS.md) · [API](4-AGC/backend/README.md) |
| 5 | Solum | Fejlfindingsguides, vidensartikler og kompetenceoverblik | 5105 | :8005 | [DOCS](5-Solum/DOCS.md) · [API](5-Solum/backend/README.md) |
| 6 | Learnify | Elevevaluering af trivsel og læringsmiljø med resultater over tid | 5106 | :8006 | [DOCS](6-Learnify/DOCS.md) · [API](6-Learnify/backend/README.md) |
| 7 | Boliga | Insight Hub med samlet boligdata og AI-sparringspartner | 5107 | :8007 | [DOCS](7-Boliga/DOCS.md) · [API](7-Boliga/backend/README.md) |
| 8 | JOE | Pant på kopper: kop-kode, retur og point i appen | 5108 | :8008 | [DOCS](8-JOE/DOCS.md) · [API](8-JOE/backend/README.md) |
| 9 | Den Sidste Rejse | Lagerfunktion i EG med historik og genbestillingsliste | 5109 | :8009 | [DOCS](9-Den-Sidste-Rejse/DOCS.md) · [API](9-Den-Sidste-Rejse/backend/README.md) |
| 10 | Ejner Hessel | Min Hessel: biler, service, reparationsstatus, booking og dokumenter | 5110 | :8010 | [DOCS](10-Ejner-Hessel/DOCS.md) · [API](10-Ejner-Hessel/backend/README.md) |

- **`DOCS.md`** beskriver prototypen: krav, forretningsregler, ER-diagram og testdata.
- **`backend/README.md`** viser alle API-endepunkter.

## Struktur

Alle prototyper er bygget ens:

```
<projekt>/
├── DOCS.md
├── backend/
│   ├── app.py            projektets endepunkter og forretningsregler
│   ├── core.py           fælles Flask-kode (ens i alle projekter)
│   ├── database.py       fælles SQLite-kode (ens i alle projekter)
│   ├── schema.sql        tabeller
│   ├── seed.sql          testdata
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── style.css         fælles stylesheet
    ├── api.js            fælles fetch- og DOM-hjælpere
    └── app.js            projektets frontend-logik
```

Flask serverer frontenden på `/` og API'et på `/api/...` fra samme adresse.

## Kør lokalt

```bash
cd 1-StockUP/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py                  # åbn http://localhost:5101
```

Databasen oprettes med testdata ved første start. Nulstil den med `python database.py --reset`.

## Deployment på DigitalOcean

Alle ti prototyper kører på én Droplet (Ubuntu, 512 MB RAM + 1 GB swap). Hver prototype kører med **Gunicorn** som sin egen **systemd**-service og nås på `http://DROPLET_IP:8001` til `:8010`.

Hvert projekt har i sin `backend`-mappe:

- `venv/` med Flask og Gunicorn
- `gunicorn.env` med projektets port, fx `PORT=8001`
- `database.db`, oprettet én gang med `venv/bin/python database.py`, fordi Gunicorn ikke opretter databasen

Alle ti bruger den samme service-skabelon, `/etc/systemd/system/gunicorn@.service`, hvor `%i` er projektmappens navn:

```ini
[Unit]
Description=Gunicorn for %i
After=network.target

[Service]
User=root
WorkingDirectory=/root/Hold-A-kravspecifikationer/%i/backend
EnvironmentFile=/root/Hold-A-kravspecifikationer/%i/backend/gunicorn.env
ExecStart=/root/Hold-A-kravspecifikationer/%i/backend/venv/bin/gunicorn --workers 1 --bind 0.0.0.0:${PORT} app:app
Restart=always
OOMScoreAdjust=500

[Install]
WantedBy=multi-user.target
```

- `--workers 1` holder hukommelsesforbruget nede.
- `Restart=always` genstarter en prototype, hvis den crasher.
- `OOMScoreAdjust=500` gør, at Linux dræber en prototype frem for SSH, hvis hukommelsen slipper op.

Hver prototype er startet og sat til at starte ved boot:

```bash
systemctl daemon-reload
systemctl enable --now gunicorn@1-StockUP      # osv. for alle ti
```

### Nyttige kommandoer

| Opgave | Kommando |
|---|---|
| Status for alle | `systemctl list-units 'gunicorn@*' --no-pager` |
| Genstart én / alle | `systemctl restart gunicorn@8-JOE` / `systemctl restart 'gunicorn@*'` |
| Se log | `journalctl -u gunicorn@8-JOE -n 30` |
| Hukommelse | `free -h` |
| Opdatér kode | `git pull` og derefter `systemctl restart gunicorn@<projekt>` |
