# Kravspecifikation for Amitylux-prototype

## 1. Formål

Denne kravspecifikation omsætter projektets analyser og primære data til krav til en digital prototype for Amitylux. Prototypen skal hjælpe B2C-kunder med at forstå forskellen mellem Amitylux' public, private og customised oplevelser, finde et relevant tilbud og afgive en kvalificeret forespørgsel. Samtidig skal løsningen reducere unødigt manuelt arbejde uden at fjerne den personlige service, som er en central del af Amitylux' værditilbud.

Kravene er formuleret, så de kan spores til projektets datagrundlag og testes i en prototype.

## 2. Foreslået løsningskoncept

Prototypen afgrænses til en digital oplevelsesvælger og forespørgselsrejse på Amitylux' hjemmeside. Kunden guides fra behovsafdækning til en begrundet anbefaling og kan derefter enten booke et standardprodukt eller sende et struktureret oplæg til Amitylux om en private/customised oplevelse.

Løsningen skal være digital selvbetjening med menneskelig overlevering – ikke en fuldautomatisk rejseplanlægger. Denne retning bygger især på følgende fund:

- Kunderne efterspørger tydelig information, anbefalinger og filtrering, men Amitylux vil bevare personlig dialog ved komplekse bookinger.
- Customised bookinger kræver i dag meget kommunikation og koordinering.
- Private og customised bookinger udgør mindre volumen end public tours, men kan have væsentligt højere værdi pr. booking.
- Små grupper, lokal ekspertise, fleksibilitet, tryghed og personlig service er centrale kundeværdier.

## 3. Målgruppe og designprincipper

### Primær målgruppe

B2C-rejsende i alderen 30–44 år, særligt par, familier og mindre grupper med interesse for private, fleksible og eksklusive storbyoplevelser. Segmentet er valgt som primært, fordi 85 % i spørgeskemaundersøgelsen vurderer unikke eller eksklusive oplevelser som vigtige eller meget vigtige, 75 % er villige til at betale ekstra, og 95 % tillægger tryghed og sikkerhed høj betydning.

### Sekundære målgrupper

- Rejsende på 45 år og derover, som vægter tryghed, bekvemmelighed, kommunikation og personlig service.
- Rejsende på 18–29 år, som er mere prisfølsomme og har behov for en tydelig forklaring af merværdien.
- Eksisterende public-tour-kunder, som kan være relevante for private, customised eller supplerende services.

### Designprincipper

1. **Tydelighed før valg:** Kunden skal forstå pris, indhold, fleksibilitet og forskelle mellem produkttyper.
2. **Personalisering med kontrol:** Kunden skal kunne angive og ændre præferencer og se, hvorfor noget anbefales.
3. **Digital effektivitet med menneskelig service:** Løsningen skal strukturere dialogen, men bevare adgang til en medarbejder.
4. **Tillid før konvertering:** Lokal ekspertise, anmeldelser, serviceforventninger og praktisk information skal være synlige.
5. **Premium uden kompleksitet:** Oplevelsen skal afspejle kvalitet og eksklusivitet uden at gøre processen tung.

## 4. Prioriteringsmetode

Kravene prioriteres efter MoSCoW:

- **Must:** Nødvendigt for at demonstrere prototypens kerneværdi.
- **Should:** Vigtigt, men prototypen kan testes uden fuld implementering.
- **Could:** Relevant videreudvikling, hvis tid og ressourcer tillader det.
- **Won't (nu):** Bevidst uden for prototypens nuværende scope.

## 5. Funktionelle krav

