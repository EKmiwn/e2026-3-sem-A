-- Fiktive testdata
INSERT INTO customer (name, email, car_plate) VALUES
  ('Gustav Jensen', 'gustav@test.dk', 'GM 12 345'),
  ('Sara Nielsen', 'sara@test.dk', 'GM 22 811'),
  ('Ali Hassan', 'ali@test.dk', 'GM 31 070');

INSERT INTO hotspot (name, address, area, lat, lng, directions) VALUES
  ('Nørreport Station', 'Frederiksborggade 2, 1360 København K', 'Indre By', 55.6833, 12.5716,
   'Pladserne ligger i vejsiden over for Torvehallerne. Kig efter de grønne GreenMobility-skilte.'),
  ('Fisketorvet', 'Kalvebod Brygge 59, 1560 København V', 'Vesterbro', 55.6627, 12.5585,
   'Kør ind i P-kælderen ved indgang 2. Pladserne står længst til venstre ved elevatoren.'),
  ('Lyngbyvej / Ryparken', 'Lyngbyvej 100, 2100 København Ø', 'Østerbro', 55.7185, 12.5620,
   'Pladserne ligger på P-pladsen bag stationen, første række ved cykelparkeringen.'),
  ('Amager Strandpark', 'Amager Strandvej 110, 2300 København S', 'Amager', 55.6555, 12.6440,
   'Pladserne ligger på den store P-plads ved Øresundsstien, tæt på toiletbygningen.'),
  ('Vesterport Station', 'Vesterbrogade 2B, 1620 København V', 'Vesterbro', 55.6758, 12.5620,
   'Pladserne ligger i Kampmannsgade ved stationens udgang mod søerne.'),
  ('Valby Station', 'Toftegårds Plads 1, 2500 Valby', 'Valby', 55.6636, 12.5160,
   'Pladserne ligger på P-pladsen ved busterminalen, markeret med grøn maling.'),
  ('Frederiksberg Centret', 'Falkoner Allé 21, 2000 Frederiksberg', 'Frederiksberg', 55.6810, 12.5330,
   'Kør ned i P-kælderen fra Solbjergvej. Pladserne står ved udkørslen, niveau -1.'),
  ('Nordhavn Station', 'Nordhavnsvej 2, 2150 Nordhavn', 'Østerbro', 55.7050, 12.5910,
   'Pladserne ligger ved siden af stationens cykelparkering på Sandkaj-siden.'),
  ('Ørestad Station', 'Ørestads Boulevard 75, 2300 København S', 'Amager', 55.6290, 12.5790,
   'Pladserne ligger i Field''s P-hus, niveau 1, lige ved rampen.');

INSERT INTO spot (hotspot_id, label, status) VALUES
  (1, 'A1', 'OPTAGET'), (1, 'A2', 'OPTAGET'), (1, 'A3', 'LEDIG'), (1, 'A4', 'SPAERRET'),
  (2, 'B1', 'LEDIG'), (2, 'B2', 'LEDIG'), (2, 'B3', 'OPTAGET'), (2, 'B4', 'LEDIG'), (2, 'B5', 'LEDIG'),
  (3, 'C1', 'OPTAGET'), (3, 'C2', 'OPTAGET'), (3, 'C3', 'OPTAGET'),
  (4, 'D1', 'LEDIG'), (4, 'D2', 'OPTAGET'), (4, 'D3', 'LEDIG'),
  (5, 'E1', 'LEDIG'), (5, 'E2', 'OPTAGET'), (5, 'E3', 'LEDIG'),
  (6, 'F1', 'OPTAGET'), (6, 'F2', 'OPTAGET'),
  (7, 'G1', 'LEDIG'), (7, 'G2', 'LEDIG'), (7, 'G3', 'OPTAGET'), (7, 'G4', 'SPAERRET'),
  (8, 'H1', 'LEDIG'), (8, 'H2', 'LEDIG'),
  (9, 'I1', 'OPTAGET'), (9, 'I2', 'LEDIG'), (9, 'I3', 'LEDIG');

INSERT INTO reservation (reservation_no, customer_id, spot_id, status, created_at, arrival_deadline, arrived_at, closed_at) VALUES
  ('R-1001', 2, 7, 'BENYTTET', '2026-09-28 08:00:00', '2026-09-28 08:20:00', '2026-09-28 08:14:00', '2026-09-28 08:14:00'),
  ('R-1002', 3, 13, 'UDLOEBET', '2026-09-28 17:30:00', '2026-09-28 17:50:00', NULL, '2026-09-28 17:50:00'),
  ('R-1003', 1, 5, 'ANNULLERET', '2026-09-28 19:00:00', '2026-09-28 19:20:00', NULL, '2026-09-28 19:05:00');

INSERT INTO staff (name, role, online) VALUES
  ('Maja Holm', 'Kundeservice', 1),
  ('Jonas Berg', 'Kundeservice', 1),
  ('Line Krogh', 'Driftsmedarbejder på gaden', 0);
