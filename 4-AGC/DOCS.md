# AGC Biologics – QC Informationshub – dokumentation af prototypen

Prototypen undersøger, hvordan et samlet informationssystem kan reducere QC-lederes manuelle arbejde med at finde, samle og sortere information.
Kildeposter fra Outlook og Teams modtages **automatisk** gennem simulerede connectors. Systemet vurderer relevans, foreslår kategori og resumé,
og lederen **kontrollerer, godkender og deler**, men skal ikke selv kopiere information ind.

Kravgrundlag: [`Kravspecifikation.md`](Kravspecifikation.md)

## Hvad kan prototypen

| Skærm | Funktion |
|---|---|
| **Til kontrol** (leder) | Kø med relevante og tvetydige udkast. Detaljevisning med originalkilde, "hvorfor fanget", rettelse (ny version), godkendelse, fravalg, deling med forhåndsvisning samt delings- og hændelseshistorik |
| **Søg** | Fritekst i titel/resumé kombineret med kategori, kildesystem og status. Kun tilladt indhold vises |
| **Delt med mig** (medarbejder) | Delte snapshots med knappen *Markér som læst* |
| **Kilder og testfeed** | *Modtag næste testpost* sender en fiktiv Outlook- eller Teams-post gennem connectoren. Manuel note og hændelseslog |
| **Administration** | CRUD for kategorier med nøgleord og for kategoriadgang (læs/redigér) |

Testkontoen vælges i toppen og sendes med hvert kald i headeren `X-User-Id` (simuleret login).

## Informationsflowet (DFD level 0–3)

```mermaid
flowchart LR
    F["Outlook / Teams<br/>(testfeed)"] -->|"F1/F2"| P1["1.0 Modtag<br/>ingest()"]
    N["Manuel note"] -->|"F3"| P1
    P1 --> D1[("source")]
    P1 --> P2["2.0 Filtrér og strukturér<br/>score_categories()<br/>suggest_category()<br/>make_summary()"]
    P2 -->|"irrelevant"| D5[("event · Fravalgt")]
    P2 -->|"relevant/tvetydig"| D2[("info · UDKAST")]
    D2 --> P3["3.0 Kontrollér, godkend, del<br/>edit / approve / share"]
    P3 --> D4[("share + share_recipient")]
    D2 --> P4["4.0 Find og vis<br/>search_info()"]
    D4 --> P4
```

## Fra krav til kode

| Krav | Implementering |
|---|---|
| F01 Roller og kategoriadgang | `current_user()`, `require_role()`, `can_view()`, `can_edit()`. Andres poster giver 403 |
| F02 To simulerede connectors, ingen dubletter | `POST /api/connectors/outlook\|teams` + `UNIQUE(system, external_id)` → 409 |
| F03 Relevans via regler/nøgleord, fravalg logges | `score_categories()`. Uden match: `processing_status = FRAVALGT` + hændelse |
| F04 Entydigt kategoriforslag, ellers Uklassificeret | `suggest_category()`: højeste score skal være > 0 og entydig (BR6) |
| F05 Redigerbart resumé med kildehenvisning | `make_summary()` (to første sætninger). `info.source_id` peger på originalen |
| F06 Rettelse øger version og ophæver godkendelse | `edit_info()`. `check_version()` kræver `expected_version` (optimistisk låsning, 409) |
| F07 Kun godkendt info deles. Én ugyldig modtager afviser alt | `share_info()` + transaktion |
| F08 Søgning og filtrering, tom tilstand | `GET /api/info?q=&category_id=&system=&status=` |
| F09 Medarbejdere ser kun godkendt/delt indhold | `can_view()` for rollen medarbejder + `GET /api/shared-with-me` (snapshots) |
| F10 Manuel note gennemgår samme flow | `POST /api/notes` → `ingest(manual=True)` |
| F11 Hændelseslog | Tabellen `event`: E01 modtaget … E06 delt, samt fravalg |
| F12 Historik | `GET /api/info/<id>` returnerer `shares` og `history` |
| F13 Admin vedligeholder kategorier, regler og adgang. Brugt kategori kan ikke slettes | CRUD. Fremmednøgle → 409 ved sletning |
| F14 Markér som læst | `POST /api/shares/<id>/read` → `read_at` |
| BR1 Intet deles automatisk | `ingest()` opretter altid `UDKAST` |
| BR5 Delt version er uforanderlig | `share.snapshot` gemmer en JSON-kopi af den godkendte version |
| BR7 Administrator ser ikke kildetekst | `can_view()` returnerer `False` for administrator |

**Eksempel på kategoriregel:** Bemanding har nøgleordene *vagtplan, bemanding, ferie, sygdom, vikar, overarbejde*.
"Ny vagtplan … ferie … vikarer" giver score 3 → Bemanding. "Kalibrering … bemanding" giver 1 til både Udstyr og Bemanding → Uklassificeret.

## Datamodel