| ID | Prioritet | Krav | Acceptkriterium for prototypen | Kilde |
|---|---|---|---|---|
| F-01 | Must | Løsningen skal indsamle kundens destination, dato/periode, gruppetype, gruppestørrelse, interesser, ønsket sprog, tempo/fleksibilitet og omtrentligt budget. | En testbruger kan gennemføre behovsafdækningen, gå tilbage og ændre svar samt se en opsummering før afsendelse. | I-1, I-3, I-6; D-6, D-8; S-3 |
| F-02 | Must | Løsningen skal forklare og sammenligne **public small-group**, **private** og **customised** oplevelser. | Sammenligningen viser mindst gruppetype, grad af fleksibilitet, personalisering, pris/princip, bookingform samt hvad der er inkluderet og ikke inkluderet. | I-3, I-6; S-3; D-3 |
| F-03 | Must | Løsningen skal anbefale én primær og højst to alternative oplevelsestyper ud fra kundens svar. | Hver anbefaling viser en kort, forståelig begrundelse koblet til mindst to af kundens valgte præferencer. | S-3, S-8; SW-2; P-4 |
| F-04 | Must | Kunden skal kunne filtrere eller justere anbefalinger efter prisniveau, sprog, gruppestørrelse og interesse. | Ændring af et filter opdaterer de viste forslag, og aktive filtre er synlige og kan nulstilles. | S-3: 30 ønsker filtrering; D-6, D-8 |
| F-05 | Must | Løsningen skal vise tydelige priser eller prisprincipper og klart angive, hvad der er inkluderet og ikke inkluderet. | Alle viste forslag har pris eller teksten "pris efter forespørgsel" samt særskilte felter for inkluderet/ikke inkluderet. | S-3: 39 vægter pris, 39 ønsker tydeligt indhold; D-9 |
| F-06 | Must | Løsningen skal synliggøre merværdien ved Amitylux og den valgte oplevelse. | Resultatsiden viser relevante værdipunkter som lille gruppe, lokal ekspertise, fleksibilitet, tidsbesparelse, tryghed eller særlig adgang – tilpasset produktet. | I-1, I-5; S-2, S-3; K-1 |
| F-07 | Must | Løsningen skal understøtte sammensætning af en private/customised forespørgsel med relevante tilvalg. | Kunden kan vælge mindst guide/sprog, museum eller kultur, madoplevelse, privat transport, båd/havn og andre aktiviteter; valgene fremgår af opsummeringen. | I-3, I-6; D-6, D-8 |
| F-08 | Must | Kunden skal kunne overlevere sit strukturerede oplæg til en Amitylux-medarbejder. | Ved afsendelse vises kontaktoplysninger, præferencer, tilvalg og en forventningsafstemning om næste trin; kunden modtager en tydelig kvittering i prototypen. | I-3, I-10; SW-2 |
| F-09 | Must | Kunden skal på alle centrale trin kunne vælge personlig hjælp. | En synlig kontaktmulighed findes i behovsafdækning, anbefaling og opsummering, uden at allerede indtastede oplysninger går tabt. | I-3, I-10; K-1 |
| F-10 | Must | Løsningen skal bruge tillidsskabende indhold tæt på beslutningen. | Resultat- og detaljesider viser anmeldelser/social proof, guidekompetence, lokal viden og relevant praktisk information. | I-4, I-9; S-2, S-3; D-5 |
| F-11 | Should | Kunden skal kunne angive præferencer for guidens sprog, faglige fokus, kommunikationsstil og turens tempo. | Præferencerne gemmes i forespørgselsopsummeringen og præsenteres som ønsker, ikke som garanti. | I-4; D-9 |
| F-12 | Should | Løsningen skal forebygge urealistiske forventninger ved korte varsler og travle perioder. | Ved kort varsel eller højsæson vises en besked om mulig begrænset kapacitet og forslag om fleksible datoer eller alternativer. | I-8; D-4, D-10 |
| F-13 | Should | Løsningen skal foreslå relevante alternativer uden for de mest belastede turistområder. | Mindst ét relevant alternativ kan vises med begrundelse som færre mennesker, lokalt præg eller bæredygtig transport, når kundens præferencer passer. | P-1, P-2; SW-2; D-11 |
| F-14 | Should | Løsningen skal gøre andre relevante Amitylux-services og destinationer synlige uden at forstyrre hovedopgaven. | Efter anbefaling eller booking vises højst tre kontekstuelle forslag, fx transport, madoplevelse, anden aktivitet eller en anden eksisterende destination. | I-1, I-2, I-9; D-6 |
| F-15 | Should | Medarbejderen skal modtage en standardiseret forespørgsel, der kan bruges som brief. | Briefen grupperer kundedata, præferencer, tilvalg, fritekst, usikkerheder og næste handling i et ensartet format. | I-3, I-10; SW-1, SW-2 |
| F-16 | Could | Kunden skal kunne gemme eller dele sin anbefaling med medrejsende. | Prototypen viser en funktion til deling eller gemning af en stabil opsummering. | S-2: de fleste rejser med andre |
| F-17 | Could | Kunden skal kunne markere tidligere oplevelser eller interesser for at få relevante tilbud på tværs af Amitylux' destinationer. | En tilbagevendende bruger kan se mindst ét relevant forslag baseret på tidligere valg. | I-2, I-9, I-11 |
| F-18 | Could | Løsningen skal kunne vise mere bæredygtige valg. | Relevante forslag kan mærkes med fx gang, cykel, offentlig transport eller område uden for centrum, og mærkningen forklares. | P-2; K-1; SW-2 |

