# Kravspecifikation – LoopAAS

## 1. Formål med projektet

Formålet med LoopAAS er at gøre New Loops retursystem mere motiverende gennem gamification.

Brugere optjener LoopPoints, når de returnerer New Loop-emballage. Pointene kan bruges på rewards hos samarbejdspartnere, fx en gratis kaffe eller andre tilbud.

Målet er at:
- øge motivationen for at returnere emballage
- gøre returprocessen mere engagerende
- skabe værdi for både brugere, New Loop og samarbejdspartnere

---

## 2. Stakeholders

De vigtigste stakeholders er:

- **New Loop** – ejer det eksisterende retursystem
- **Brugere** – returnerer emballage og optjener LoopPoints
- **Samarbejdspartnere** – fx caféer, der tilbyder rewards
- **Restauranter/takeaway-steder** – udleverer New Loop-emballage
- **Udviklingsteamet** – udvikler og vedligeholder prototypen

---

## 3. Brugere af produktet

Den primære bruger er en forbruger, der køber takeaway i New Loop-emballage.

Brugeren skal kunne:

- registrere en returnering
- optjene LoopPoints
- se sin pointsaldo
- se tilgængelige rewards
- indløse rewards
- se historik over returneringer og point

---

## 4. Scope

### Produktet omfatter

- brugerprofil
- registrering af returnering
- tildeling af LoopPoints
- pointsaldo
- reward-katalog
- indløsning af rewards
- historik

### Produktet omfatter ikke

- rigtig betaling
- fuld integration med New Loops eksisterende system
- fysisk returhardware
- samarbejdspartnernes interne IT-systemer

---

## 5. Business Use Case

Det overordnede forretningsflow er:

1. Brugeren køber takeaway i New Loop-emballage
2. Brugeren returnerer emballagen
3. Returneringen registreres
4. Systemet godkender returneringen
5. Brugeren modtager LoopPoints
6. Brugeren ser sine point
7. Brugeren vælger en reward
8. Systemet kontrollerer pointsaldoen
9. Reward indløses hos en samarbejdspartner

---

## 6. Product Use Case

Brugerrejsen kan beskrives sådan:

| Fase | Brugerhandling | Systemets respons |
|---|---|---|
| Køb | Brugeren modtager New Loop-emballage | Emballagen kan senere returneres |
| Returnering | Brugeren afleverer emballagen | Returneringen registreres |
| Point | Brugeren får godkendt returneringen | LoopPoints tilføjes |
| Overblik | Brugeren åbner LoopAAS | Pointsaldo vises |
| Reward | Brugeren vælger en belønning | Systemet kontrollerer point |
| Indløsning | Brugeren indløser reward | Pointsaldo reduceres |

---

## 7. Funktionelle krav

| ID | Funktionelt krav |
|---|---|
| FR01 | Systemet skal kunne identificere en bruger |
| FR02 | Systemet skal kunne registrere en returnering |
| FR03 | Systemet skal kunne tildele LoopPoints efter en godkendt returnering |
| FR04 | Brugeren skal kunne se sin pointsaldo |
| FR05 | Brugeren skal kunne se tilgængelige rewards |
| FR06 | Brugeren skal kunne indløse en reward |
| FR07 | Systemet skal kontrollere, om brugeren har nok point |
| FR08 | Systemet skal reducere pointsaldoen efter indløsning |
| FR09 | Brugeren skal kunne se sin historik |
| FR10 | Systemet skal gemme brugere, returneringer, point og rewards |

---

## 8. Non-funktionelle krav

- Systemet skal være mobilvenligt
- Systemet skal være let at forstå
- Centrale funktioner skal være nemme at finde
- Pointsaldoen skal opdateres efter en godkendt returnering
- Systemet skal håndtere fejl
- Brugerdata skal behandles sikkert
- Løsningen skal kunne udvides med flere rewards og samarbejdspartnere

---

## 9. Tre-lags arkitektur

### Præsentationslag

Præsentationslaget er den del, brugeren interagerer med.

Det indeholder fx:

- brugerprofil
- pointsaldo
- rewards
- historik
- knap til registrering af returnering

### Logiklag

Logiklaget håndterer systemets forretningslogik.

Det skal fx:

- validere returneringer
- beregne LoopPoints
- kontrollere pointsaldo
- håndtere indløsning af rewards
- håndtere fejl

### Datalag

Datalaget gemmer systemets data.

Det kan fx gemme:

- brugere
- returneringer
- pointsaldo
- rewards
- indløsninger

---

## 10. Data / ER-struktur

Forslag til entiteter:

### User

- UserID
- Name
- Email
- Points

### Return

- ReturnID
- UserID
- Date
- PointsEarned

### Reward

- RewardID
- Name
- PointsRequired
- PartnerID

### Partner

- PartnerID
- Name

### Redemption

- RedemptionID
- UserID
- RewardID
- Date

---

## 11. Events

| Event | Trigger | Resultat |
|---|---|---|
| Returnering registreres | Brugeren afleverer emballage | Returnering gemmes |
| Point tildeles | Returnering godkendes | Pointsaldo opdateres |
| Reward vælges | Brugeren vælger reward | Point kontrolleres |
| Reward indløses | Brugeren har nok point | Point trækkes |
| Fejl opstår | Ugyldig handling | Fejlbesked vises |

---

## 12. Antagelser og begrænsninger

Prototypen bygger på følgende antagelser:

- returneringer kan identificeres digitalt
- en godkendt returnering kan udløse LoopPoints
- samarbejdspartnere kan tilbyde rewards
- brugere har en unik profil
- prototypen anvender testdata