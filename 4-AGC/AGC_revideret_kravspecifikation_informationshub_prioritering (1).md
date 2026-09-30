# AGC Biologics Copenhagen

## Revideret kravspecifikation -- Informationshub med Leverancer & Prioritering

**Økonomi & IT · 3. semester · EK -- Erhvervsakademi København**\
**Revideret efter fokusgruppe 29. september 2026**\
**Arbejdsgrundlag for prototype**

------------------------------------------------------------------------

# 1. Formålet med projektet

Prototypen skal undersøge, hvordan et fælles digitalt informationshub
kan gøre intern information mere overskuelig og relevant for
medarbejdere og ledere hos AGC Biologics Copenhagen.

Den oprindelige løsningsidé fastholdes: information fra forskellige
kanaler skal kunne samles, filtreres, kategoriseres og gøres lettere at
finde. Formålet er at mindske den tid, brugerne anvender på at finde
relevant information og skabe et mere samlet overblik.

På baggrund af fokusgruppen udvides løsningen med en ny funktion:
**Leverancer & Prioritering**. Fokusgruppen viste et yderligere behov
blandt lederne for at kunne skabe et fælles overblik over, hvilke
opgaver og leverancer der er vigtigst, hvem der har ansvaret, hvilken
deadline de har, og hvor langt de er.

Løsningen består derfor af to sammenhængende hovedområder:

1.  **Informationshub** -- samler, filtrerer og strukturerer relevant
    information.
2.  **Leverancer & Prioritering** -- giver ledere og teams et fælles
    overblik over vigtige leverancer og deres prioritet.

Prototypen skal ikke erstatte AGC's eksisterende kvalitetssystemer eller
øvrige autoritative systemer. Den skal undersøge, om et fælles digitalt
overblik kan understøtte informationshåndtering og prioritering.

## Succeskriterier

-   Brugeren kan finde relevant information i informationshubben.
-   Information kan kategoriseres og filtreres.
-   Lederen kan oprette en leverance og angive prioritet.
-   Brugeren kan se leverancens ansvarlige team/person, deadline og
    status.
-   De vigtigste leverancer kan identificeres uden at åbne hver enkelt
    leverance.
-   Lederen kan ændre prioriteringen, når situationen ændrer sig.
-   Prototypen giver et samlet overblik uden at skabe unødvendig ekstra
    information.

------------------------------------------------------------------------

# 2. Baggrund for ændringen

Den oprindelige løsning blev udviklet på baggrund af projektets første
dataindsamling, hvor udfordringer omkring informationsmængde, relevans,
tid og forskellige informationskanaler blev identificeret.

Fokusgruppen gav en mere detaljeret forståelse af ledernes udfordringer.
Deltagerne beskrev blandt andet:

-   manglende fælles prioritering på tværs af teams,
-   behov for bedre overblik over leverancer,
-   lokale Excel-ark, Planner-boards og individuelle systemer,
-   uklart ansvar i forbindelse med opgaver,
-   meget manuel koordinering,
-   forskelle i hvad teams opfatter som vigtigst.

På den baggrund erstattes den oprindelige informationshub **ikke**. Den
videreudvikles i stedet med en funktion til **Leverancer &
Prioritering**.

Dette følger projektets Design Thinking-tilgang: ny brugerindsigt
anvendes til at justere og videreudvikle løsningen.

------------------------------------------------------------------------

# 3. Interessenter

  -------------------------------------------------------------------------
  Interessent             Behov/interesse         Rolle
  ----------------------- ----------------------- -------------------------
  QC-ledere               Relevant information    Primære brugere af
                          samt overblik og        prioriteringsfunktionen
                          prioritering af         
                          leverancer              

  QC-medarbejdere         Let adgang til relevant Brugere
                          information og          
                          tydelighed om relevante 
                          leverancer              

  Andre QC-teams / QA     Fælles overblik over    Samarbejdende teams
                          relevante leverancer    

  AGC IT                  Sikkerhed, adgang og    Teknisk interessent
                          eventuelle              
                          integrationer           

  Ledelse/business        Overblik over kritiske  Sekundær interessent
                          leverancer              
  -------------------------------------------------------------------------