```mermaid
erDiagram
    CATEGORY ||--o{ CATEGORY_ACCESS : "category_id"
    USER ||--o{ CATEGORY_ACCESS : "user_id"
    USER ||--o{ INFO : "approver_id"
    CATEGORY ||--o{ INFO : "category_id"
    USER ||--o{ INFO : "owner_id"
    SOURCE ||--o{ INFO : "source_id"
    USER ||--o{ SHARE : "sender_id"
    INFO ||--o{ SHARE : "info_id"
    USER ||--o{ SHARE_RECIPIENT : "user_id"
    SHARE ||--o{ SHARE_RECIPIENT : "share_id"
    USER {
        INTEGER id PK
        TEXT name
        TEXT login
        TEXT role
        INTEGER active
    }
    CATEGORY {
        INTEGER id PK
        TEXT name
        TEXT keywords
        INTEGER active
    }
    CATEGORY_ACCESS {
        INTEGER id PK
        INTEGER user_id FK
        INTEGER category_id FK
        TEXT permission
    }
    SOURCE {
        INTEGER id PK
        TEXT system
        TEXT external_id
        TEXT sender
        TEXT channel
        TEXT title
        TEXT text
        TEXT received_at
        TEXT processing_status
    }
    INFO {
        INTEGER id PK
        INTEGER source_id FK
        INTEGER owner_id FK
        TEXT title
        TEXT summary
        INTEGER category_id FK
        TEXT match_basis
        TEXT status
        INTEGER version
        INTEGER approver_id FK
        TEXT approved_at
    }
    SHARE {
        INTEGER id PK
        INTEGER info_id FK
        INTEGER sender_id FK
        INTEGER version
        TEXT snapshot
        TEXT shared_at
    }
    SHARE_RECIPIENT {
        INTEGER share_id PK
        INTEGER user_id PK
        TEXT read_at
    }
    EVENT {
        INTEGER id PK
        INTEGER source_id
        INTEGER info_id
        INTEGER actor_id
        TEXT type
        TEXT occurred_at
        TEXT details
    }
    TEST_FEED {
        INTEGER id PK
        TEXT system
        TEXT external_id
        TEXT sender
        TEXT channel
        TEXT title
        TEXT text
        INTEGER delivered
    }
```

| Tabel | Rolle (D-numre fra DFD) |
|---|---|
| `source` | D1: original kildepost, ændres aldrig |
| `info` | D2: udkast/godkendt post med resumé, kategori og version |
| `category` · `category_access` | D3: kategorier, nøgleord og adgang |
| `share` · `share_recipient` | D4: delinger med snapshot og læst-tidspunkt |
| `event` | D5: hændelseslog |
| `test_feed` | Fiktive Outlook/Teams-poster, som connectoren afleverer |

## Eksempel på dataudveksling

Den simulerede Outlook-connector afleverer en ny mail. Systemet finder nøgleordene *audit, sop, gmp*, foreslår Quality og opretter et udkast:

```bash
curl -X POST http://localhost:5104/api/connectors/outlook \
  -H 'Content-Type: application/json' \
  -d '{"external_id": "MSG-9001", "sender": "qa@agc.test", "title": "Audit næste uge", "text": "Husk at læse SOP QC-014 før audit. GMP-kravene til dokumentation er skærpet."}'
```

Svar `201`:

```json
{
  "source_id": 1,
  "relevant": true,
  "info": {
    "id": 1,
    "source_id": 1,
    "owner_id": 1,
    "title": "Audit næste uge",
    "summary": "Husk at læse SOP QC-014 før audit. GMP-kravene til dokumentation er skærpet.",
    "category_id": 2,
    "match_basis": "Quality: audit, sop, gmp (score 3)",
    "status": "UDKAST",
    "version": 1,
    "approver_id": null,
    "approved_at": null,
    "category_name": "Quality",
    "system": "Outlook",
    "external_id": "MSG-9001",
    "…": "6 felter mere"
  },
  "candidates": [
    {
      "category_id": 2,
      "name": "Quality",
      "score": 3,
      "keywords": [
        "audit",
        "sop",
        "… (forkortet)"
      ]
    }
  ]
}
```

## Kør prototypen

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # første gang
pip install -r requirements.txt                       # første gang
python app.py
```

Terminalen skriver ` * Åbn http://localhost:5104`. Åbn adressen i browseren. Flask serverer både API'et (`/api/...`) og frontenden.

- **Port:** Prototypen bruger port **5104** (5100 + projektnummer). Er porten optaget, vælger `run()` i `core.py` selv den næste ledige og skriver fx ` * Port 5104 er optaget – bruger port 5105 i stedet`. Du kan også vælge port selv med `PORT=5200 python app.py`.
- **Stop serveren** med `Ctrl` + `C` i terminalen, hvor den kører.
- **Kodeændringer:** Serveren kører i debug-tilstand og genstarter selv, når du gemmer en `.py`-fil. Den bliver på samme port. Ændringer i `frontend/` kræver kun, at du genindlæser siden.
- **Database:** `backend/database.db` oprettes med testdata ved første start. Nulstil den med `python database.py --reset`, mens serveren er stoppet.
- **Tjek at backenden svarer:** `curl http://localhost:5104/api/health`