## 6. Ikke-funktionelle krav

| ID | Prioritet | Krav | Acceptkriterium for prototypen | Kilde |
|---|---|---|---|---|
| NF-01 | Must | Prototypen skal være mobilvenlig og fungere på de mest almindelige skærmstørrelser. | Kerneflowet kan gennemføres ved ca. 375 px mobilbredde og på desktop uden vandret scrolling eller skjulte handlinger. | S-3; P-3 |
| NF-02 | Must | Sproget skal være enkelt, internationalt forståeligt og i første prototype mindst tilgængeligt på engelsk. | Alle centrale skærme findes på engelsk; fagudtryk og produktforskelle forklares i almindeligt sprog. | I-1; D-1, D-8 |
| NF-03 | Must | Visuelt udtryk og tone skal understøtte Amitylux' premium-position og personlige service. | Brugertestere kan genkende mindst tre af værdierne kvalitet, personlighed, lokal autenticitet, ekspertise og eksklusivitet i løsningen. | K-1; S-9 |
| NF-04 | Must | Løsningen skal være transparent om anbefalinger og bevare brugerens kontrol. | Brugeren kan se, hvilke svar anbefalingen bygger på, ændre dem og fravælge forslag; prototypen må ikke love en endelig AI-booking. | I-10; S-3; SW-2 |
| NF-05 | Must | Indhold og komponenter skal kunne genbruges ensartet på tværs af destinationer. | Samme struktur anvendes for produktkort, guideinformation, inkluderet/ikke inkluderet og forespørgselsbrief på mindst to destinationseksempler. | I-2, I-4, I-11; D-9 |
| NF-06 | Should | Kerneflowet skal opleves hurtigt og overskueligt. | Mindst 80 % af testbrugerne kan nå fra start til en relevant anbefaling uden hjælp på højst fem minutter. | I-3, I-10; S-3 |
| NF-07 | Should | Prototypen skal begrænse indsamlingen til oplysninger, der er nødvendige for anbefaling og opfølgning. | Kontaktdata indsamles først ved afsendelse, og brugeren kan se, hvilke oplysninger der sendes til Amitylux. | Afledt af F-01 og F-08; skal valideres juridisk før implementering |

## 7. Forretningskrav og succeskriterier