------------------------------------------------------------------------

# 4. Brugere af produktet

## QC-leder

QC-lederen skal kunne:

-   se relevant information,
-   godkende eller håndtere relevant information i informationshubben,
-   oprette leverancer,
-   fastsætte og ændre prioritet,
-   angive ansvarlig person eller team,
-   angive deadline og status,
-   få overblik over de vigtigste leverancer.

## QC-medarbejder

QC-medarbejderen skal kunne:

-   finde relevant information,
-   søge og filtrere information,
-   se relevante leverancer,
-   se prioritet, ansvar, deadline og status,
-   undgå at blive præsenteret for unødvendig information.

------------------------------------------------------------------------

# 5. Produktets overordnede scope

## 5.1 Informationshub -- eksisterende kernefunktion

Informationshubben fastholdes som løsningens centrale del.

Den skal understøtte:

-   samlet informationsoversigt,
-   kategorisering af information,
-   filtrering,
-   søgning,
-   visning af relevant information,
-   mulighed for at dele information med relevante brugere/teams,
-   mulighed for opsummering af information,
-   strukturering efter emne eller kategori.

Information kan i prototypen være baseret på fiktive data, som
repræsenterer information fra eksempelvis Teams og Outlook.

## 5.2 Leverancer & Prioritering -- ny funktion

Den nye funktion skal give et fælles overblik over opgaver og
leverancer.

En leverance skal som minimum indeholde:

-   titel,
-   beskrivelse,
-   prioritet,
-   ansvarligt team/person,
-   deadline,
-   status.

Funktionen skal gøre det muligt at se, hvilke leverancer der bør
håndteres først.

### Foreslåede prioriteter

-   Business Critical
-   High
-   Normal
-   Low

Prioritetsniveauerne er et prototypeforslag og skal valideres med AGC.

### Foreslåede statusser

-   Ikke startet
-   I gang
-   Afventer
-   Blokeret
-   Afsluttet

Statusbegreberne skal ligeledes valideres med AGC.

------------------------------------------------------------------------

# 6. Foreslået brugerflow

## Informationsflow

**INFORMATION MODTAGES → FILTRERES → KATEGORISERES → VURDERES → GØRES
TILGÆNGELIG FOR RELEVANTE BRUGERE**

Brugeren skal efterfølgende kunne søge og finde informationen i
informationshubben.

## Leverance- og prioriteringsflow

**OPRET LEVERANCE → ANGIV PRIORITET → TILDEL ANSVARLIG → ANGIV DEADLINE
→ OPDATÉR STATUS → AFSLUT**

Prioriteten skal kunne ændres undervejs, hvis en leverance bliver mere
eller mindre vigtig.

------------------------------------------------------------------------

# 7. Centrale skærmbilleder

## 7.1 Home / Informationshub

Skal vise:

-   relevant information,
-   seneste information,
-   kategorier,
-   søgefelt,
-   filtre,
-   mulighed for at åbne information,
-   genvej til Leverancer & Prioritering.

## 7.2 Informationsdetalje

Skal vise:

-   titel,
-   indhold eller opsummering,
-   kategori,
-   kilde,
-   dato,
-   relevante teams/personer,
-   mulighed for at dele eller markere information.

## 7.3 Leverancer & Prioritering

Skal vise et samlet overblik over leverancer med:

-   titel,
-   prioritet,
-   ansvarlig,
-   deadline,
-   status.

Som udgangspunkt sorteres de vigtigste leverancer øverst.

Eksempel:

  Leverance           Prioritet           Ansvarlig   Deadline   Status
  ------------------- ------------------- ----------- ---------- --------------
  Batch Release 245   Business Critical   QA          02/10      I gang
  Stability Report    High                Stability   04/10      Afventer
  Method Update       Normal              QC          08/10      Ikke startet

## 7.4 Leverancedetalje

