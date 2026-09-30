-- Fiktive testdata: 4 teams, 3 ledere, 5 medarbejdere, 1 administrator, 4 kategorier, 7 leverancer
INSERT INTO team (name) VALUES ('QC'), ('QA'), ('Stability'), ('QC Træning');

INSERT INTO user (name, login, role, team_id) VALUES
  ('Hanne Leder', 'hanne', 'leder', 1),
  ('Peter Leder', 'peter', 'leder', 2),
  ('Sofie Leder', 'sofie', 'leder', 4),
  ('Ali Medarbejder', 'ali', 'medarbejder', 1),
  ('Bente Medarbejder', 'bente', 'medarbejder', 2),
  ('Carl Medarbejder', 'carl', 'medarbejder', 3),
  ('Dorte Medarbejder', 'dorte', 'medarbejder', 1),
  ('Emil Medarbejder', 'emil', 'medarbejder', 4),
  ('Ida Administrator', 'ida', 'administrator', NULL);

INSERT INTO category (name, keywords) VALUES
  ('Bemanding', 'vagtplan,bemanding,ferie,sygdom,vikar,overarbejde'),
  ('Quality', 'afvigelse,deviation,capa,audit,sop,gmp'),
  ('Udstyr', 'hplc,kalibrering,instrument,service,nedbrud,vedligehold'),
  ('Træning', 'træning,kursus,oplæring,certificering,introduktion');

INSERT INTO category_access (user_id, category_id, permission) VALUES
  (1, 1, 'redigér'), (1, 2, 'redigér'), (1, 3, 'redigér'), (1, 4, 'redigér'),
  (2, 2, 'redigér'), (2, 3, 'redigér'),
  (3, 1, 'redigér'), (3, 4, 'redigér'),
  (4, 1, 'læs'), (4, 3, 'læs'),
  (5, 1, 'læs'), (5, 2, 'læs'), (5, 4, 'læs'),
  (6, 3, 'læs'),
  (7, 1, 'læs'), (7, 2, 'læs'), (7, 3, 'læs'), (7, 4, 'læs'),
  (8, 4, 'læs');

INSERT INTO test_feed (system, external_id, sender, channel, title, text) VALUES
  ('Outlook', 'MSG-0001', 'hr@agc.test', NULL, 'Ny vagtplan for uge 41', 'Vagtplan for uge 41 er klar. Husk at melde ferie senest fredag. To vikarer starter mandag.'),
  ('Teams', 'TMS-0001', 'Lab-teamet', 'QC Lab', 'HPLC 3 nede', 'HPLC 3 har nedbrud og afventer service. Brug HPLC 2 til analyser indtil videre.'),
  ('Outlook', 'MSG-0002', 'qa@agc.test', NULL, 'Afvigelse DEV-2231 åbnet', 'Der er åbnet en afvigelse på batch 118. CAPA skal vurderes inden audit i næste uge.'),
  ('Outlook', 'MSG-0003', 'kantine@agc.test', NULL, 'Menu i kantinen', 'Fredag serveres der lasagne og salat. Kaffemaskinen på 2. sal er repareret.'),
  ('Teams', 'TMS-0002', 'Træningskoordinator', 'QC Træning', 'Nyt GMP-kursus', 'GMP-kursus og oplæring for nye medarbejdere afholdes den 12. Tilmelding i LMS.'),
  ('Teams', 'TMS-0003', 'Lab-teamet', 'QC Lab', 'Kalibrering og bemanding', 'Kalibrering af pipetter kræver ekstra bemanding torsdag. Hvem kan tage vagten?'),
  ('Outlook', 'MSG-0004', 'it@agc.test', NULL, 'Opdatering af Windows', 'Din computer genstarter i nat for at installere opdateringer.'),
  ('Outlook', 'MSG-0005', 'qa@agc.test', NULL, 'Opdateret SOP for prøvemodtagelse', 'SOP QC-014 er revideret. Læs ændringerne inden audit. GMP krav om dokumentation er skærpet.'),
  ('Teams', 'TMS-0004', 'Hanne Leder', 'QC Ledere', 'Sygdom i teamet', 'To medarbejdere er meldt syge. Vi skal finde en vikar og justere vagtplan for weekenden.'),
  ('Teams', 'TMS-0005', 'Social klub', 'Generelt', 'Fredagsbar', 'Fredagsbar kl. 15 i atriet – alle er velkomne!'),
  ('Outlook', 'MSG-0006', 'service@leverandor.test', NULL, 'Servicebesøg på instrument', 'Serviceteknikeren kommer tirsdag for vedligehold af instrument 7 og kalibrering.'),
  ('Outlook', 'MSG-0007', 'træning@agc.test', NULL, 'Certificering udløber', 'Certificering for tre analytikere udløber i november. Planlæg træning og introduktion.'),
  ('Teams', 'TMS-0001', 'Lab-teamet', 'QC Lab', 'HPLC 3 nede (gentaget)', 'Samme besked sendt igen – skal ikke give en dublet.');