### Fejlfinding

| Problem | Årsag | Løsning |
|---|---|---|
| ` * Port 5104 er optaget – bruger port …` | En anden proces, ofte en glemt server, bruger porten | Brug den adresse, der står i terminalen. Se hvad der optager porten med `lsof -nP -iTCP:5104 -sTCP:LISTEN`. En Flask-server i debug-tilstand er to processer, så stop dem begge med `lsof -t -iTCP:5104 -sTCP:LISTEN \| xargs kill` |
| `ModuleNotFoundError: No module named 'flask'` | Det virtuelle miljø er ikke aktiveret, eller Flask er ikke installeret | `source .venv/bin/activate` og `pip install -r requirements.txt` |
| Siden viser "Kan ikke hente data fra backenden" | Serveren kører ikke, eller `index.html` er åbnet direkte fra disken, mens serveren kører på en anden port | Start serveren og åbn adressen fra terminalen i stedet for filen |
| Tallene passer ikke efter mange tests | Databasen indeholder testdata fra tidligere afprøvninger | Stop serveren og kør `python database.py --reset` |
| `no such table …` | `database.db` er tom eller ødelagt | `python database.py --reset` |

## Arkitektur

Prototypen følger holdets fælles tre-lags struktur (se [`../README.md`](../README.md)):

```mermaid
flowchart LR
    subgraph Klient["Browser – præsentationslag"]
        HTML["index.html + style.css"] --- JS["app.js"] --- API["api.js · api()"]
    end
    subgraph Server["Flask – logiklag"]
        ROUTES["app.py · endepunkter og forretningsregler"] --- CORE["core.py · run(), register_crud(), ApiError"]
    end
    subgraph Data["Datalag"]
        DBPY["database.py"] --- DB[("SQLite3 · database.db")]
    end
    API <-->|"HTTP + JSON"| ROUTES
    CORE --- DBPY
```

| Fil | Lag | Indhold |
|---|---|---|
| `frontend/index.html` | Præsentation | Skærmbilleder som faneblade og formularer. Projektets farver og `data-api-port` |
| `frontend/app.js` | Præsentation | Henter data med `api()`, tegner dem i DOM'en og sender formularer |
| `frontend/api.js` | Præsentation | Fælles for alle prototyper: `api()` (fetch + JSON), `h()`, `renderTable()`, `fillSelect()`, `formToJson()`, `bindCrudForm()` og `toast()` |
| `frontend/style.css` | Præsentation | Fælles responsivt design |
| `backend/app.py` | Logik | Projektets forretningsregler og endepunkter |
| `backend/core.py` | Logik | Fælles: `create_app()` (Flask, CORS, JSON-fejl), `run()` (start på ledig port), `ApiError` og `register_crud()` |
| `backend/database.py` | Data | Fælles: forbindelse, `query_all/query_one/execute`, `transaction()` og `init_db()` |
| `backend/schema.sql` · `seed.sql` | Data | Tabeller og fiktive testdata |

Alle fejl returneres som JSON (`{"error": "…", "path": "/api/…"}`) med statuskode 400, 401, 403, 404 eller 409 og vises som en rød besked i frontenden.
Nederst på siden kan man åbne **"Seneste JSON-svar fra API'et"** og se den rå dataudveksling.
Den fulde endepunktsliste står i [`backend/README.md`](backend/README.md).

## Design og responsivitet

- Samme stylesheet i alle prototyper. Kun farverne (`--brand`, `--brand-dark`, `--brand-soft`) sættes i `index.html`.
- Layoutet virker fra mobil (375 px) til desktop uden vandret scroll. Kort lægger sig under hinanden på små skærme, og brede tabeller scroller inde i deres kort.
- Formularfelter kan ikke blive bredere end deres kort. En `<select>` med lange valgmuligheder skubber altså ikke formularen ud over kanten.
- Beskeder vises kort i toppen (grøn = gennemført, rød = fejl fra serveren).


## Testdata og testkonti

| Rolle | Konti |
|---|---|
| Leder | Hanne (alle kategorier), Peter (Quality, Udstyr), Sofie (Bemanding, Træning) |
| Medarbejder | Ali, Bente, Carl, Dorte, Emil (forskellig læseadgang) |
| Administrator | Ida |

4 kategorier og 13 testfeed-poster med relevante, irrelevante, tvetydige og én dublet.
De første 8 modtages automatisk, når databasen oprettes, så *Til kontrol* ikke er tom.

## Afgrænsning

Ingen rigtig Microsoft Graph-integration, adgangskode eller AI-resumé. Resuméet er de første sætninger, og kategoriseringen er en nøgleordsheuristik, som beskrevet i A4.