Skal vise:

-   titel,
-   beskrivelse,
-   prioritet,
-   ansvarligt team/person,
-   deadline,
-   status,
-   eventuelle kommentarer,
-   historik over centrale ændringer.

## 7.5 Opret/redigér leverance

Lederen skal kunne:

-   oprette titel og beskrivelse,
-   vælge prioritet,
-   vælge ansvarlig,
-   vælge deadline,
-   vælge status,
-   gemme leverancen.

------------------------------------------------------------------------

# 8. Funktionelle krav

  ----------------------------------------------------------------------------------
  ID                Krav                  MoSCoW            Acceptkriterium
  ----------------- --------------------- ----------------- ------------------------
  F01               Brugeren skal kunne   Must              Informationsoversigten
                    se information samlet                   vises på forsiden.
                    i informationshubben.                   

  F02               Brugeren skal kunne   Must              Information vises med en
                    kategorisere                            kategori.
                    information.                            

  F03               Brugeren skal kunne   Must              Søgeresultater matcher
                    søge efter                              søgeord.
                    information.                            

  F04               Brugeren skal kunne   Must              Filtrering ændrer den
                    filtrere information.                   viste information.

  F05               Relevant information  Must              Modtager/relevans
                    skal kunne knyttes                      fremgår af
                    til relevante                           informationen.
                    teams/personer.                         

  F06               Brugeren skal kunne   Must              Informationsdetalje
                    åbne og læse                            vises.
                    information.                            

  F07               Systemet skal kunne   Should            Opsummering vises på
                    vise en kort                            kort eller detaljeside.
                    opsummering af                          
                    information.                            

  F08               Leder skal kunne      Must              Leverancen gemmes og
                    oprette en leverance.                   vises i oversigten.

  F09               Leder skal kunne      Must              Business Critical, High,
                    angive prioritet på                     Normal eller Low kan
                    en leverance.                           vælges.

  F10               Systemet skal vise    Must              Kritiske/høje leverancer
                    leverancer                              kan identificeres
                    sorteret/markeret                       hurtigt.
                    efter prioritet.                        

  F11               Leder skal kunne      Must              Ansvarlig vises på
                    angive ansvarligt                       leverancen.
                    team/person.                            

  F12               Leder skal kunne      Must              Deadline vises i
                    angive deadline.                        oversigten.

  F13               Leverancen skal have  Must              Status vises på oversigt
                    en status.                              og detaljeside.

  F14               Leder skal kunne      Must              Ændringen vises straks.
                    ændre prioritet.                        

  F15               Leder skal kunne      Must              Ændringer gemmes.
                    ændre ansvarlig,                        
                    deadline og status.                     

  F16               Brugeren skal kunne   Should            Kombinerede filtre
                    filtrere leverancer                     virker.
                    efter prioritet,                        
                    ansvarlig og status.                    

  F17               Systemet skal kunne   Should            Overdue/overskredet
                    markere overskredne                     vises tydeligt.
                    deadlines.                              

  F18               Systemet skal kunne   Could             Ændring, tidspunkt og
                    vise historik over                      bruger vises.
                    centrale ændringer på                   
                    en leverance.                           

  F19               Information skal      Could             Relevant
                    senere kunne kobles                     informationspost kan
                    til en konkret                          forbindes med
                    leverance.                              leverancen.

  F20               AI kan senere bruges  Could             AI-forslag kræver
                    til opsummering og                      brugerens godkendelse.
                    forslag til actions.                    
  ----------------------------------------------------------------------------------

------------------------------------------------------------------------

# 9. Forretningsregler

-   BR1: En leverance skal have titel, prioritet, ansvarlig og deadline.
-   BR2: Business Critical skal kunne identificeres tydeligt i
    leveranceoversigten.
-   BR3: Kun relevante brugere skal kunne ændre prioritet.
-   BR4: Prioritet skal kunne ændres, når situationen ændrer sig.
-   BR5: En afsluttet leverance skal fortsat kunne findes.
-   BR6: Status "Blokeret" bør ledsages af en kort begrundelse.
-   BR7: Information og leverancer skal holdes adskilt som to
    funktioner, men skal kunne forbindes i en senere version.
