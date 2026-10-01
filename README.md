# Hold A – prototyper

Hver gruppemappe indeholder en prototype bygget ud fra gruppens kravspecifikation:

- `backend/`: Python Flask API med en SQLite3-database
- `frontend/`: HTML, CSS og JavaScript, der henter JSON fra API'et

| # | Projekt | Prototype | Lokal port | Server | Dokumentation |
|---|---|---|---|---|---|
| 1 | StockUP | Lager af kaffesække og kaffeposer (ristning, salg, bevægelseslog) | 5101 | :8001 | [DOCS](1-StockUP/DOCS.md) · [API](1-StockUP/backend/README.md) |
| 2 | GreenMobility | Reservation af hotspotparkering med 20 min. frist | 5102 | :8002 | [DOCS](2-GreenMobility-UrbanMotion/DOCS.md) · [API](2-GreenMobility-UrbanMotion/backend/README.md) |
| 3 | Amitylux | Experience Compass: højst tre forklarede oplevelsesforslag og struktureret overlevering (engelsk UI) | 5103 | :8003 | [DOCS](3-Amitylux/DOCS.md) · [API](3-Amitylux/backend/README.md) |
| 4 | AGC | QC-informationshub med godkendelse og deling samt Leverancer & Prioritering | 5104 | :8004 | [DOCS](4-AGC/DOCS.md) · [API](4-AGC/backend/README.md) |
| 5 | Solum | Fejlfindingsguides, vidensartikler og kompetenceoverblik | 5105 | :8005 | [DOCS](5-Solum/DOCS.md) · [API](5-Solum/backend/README.md) |
| 6 | Learnify | Månedlig elevevaluering med login (elev/lærer/virksomhed), elevprofil, lærerens overblik pr. elev og filtrering for virksomheden | 5106 | :8006 | [DOCS](6-Learnify/DOCS.md) · [API](6-Learnify/backend/README.md) |
| 7 | Boliga | Insight Hub med samlet boligdata og AI-sparringspartner | 5107 | :8007 | [DOCS](7-Boliga/DOCS.md) · [API](7-Boliga/backend/README.md) |
| 8 | JOE | Pant på kopper: kop-kode, retur og point i appen | 5108 | :8008 | [DOCS](8-JOE/DOCS.md) · [API](8-JOE/backend/README.md) |
| 9 | Den Sidste Rejse | Lagerfunktion i EG med historik og genbestillingsliste | 5109 | :8009 | [DOCS](9-Den-Sidste-Rejse/DOCS.md) · [API](9-Den-Sidste-Rejse/backend/README.md) |
| 10 | Ejner Hessel | Min Hessel: biler med billeder, booking i trin, reparationsstatus, dokumenter, forbrug og klima samt separat medarbejdervisning | 5110 | :8010 | [DOCS](10-Ejner-Hessel/DOCS.md) · [API](10-Ejner-Hessel/backend/README.md) |
| 11 | Sunny AI | Ugeplan for produktion, råvaremangler, lageropslag og regelbaseret assistent | 5111 | :8011 | [DOCS](11-Sunny-AI/DOCS.md) · [API](11-Sunny-AI/backend/README.md) |
| 12 | NewLoop | LoopAAS: returnér emballage, optjen LoopPoints, niveauer og badges, rewards hos partnere | 5112 | – (ikke deployet endnu) | [DOCS](12-NewLoop/DOCS.md) · [API](12-NewLoop/backend/README.md) |

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

Sunny AI har desuden `backend/planner.py` (planmotoren uden Flask og SQLite) og `backend/tests.py` (accepttests), fordi kravspecifikationen kræver, at beregningslogikken kan testes alene.
Amitylux har tilsvarende `backend/compass.py` (matchmotoren) og `backend/tests.py` (test af K1–K12).

Flask serverer frontenden på `/` og API'et på `/api/...` fra samme adresse.

## Kør lokalt

Kræver Python 3.10 eller nyere. Kommandoerne køres fra projektets `backend`-mappe, fx `1-StockUP/backend`.

### Mac og Linux (Terminal)

```bash
cd 1-StockUP/backend
python3 -m venv .venv                # første gang
source .venv/bin/activate
pip install -r requirements.txt      # første gang
python app.py                        # åbn http://localhost:5101
```

### Windows (PowerShell)

```powershell
cd 1-StockUP\backend
py -m venv .venv                     # første gang
.venv\Scripts\Activate.ps1
pip install -r requirements.txt      # første gang
python app.py                        # åbn http://localhost:5101
```

Giver `Activate.ps1` fejlen *"running scripts is disabled on this system"*, så tillad lokale scripts én gang med
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` og prøv igen.

### Windows (Kommandoprompt / cmd)

```bat
cd 1-StockUP\backend
py -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
python app.py
```

Er `py` ikke fundet, så installér Python fra [python.org](https://www.python.org/downloads/) og sæt flueben i *"Add python.exe to PATH"*. Brug derefter `python` i stedet for `py`.

### Gælder for alle

- Databasen oprettes med testdata ved første start. Nulstil den med `python database.py --reset`, mens serveren er stoppet.
- Stop serveren med `Ctrl` + `C`. Deaktivér det virtuelle miljø med `deactivate`.
- Er porten optaget, bruger serveren automatisk den næste ledige og skriver adressen i terminalen.

| Opgave | Mac og Linux | Windows (PowerShell) | Windows (cmd) |
|---|---|---|---|
| Vælg selv port | `PORT=5300 python app.py` | `$env:PORT=5300; python app.py` | `set PORT=5300 && python app.py` |
| Se hvad der bruger porten | `lsof -nP -iTCP:5101 -sTCP:LISTEN` | `Get-NetTCPConnection -LocalPort 5101` | `netstat -ano \| findstr :5101` |
| Stop en glemt server | `lsof -t -iTCP:5101 -sTCP:LISTEN \| xargs kill` | `Stop-Process -Id <PID>` | `taskkill /PID <PID> /F` |

Kommandoerne i hvert projekts `DOCS.md` er skrevet til Mac og Linux. På Windows bruges `\` i stier og `.venv\Scripts\` i stedet for `.venv/bin/`.

## Deployment på DigitalOcean

Alle elleve prototyper kører på én Droplet (Ubuntu, 512 MB RAM + 1 GB swap). Hver prototype kører med **Gunicorn** som sin egen **systemd**-service og nås på `http://DROPLET_IP:8001` til `:8011`.

Hvert projekt har i sin `backend`-mappe:

- `venv/` med Flask og Gunicorn
- `gunicorn.env` med projektets port, fx `PORT=8001`
- `database.db`, oprettet én gang med `venv/bin/python database.py`, fordi Gunicorn ikke opretter databasen

Alle elleve bruger den samme service-skabelon, `/etc/systemd/system/gunicorn@.service`, hvor `%i` er projektmappens navn:

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
systemctl enable --now gunicorn@1-StockUP      # osv. for alle elleve
```

### Nyttige kommandoer

| Opgave | Kommando |
|---|---|
| Status for alle | `systemctl list-units 'gunicorn@*' --no-pager` |
| Genstart én / alle | `systemctl restart gunicorn@8-JOE` / `systemctl restart 'gunicorn@*'` |
| Se log | `journalctl -u gunicorn@8-JOE -n 30` |
| Hukommelse | `free -h` |
| Opdatér kode | `git pull` og derefter `systemctl restart gunicorn@<projekt>` |
