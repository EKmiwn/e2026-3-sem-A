Kravspecifikation – Min Hessel

## 1. Formålet med projektet

Formålet med projektet er at udvikle en prototype på Min Hessel, som er en samlet digital kundeportal for Ejner Hessels kunder. Portalen skal samle oplysninger om kundens biler på tværs af bilmærker som Mercedes-Benz, Renault, Dacia og Ford.

Kunden skal blandt andet kunne se servicehistorik, dokumenter, aftaler, værkstedsbookinger og status på reparationer ét samlet sted. Løsningen skal skabe en mere sammenhængende kundeoplevelse, styrke kundeloyaliteten og gøre Ejner Hessels interne arbejdsprocesser mere effektive.

## 2. Interessenter og brugere

De primære brugere er privatkunder, som har købt eller leaset en bil gennem Ejner Hessel.

Projektets interessenter er:

- Ejner Hessels kunder
- Ejner Hessels ledelse
- Medarbejdere i kundeservice
- Værkstedsmedarbejdere
- Salgsmedarbejdere
- IT-medarbejdere
- Ejner Hessels forskellige bilmærker

Kunderne skal kunne finde deres oplysninger hurtigt, mens medarbejderne skal kunne oprette og opdatere information om biler, bookinger og reparationer.

## 3. Begrænsninger

Prototypen udvikles inden for en begrænset tidsperiode og vil derfor ikke indeholde alle funktionerne fra en færdig kundeportal.

Prototypen skal:

- Udvikles som en webapplikation
- Anvende React i frontend
- Anvende Node.js og Express i backend
- Anvende SQLite som database
- Følge en tre-lags arkitektur
- Kommunikere gennem HTTP og JSON
- Kun anvende testdata og ikke rigtige kundeoplysninger

Der udvikles ikke en mobilapp i denne version.

## 4. Projektets og produktets scope

Projektet omfatter udviklingen af en fungerende prototype på Min Hessel. Prototypen skal vise, hvordan en kunde kan få et samlet overblik over sine biler og de vigtigste oplysninger, der er knyttet til dem.

Prototypen omfatter:

- Oversigt over kundens biler
- Biloplysninger
- Servicehistorik
- Værkstedsbooking
- Status på en reparation
- Aftaler og dokumenter

Prototypen omfatter ikke:

- Betaling
- Integration med Ejner Hessels nuværende systemer
- Integration med bilmærkernes egne apps
- Brug af virkelige kundeoplysninger
- En færdig mobilapplikation

## 5. Funktionelle krav og datakrav

Systemet skal kunne:

- Vise en oversigt over kundens biler
- Vise oplysninger om den enkelte bil
- Vise bilens servicehistorik
- Vise kommende værkstedsbookinger
- Oprette, redigere og slette en booking
- Vise status på en igangværende reparation
- Vise kundens aftaler og dokumenter
- Hente og sende data mellem frontend og backend som JSON
- Gemme data i en SQLite-database
- Understøtte CRUD-funktionerne Create, Read, Update og Delete

Databasen skal blandt andet kunne indeholde:

- Kunder
- Biler
- Bookinger
- Servicehistorik
- Reparationsstatus
- Aftaler og dokumenter

## 6. Krav til design og udseende

Min Hessel skal have et enkelt, moderne og professionelt design, der passer til Ejner Hessels visuelle identitet.

Designet skal:

- Have en tydelig og overskuelig menu
- Bruge ensartede farver, skrifttyper og knapper
- Præsentere oplysninger i overskuelige bokse
- Være responsivt på computer, tablet og mobil
- Gøre de vigtigste oplysninger nemme at finde
- Have tydelige knapper til booking og biloplysninger

## 7. Krav til brugervenlighed

Systemet skal være nemt at anvende for kunder med forskellige digitale kompetencer.

Brugeren skal:

- Kunne forstå navigationen uden vejledning
- Kunne finde sine biloplysninger med få klik
- Kunne oprette en booking gennem en enkel proces
- Modtage en tydelig besked, når en handling er gennemført
- Modtage en forståelig fejlbesked, hvis noget går galt
- Kunne bruge systemet på både computer og mobil

## 8. Krav til ydeevne

Systemet skal reagere hurtigt og stabilt under almindelig anvendelse.

Der stilles følgende krav:

- Sider skal som udgangspunkt indlæses inden for tre sekunder
- Data skal hentes fra databasen uden unødvendig ventetid
- Systemet må ikke gå ned ved almindelig brug
- Backend skal returnere korrekte JSON-svar
- Fejl i kommunikationen mellem frontend og backend skal håndteres
- Data skal opdateres på siden efter en ændring

## 9. Sikkerhed og lovgivning

Prototypen må ikke indeholde virkelige eller følsomme kundeoplysninger. Al data skal være opdigtet testdata.

En færdig løsning skal:

- Beskytte kundernes personoplysninger
- Overholde GDPR
- Kræve sikkert login
- Sikre, at kunder kun kan se deres egne oplysninger
- Beskytte kommunikationen mellem bruger og server
- Begrænse medarbejdernes adgang efter deres arbejdsopgaver
- Opbevare data sikkert og forhindre uautoriseret adgang

## 10. Risici og uafklarede spørgsmål

Projektets vigtigste risici er:

- Manglende tid til at udvikle alle funktionerne
- Problemer med forbindelsen mellem frontend, backend og database
- Uklarhed om, hvilke eksisterende systemer Ejner Hessel anvender
- Vanskeligheder ved at samle data fra forskellige bilmærker
- Risiko for, at løsningen bliver for omfattende
- Risiko for fejl eller manglende data i prototypen

Det er endnu uafklaret, hvordan en færdig løsning skal integreres med Ejner Hessels og bilmærkernes eksisterende systemer.

## 11. Idéer til fremtidige løsninger

Følgende funktioner kan tilføjes i en senere version:

- Personligt og sikkert login
- Automatisk import af oplysninger fra bilmærkernes systemer
- Onlinebetaling
- Notifikationer om service og reparationer
- Digital kommunikation med værkstedet
- Liveopdatering af reparationsstatus
- Integration med forsikring og leasingaftaler
- En mobilapp til iOS og Android
- Personlige anbefalinger baseret på kundens bil og servicehistorik
