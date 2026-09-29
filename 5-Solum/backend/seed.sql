-- Fiktive testdata
INSERT INTO employee (name, experience, role) VALUES
  ('Jesper (erfaren)', 'erfaren', 'tekniker'),
  ('Lone (erfaren)', 'erfaren', 'maskinfører'),
  ('Mikkel (nyansat)', 'nyansat', 'maskinfører'),
  ('Sara (nyansat)', 'nyansat', 'maskinfører'),
  ('Thomas (driftsleder)', 'erfaren', 'driftsleder');

INSERT INTO machine (name, nickname, location, type, icon) VALUES
  ('Sorteringsrobot', 'Jespers robot', 'Hal A', 'Sortering', '🤖'),
  ('Læssemaskine 1', 'Lones læsser', 'Pladsen nord', 'Læssemaskine', '🚜'),
  ('Læssemaskine 2', NULL, 'Pladsen syd', 'Læssemaskine', '🚜'),
  ('Neddeler', 'Bents neddeler', 'Hal B', 'Neddeler', '🪓'),
  ('Tromlesigte', NULL, 'Hal A', 'Sigte', '🌀'),
  ('Magnetseparator', NULL, 'Hal A', 'Separator', '🧲'),
  ('Balle-presser', 'Hennings presser', 'Hal C', 'Presser', '📦'),
  ('Transportbånd A', NULL, 'Hal A', 'Transport', '➡️');

INSERT INTO competence (employee_id, machine_id, level, approved_date) VALUES
  (1, 1, 'ekspert', '2024-03-01'), (1, 4, 'godkendt', '2024-05-10'), (1, 5, 'godkendt', '2025-01-12'),
  (1, 6, 'ekspert', '2023-11-02'), (1, 8, 'godkendt', '2024-02-20'),
  (2, 2, 'ekspert', '2022-09-01'), (2, 3, 'godkendt', '2023-04-15'), (2, 7, 'godkendt', '2024-06-01'),
  (3, 2, 'under oplæring', '2026-09-15'), (3, 8, 'godkendt', '2026-09-20'),
  (4, 3, 'under oplæring', '2026-09-22'),
  (5, 2, 'godkendt', '2021-01-01'), (5, 3, 'godkendt', '2021-01-01');

INSERT INTO article (machine_id, author_id, fault_type, title, steps, tags, level, media_url, created_date) VALUES
  (1, 1, 'Nødstop', 'Robotten står i nødstop efter fastklemt emne',
   'Tryk på den gule reset-knap ved styreskabet
Kontrollér at der ikke sidder emner fast ved griberen
Kør båndet baglæns i 5 sekunder via panelet
Start robotten fra panelet med "Auto"',
   'nødstop,fastklemt,E-101,stopper,griber', 'grundlæggende', NULL, '2026-08-12'),
  (1, 1, 'Kamera', 'Kamera genkender ikke materialer (fejlkode E-230)',
   'Rens kameraets linse med den blå klud
Kontrollér belysningen i sorteringskabinen
Genstart vision-softwaren fra servicemenuen
Hvis fejlen fortsætter: kalibrér kameraet efter manualens afsnit 4',
   'kamera,E-230,genkender ikke,forkert sortering,vision', 'dybdegående', NULL, '2026-08-20'),
  (1, 1, 'Luft', 'Lavt lufttryk – griberen taber emner',
   'Aflæs manometeret ved kompressoren (skal være 6 bar)
Tøm vandudskilleren
Kontrollér slangerne for utætheder
Genstart kompressoren',
   'lufttryk,taber,griber,kompressor,E-150', 'grundlæggende', NULL, '2026-09-01'),
  (2, 2, 'Hydraulik', 'Skovlen løfter langsomt',
   'Kontrollér hydraulikolie-niveauet i skueglasset
Se efter olie under maskinen
Lad motoren varme op i 10 minutter i koldt vejr
Kontakt tekniker hvis niveauet er ok og fejlen fortsætter',
   'hydraulik,langsom,skovl,olie', 'grundlæggende', NULL, '2026-07-05'),
  (4, 1, 'Blokering', 'Neddeleren blokerer',
   'Stop fødningen og vent til rotoren står stille
Kør rotoren baglæns 2 omdrejninger
Fjern blokerende emner med krog – aldrig med hænderne
Start langsomt op igen',
   'blokerer,stopper,rotor,fastklemt', 'grundlæggende', NULL, '2026-06-18'),
  (8, 1, 'Bånd', 'Transportbåndet kører skævt',
   'Stop båndet
Justér strammeskruen på den side båndet trækker mod
Kør båndet tomt i 2 minutter og kontrollér',
   'skævt,bånd,slid', 'grundlæggende', NULL, '2026-05-02');

INSERT INTO fault_log (machine_id, employee_id, article_id, symptom, fault_type, timestamp, status, duration_minutes) VALUES
  (1, 3, 1, 'Robot stopper', 'Nødstop', '2026-08-14 07:30:00', 'LØST', 12),
  (1, 2, 1, 'nødstop', 'Nødstop', '2026-08-19 13:10:00', 'LØST', 8),
  (1, 3, 2, 'forkert sortering', 'Kamera', '2026-08-22 09:00:00', 'ULØST', 95),
  (1, 1, 2, 'E-230', 'Kamera', '2026-08-23 10:00:00', 'LØST', 40),
  (1, 4, 3, 'taber emner', 'Luft', '2026-09-03 11:20:00', 'LØST', 15),
  (1, 3, 1, 'stopper', 'Nødstop', '2026-09-10 06:45:00', 'LØST', 10),
  (1, 2, NULL, 'lyd fra motor', 'Ukendt', '2026-09-18 14:00:00', 'ULØST', 180),
  (2, 3, 4, 'skovl langsom', 'Hydraulik', '2026-09-12 08:00:00', 'LØST', 20),
  (4, 2, 5, 'blokerer', 'Blokering', '2026-09-15 10:30:00', 'LØST', 25),
  (1, 3, 1, 'nødstop', 'Nødstop', '2026-09-25 07:10:00', 'LØST', 9);