-   BR8: Notifikationer må kun bruges ved relevante handlinger og må
    ikke skabe en ny informationsbelastning.

------------------------------------------------------------------------

# 10. Tre-lags arkitektur

## Præsentationslag

Brugerfladen består primært af:

1.  Home / Informationshub
2.  Informationsdetalje
3.  Leverancer & Prioritering
4.  Leverancedetalje
5.  Opret/redigér leverance

## Logiklag

### Informationslogik

-   filtrering,
-   kategorisering,
-   søgning,
-   relevans,
-   visning til relevante brugere.

### Prioriteringslogik

-   leverancer har en prioritet,
-   højere prioritet vises før lavere prioritet,
-   prioritet kan ændres,
-   deadline kan markeres som overskredet,
-   status kan opdateres,
-   ansvarlig kan ændres.

## Datalag

### Information

-   information_id
-   titel
-   indhold
-   kategori
-   kilde
-   dato
-   relevant_team
-   opsummering

### Leverance

-   leverance_id
-   titel
-   beskrivelse
-   prioritet
-   ansvarlig_team
-   ansvarlig_bruger
-   deadline
-   status
-   oprettet_tid

### Bruger

-   bruger_id
-   navn
-   rolle
-   team_id

### Team

-   team_id
-   teamnavn

### Hændelse

-   event_id
-   leverance_id
-   bruger_id
-   type
-   tidspunkt
-   detaljer

------------------------------------------------------------------------

# 11. DFD -- overordnet forslag

## Kontekstdiagram

**QC-LEDER / QC-MEDARBEJDER ↔ INFORMATIONSHUB & PRIORITERINGSSYSTEM ↔
DATA**

## Level 0

### 1.0 Håndter information

Modtager, kategoriserer, filtrerer og viser information.

### 2.0 Find information

Søgning og filtrering af relevant information.

### 3.0 Håndter leverance

Opretter og redigerer leverancer.

### 4.0 Håndter prioritering

Fastlægger og ændrer prioritet.

### 5.0 Vis leveranceoverblik

Viser leverancer efter prioritet, ansvar, deadline og status.

------------------------------------------------------------------------

# 12. Events

  -----------------------------------------------------------------------
  Event                   Trigger                 Systemrespons
  ----------------------- ----------------------- -----------------------
  E01 InformationOprettet Ny information          Information gemmes og
                          registreres             kategoriseres

  E02 InformationDelt     Information gøres       Informationen vises for
                          relevant for            relevante brugere
                          team/person             

  E03 LeveranceOprettet   Leder opretter          Leverancen vises i
                          leverance               oversigten

  E04 PrioritetÆndret     Leder ændrer prioritet  Oversigt og rækkefølge
                                                  opdateres

  E05 AnsvarligÆndret     Ny ansvarlig vælges     Leverancen opdateres

  E06 StatusÆndret        Status ændres           Ny status vises

  E07 DeadlineOverskredet Deadline passeres       Leverancen markeres
                                                  overskredet

  E08 LeveranceAfsluttet  Status sættes til       Leverancen flyttes til
                          afsluttet               afsluttede
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 13. Non-funktionelle krav

## Brugervenlighed

-   NF01: Brugeren skal hurtigt kunne forstå forskellen mellem
    information og leverancer.
-   NF02: De vigtigste leverancer skal kunne identificeres uden at åbne
    dem.
-   NF03: Prioritet, ansvarlig, deadline og status skal være synlige i
    samme oversigt.
-   NF04: Systemet skal anvende ensartede betegnelser.
-   NF05: Centrale handlinger skal kræve få klik.

## Ydeevne og robusthed

-   NF06: Prototypen skal opleves responsiv i en moderne browser.
-   NF07: Gentagne klik må ikke skabe dubletter.
-   NF08: Fejl skal kommunikeres tydeligt til brugeren.