| ID | Krav | Foreslået målepunkt ved test/pilot | Kilde |
|---|---|---|---|
| B-01 | Løsningen skal øge forståelsen af forskellen mellem public, private og customised. | Mindst 80 % af testbrugerne kan efter flowet forklare forskellen korrekt. | I-3; S-3 |
| B-02 | Løsningen skal skabe flere kvalificerede henvendelser til private/customised oplevelser. | Mindst 70 % af de afsendte testforespørgsler indeholder alle obligatoriske præferencefelter og kan vurderes uden en indledende afklaringsmail. | I-1, I-3, I-11; D-3 |
| B-03 | Løsningen skal bevare oplevelsen af personlig service. | Mindst 80 % af testbrugerne vurderer, at det er tydeligt, hvordan de får personlig hjælp. | I-3, I-10; K-1 |
| B-04 | Løsningen skal kommunikere premiumproduktets merværdi. | Mindst 75 % af testbrugerne kan nævne to konkrete grunde til at vælge private/customised frem for public. | S-3; I-5, I-6 |
| B-05 | Løsningen skal understøtte mere ensartet kvalitet og behandling af forespørgsler. | Alle testforespørgsler afleveres i samme briefstruktur på tværs af to destinationer. | I-2, I-4, I-11; D-9 |
| B-06 | Løsningen skal gøre mersalg relevant frem for påtrængende. | Mindst 50 % af testbrugerne vurderer de viste tilvalg som relevante; højst tre tilvalg vises ad gangen. | I-1, I-3, I-6; D-6 |

Måltallene er hypoteser for prototype- og pilottest. De er ikke dokumenterede historiske baselines og skal justeres, når Amitylux har målt den nuværende kunderejse.

## 8. Scope

### Indgår i MVP-prototypen

- Behovsafdækning og præferencevalg
- Sammenligning af de tre produkttyper
- Personlig anbefaling med begrundelse
- Filtrering og justering
- Tydelig pris- og indholdskommunikation
- Tilvalg til private/customised oplevelser
- Tillidsskabende information
- Opsummering og overlevering til en medarbejder
- Mobil og desktop visning

### Indgår ikke i denne prototype

- Betaling og juridisk bindende booking
- Live-integration til guider, hoteller, transport, restauranter eller attraktioner
- Automatisk bekræftelse af kapacitet eller specialadgang
- Fuldautomatisk AI-genereret og leverandørbooket rejseplan
- B2B-partnerportal
- Komplet CRM-, review- eller loyalitetssystem
- Udrulning til alle destinationer og sprog

## 9. Sporbarhed fra indsigt til krav

| Central indsigt | Evidens | Krav, der adresserer indsigten |
|---|---|---|
| Kunderne mangler tydelighed om produkttyper og forventer nogle gange private-egenskaber fra public tours. | Interview; SMP-analyse | F-02, F-05, F-06, B-01, B-04 |
| Store grupper, manglende fleksibilitet, uklarhed om indhold og dårlig kommunikation er centrale frustrationer. | Spørgeskema: 39, 17, 16 og 16 svar | F-02, F-05, F-09, F-10, F-11 |
| Kunder efterspørger digital tydelighed, anbefalinger, filtrering og tilpasning. | Spørgeskema: 39, 33, 30 og 21 svar | F-01, F-03, F-04, F-07 |
| Tryghed og anmeldelser vægtes højt på tværs af aldersgrupper. | SMP-analyse | F-10, NF-03, B-03 |
| Segmentet 30–44 år har stærkt match med eksklusive, personlige oplevelser. | 85 % interesse; 75 % betalingsvillighed; 95 % vægter tryghed | F-03, F-06, F-07, B-04 |
| Customised oplevelser er værdifulde, men kræver meget manuel koordinering. | Interview; virksomhedsdata; SWOT | F-01, F-07, F-08, F-15, B-02 |
| Personlig service må ikke forsvinde ved digitalisering. | Interview; kulturanalyse | F-08, F-09, NF-03, B-03 |
| Guide-match og ensartet kvalitet er operationelle udfordringer. | Interview; virksomhedsdata; SWOT | F-11, F-15, NF-05, B-05 |
| Peakperioder og korte varsler giver kapacitetsproblemer. | Interview; virksomhedsdata | F-12 |
| Amitylux vil styrke eksisterende destinationer og skabe genkøb på tværs. | Interview | F-14, F-17, NF-05 |
| Turismen er koncentreret i centrum, og bæredygtighedspresset stiger. | PESTLE; SWOT; virksomhedsdata | F-13, F-18 |
| Tilbuddene er værdifulde, men ikke vanskelige at kopiere enkeltvis. | VRIO; SWOT | F-03, F-06, NF-03 |