-- Leverancer med deadlines i forhold til dags dato, så én altid er overskredet (F17)
INSERT INTO deliverable (title, description, priority, team_id, owner_id, deadline, status, blocked_reason, created_by, created_at, closed_at) VALUES
  ('Batch Release 245', 'Frigivelse af batch 245 kræver færdige QC-analyser og QA-review.', 'Business Critical', 2, 5, date('now', 'localtime', '+2 days'), 'I gang', NULL, 1, datetime('now', 'localtime', '-5 days'), NULL),
  ('Stability Report', 'Kvartalsvis stabilitetsrapport for produkt B.', 'High', 3, 6, date('now', 'localtime', '+4 days'), 'Afventer', NULL, 1, datetime('now', 'localtime', '-6 days'), NULL),
  ('Method Update', 'Opdatering af analysemetode efter ny SOP QC-014.', 'Normal', 1, 4, date('now', 'localtime', '+8 days'), 'Ikke startet', NULL, 2, datetime('now', 'localtime', '-2 days'), NULL),
  ('CAPA-opfølgning DEV-2231', 'Vurdér CAPA for afvigelsen på batch 118 inden audit.', 'High', 2, NULL, date('now', 'localtime', '-1 days'), 'I gang', NULL, 2, datetime('now', 'localtime', '-9 days'), NULL),
  ('Kalibrering af HPLC 3', 'HPLC 3 skal kalibreres, før den tages i brug igen.', 'Normal', 1, 7, date('now', 'localtime', '+5 days'), 'Blokeret', 'Afventer servicetekniker fra leverandøren', 1, datetime('now', 'localtime', '-3 days'), NULL),
  ('Træningsplan for nye analytikere', 'Plan for oplæring og certificering i Q4.', 'Low', 4, 8, date('now', 'localtime', '+20 days'), 'Ikke startet', NULL, 3, datetime('now', 'localtime', '-1 days'), NULL),
  ('Vagtplan uge 40', 'Bemanding af laboratoriet i uge 40.', 'Normal', 1, NULL, date('now', 'localtime', '-3 days'), 'Afsluttet', NULL, 1, datetime('now', 'localtime', '-12 days'), datetime('now', 'localtime', '-4 days'));

INSERT INTO deliverable_comment (deliverable_id, user_id, text, created_at) VALUES
  (1, 5, 'QC-analyserne er modtaget. QA-review starter i morgen.', datetime('now', 'localtime', '-1 days')),
  (5, 1, 'Leverandøren har bekræftet besøg på tirsdag.', datetime('now', 'localtime', '-1 days'));

INSERT INTO event (deliverable_id, actor_id, type, occurred_at, details) VALUES
  (1, 1, 'E03 LeveranceOprettet', datetime('now', 'localtime', '-5 days'), 'High · deadline sat'),
  (1, 1, 'E04 PrioritetÆndret', datetime('now', 'localtime', '-2 days'), 'High → Business Critical'),
  (1, 2, 'E06 StatusÆndret', datetime('now', 'localtime', '-2 days'), 'Ikke startet → I gang'),
  (7, 1, 'E08 LeveranceAfsluttet', datetime('now', 'localtime', '-4 days'), 'I gang → Afsluttet');