## Sikkerhed

-   NF09: Prototypen skal anvende fiktive eller anonymiserede data.
-   NF10: Brugere skal kun kunne ændre funktioner, de har rettighed til.
-   NF11: Eventuelle fremtidige integrationer skal følge AGC's
    sikkerheds- og adgangskrav.

------------------------------------------------------------------------

# 14. Visuelt design

Informationshubben og prioriteringsfunktionen skal opleves som dele af
**samme løsning**.

Navigationen kan eksempelvis bestå af:

-   Home
-   Information
-   Leverancer
-   Prioritering

Leveranceoversigten skal være enkel og handlingsorienteret.

Prioritet og status skal kommunikeres med både tekst og visuelle
markeringer. Farve må ikke være den eneste indikator.

Den vigtigste designregel er:

> Brugeren skal hurtigt kunne forstå: **Hvad er vigtigt lige nu, hvem
> har ansvaret, og hvornår skal det være færdigt?**

------------------------------------------------------------------------

# 15. Afgrænsninger

Første prototype skal ikke:

-   erstatte LIMS, TrackWise eller andre kvalitetssystemer,
-   anvende rigtige fortrolige produktionsdata,
-   integrere direkte med AGC's systemer,
-   automatisere hele QC-processen,
-   implementere et komplekst tværgående workflow,
-   foretage automatisk AI-prioritering,
-   beslutte prioritet uden en leder.

Første prototype skal primært demonstrere **informationshubben samt den
nye funktion til Leverancer & Prioritering**.

------------------------------------------------------------------------

# 16. Åbne spørgsmål til validering med AGC

-   Hvilke prioritetsniveauer bruger lederne allerede?
-   Hvem skal have rettighed til at ændre prioritet?
-   Skal prioriteringen være fælles for hele QC eller pr. team?
-   Hvilke oplysninger skal en leverance som minimum indeholde?
-   Hvilke statusbegreber giver bedst mening for AGC?
-   Skal medarbejdere kunne ændre status på leverancer?
-   Hvor ofte skal prioriteringen opdateres?
-   Skal information kunne kobles direkte til en leverance?
-   Skal leverancer senere kunne hente data fra Planner, Excel eller
    andre systemer?

------------------------------------------------------------------------

# 17. Risici

  -----------------------------------------------------------------------
  Risiko                              Håndtering
  ----------------------------------- -----------------------------------
  Løsningen bliver endnu et system    Prototypen skal undersøge samlet
                                      overblik; integration vurderes
                                      senere

  Prioriteringen bliver ikke fælles   Beslutningsret skal afklares

  Prioriteter bliver forældede        Tydeligt ansvar for opdatering

  For mange notifikationer            Kun relevante ændringer bør
                                      notificeres

  Leverancefunktionen bliver for      Første prototype holdes enkel
  kompleks                            

  Informationshub og leverancer       Ens navigation og visuelt design
  opleves som to separate systemer    
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 18. Accepttest

  -----------------------------------------------------------------------
  Test                    Scenarie                Forventet resultat
  ----------------------- ----------------------- -----------------------
  T01                     Find en bestemt         Brugeren kan finde den
                          informationspost        via søgning/filter

  T02                     Filtrér information     Kun relevant
                          efter kategori          information vises

  T03                     Opret en leverance      Leverancen vises i
                                                  oversigten

  T04                     Sæt leverance til       Leverancen
                          Business Critical       fremhæves/prioriteres

  T05                     Ændr prioritet fra      Oversigten opdateres
                          Normal til High         

  T06                     Tildel ansvarlig        Ansvarlig vises på
                                                  leverancen

  T07                     Ændr status til I gang  Ny status vises

  T08                     Filtrér efter High + I  Kun matchende
                          gang                    leverancer vises

  T09                     Overskrid deadline      Leverancen markeres
                                                  tydeligt

  T10                     Brugertest med leder    Lederen kan
                                                  identificere vigtigste
                                                  leverance, ansvarlig og
                                                  deadline
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 19. Waiting room / senere udvikling