## 10. Testkrav

Prototypen bør testes med mindst 5–8 personer fra den primære målgruppe og, hvis muligt, 2–3 personer fra hver sekundær målgruppe. Testen skal som minimum undersøge:

1. Om brugeren forstår forskellen mellem public, private og customised.
2. Om spørgsmålene opleves relevante og tilstrækkelige.
3. Om anbefalingen passer til de angivne behov og kan forklares.
4. Om pris, inkluderet/ikke inkluderet og næste trin er tydelige.
5. Om brugeren oplever kontrol og adgang til personlig hjælp.
6. Om premiumproduktets merværdi er tydelig nok til at retfærdiggøre en højere pris.
7. Om medarbejderen kan arbejde videre fra den genererede brief uden væsentlig genindtastning eller gentagne grundspørgsmål.

Amitylux bør deltage i en særskilt faglig gennemgang af anbefalingslogik, produktindhold, guidepræferencer og realistiske løfter om kapacitet.

## 11. Datagrundlag og kildekoder

- **I:** [Amitylux-interview](data/Amitylux%20interview%20.pdf). Nummeret er interviewets afsnit, fx I-3 for bookingoplevelsen.
- **D:** [Virksomhedsdata](data/Data%20Amitylux(Ark1).csv). D-1 = kundemarked, D-3 = bookingtype, D-4 = sæson, D-5 = kundetilfredshed, D-6 = services og kundehenvendelser, D-8 = efterspurgte oplevelser, D-9 = klager/challenges, D-10 = svære forespørgsler og D-11 = geografi.
- **S:** [SMP-analyse](analyser/SMP%20analyse.pdf). S-2 = behov og beslutningskriterier, S-3 = guidede oplevelser og digital kunderejse, S-8 = segmentprofilen 30–44 år og S-9 = målgruppevalg, positionering og branding.
- **SW:** [SWOT- og TOWS-analyse](analyser/SWOT-%20%26%20TOWS%20Analyse.pdf). SW-1 = interne styrker/svagheder og SW-2 = muligheder/trusler.
- **P:** [PESTLE og Porter's Five Forces](analyser/PESTLE%20%26%20P5F%20(1).pdf). P-1 = turismespredning, P-2 = miljø/bæredygtighed, P-3 = digitale kanaler og P-4 = teknologi/AI.
- **K:** [Kulturanalyse](analyser/Kulturanalyse.pdf).
- **V:** [VRIO-analyse](analyser/VRIO-analyse.pdf).

**K-1** henviser til kulturens værdier og grundantagelser. **V-1** henviser til vurderingen af ressourcer, kompetencer og differentieringspotentiale.

## 12. Forbehold og valideringsbehov

- Spørgeskemaet har 74 respondenter og kan ikke uden videre generaliseres til hele Amitylux' internationale kundebase.
- Flere virksomhedsdata er estimater eller kvalitative vurderinger; deres datastyrke varierer fra lav til høj.
- Amitylux indsamler ikke systematisk kundernes alder, så målgruppevalget kan endnu ikke sammenholdes direkte med faktiske booking- og omsætningstal.
- Bookingvolumen må ikke forveksles med økonomisk værdi; private og customised bookinger kan være mere værdifulde pr. booking.
- Value Proposition Canvas er nævnt i projektbeskrivelsen, men der ligger ingen selvstændig VPC-fil i de tilgængelige mapper. Kravene bør opdateres, hvis analysen tilføjes.
- Før en produktionsløsning udvikles, skal krav til databeskyttelse, samtykke, tilgængelighed, sikkerhed, integrationer og faktisk svartid specificeres og godkendes.