Funktioner der kan undersøges senere:

-   kobling mellem informationsposter og konkrete leverancer,
-   integration med Microsoft Teams,
-   integration med Planner/Power Platform,
-   automatisk import af information fra Outlook,
-   AI-genererede informationsresuméer,
-   AI-genererede møderesuméer og actions,
-   forslag til prioritet,
-   mere avancerede workflows mellem teams,
-   kapacitetsplanlægning,
-   KPI'er og ledelsesrapportering.

------------------------------------------------------------------------

# 20. Prototype -- anbefalet første version

Den første prototype bør fokusere på følgende fem skærme:

1.  **Home / Informationshub**
2.  **Information**
3.  **Leverancer & Prioritering**
4.  **Leverancedetalje**
5.  **Opret/redigér leverance**

Den vigtigste nye funktion efter fokusgruppen er **Leverancer &
Prioritering**.

Et simpelt demonstrationsscenarie kan være:

1.  Lederen åbner informationshubben.
2.  Lederen går til **Leverancer**.
3.  Tre eller flere aktuelle leverancer vises.
4.  Lederen identificerer en leverance som vigtig.
5.  Prioriteten ændres til **Business Critical**.
6.  Leverancen placeres tydeligt øverst/fremhæves.
7.  Lederen kan se ansvarlig, deadline og status.
8.  En medarbejder kan efterfølgende se, hvilke leverancer der har
    højeste prioritet.

------------------------------------------------------------------------

# 21. Sammenhæng mellem dataindsamling og løsning

## Før fokusgruppen

Den første dataindsamling pegede på udfordringer med:

-   informationsmængde,
-   irrelevant information,
-   tid,
-   forskellige kanaler,
-   behov for bedre overblik.

Dette dannede grundlag for **informationshubben**.

## Efter fokusgruppen

Fokusgruppen gjorde især følgende udfordring tydeligere:

-   fælles prioritering af opgaver og leverancer,
-   overblik over hvad der er vigtigst,
-   ansvar for leverancer,
-   forskellige lokale prioriteringer,
-   manuel koordinering.

Dette danner grundlag for den nye funktion **Leverancer &
Prioritering**.

## Samlet løsning

**INFORMATIONSHUB + LEVERANCER & PRIORITERING**

Løsningen videreudvikles dermed på baggrund af ny brugerindsigt frem for
at erstatte den oprindelige idé.

------------------------------------------------------------------------

# 22. Kort problem-løsning-sammenhæng

  -----------------------------------------------------------------------
  Identificeret udfordring            Funktion i prototypen
  ----------------------------------- -----------------------------------
  Information ligger forskellige      Informationshub
  steder                              

  Brugerne modtager irrelevant        Filtrering og kategorisering
  information                         

  Det tager tid at finde information  Søgning og samlet overblik

  Ledere skal vurdere hvad der er     Relevans og informationshåndtering
  relevant                            

  Manglende fælles prioritering       Leverancer & Prioritering

  Uklart hvad der er vigtigst         Prioritetsniveau og sortering

  Uklart hvem der har ansvaret        Ansvarligt team/person

  Manglende overblik over deadlines   Deadline på leverancen

  Manglende overblik over fremdrift   Status på leverancen
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 23. Konklusion på kravspecifikationen

Den reviderede prototype fastholder den oprindelige idé om et fælles
informationshub. Fokusgruppen anvendes til at videreudvikle løsningen
med en ny funktion til **Leverancer & Prioritering**.

Kernen i prototypen bliver derfor ikke et fuldt
workflow-management-system. Den bliver et samlet informations- og
overbliksværktøj, hvor den nye prioriteringsfunktion skal hjælpe lederne
med lettere at vurdere:

**Hvilke leverancer bør løses først?**

Samtidig skal brugerne kunne se:

**Hvem har ansvaret? Hvad er deadline? Og hvad er status?**

Kravene skal efterfølgende valideres gennem prototype- og brugertest med
relevante brugere.
