-- Fiktive testdata
INSERT INTO customer (name, email, car_plate) VALUES
  ('Gustav Jensen', 'gustav@test.dk', 'GM 12 345'),
  ('Sara Nielsen', 'sara@test.dk', 'GM 22 811'),
  ('Ali Hassan', 'ali@test.dk', 'GM 31 070');

INSERT INTO hotspot (name, address, area) VALUES
  ('Nørreport Station', 'Frederiksborggade 2, 1360 København K', 'Indre By'),
  ('Fisketorvet', 'Kalvebod Brygge 59, 1560 København V', 'Vesterbro'),
  ('Lyngbyvej / Ryparken', 'Lyngbyvej 100, 2100 København Ø', 'Østerbro'),
  ('Amager Strandpark', 'Amager Strandvej 110, 2300 København S', 'Amager');

INSERT INTO spot (hotspot_id, label, status) VALUES
  (1, 'A1', 'OPTAGET'), (1, 'A2', 'OPTAGET'), (1, 'A3', 'LEDIG'), (1, 'A4', 'SPAERRET'),
  (2, 'B1', 'LEDIG'), (2, 'B2', 'LEDIG'), (2, 'B3', 'OPTAGET'), (2, 'B4', 'LEDIG'), (2, 'B5', 'LEDIG'),
  (3, 'C1', 'OPTAGET'), (3, 'C2', 'OPTAGET'), (3, 'C3', 'OPTAGET'),
  (4, 'D1', 'LEDIG'), (4, 'D2', 'OPTAGET'), (4, 'D3', 'LEDIG');

INSERT INTO reservation (reservation_no, customer_id, spot_id, status, created_at, arrival_deadline, arrived_at, closed_at) VALUES
  ('R-1001', 2, 7, 'BENYTTET', '2026-09-28 08:00:00', '2026-09-28 08:20:00', '2026-09-28 08:14:00', '2026-09-28 08:14:00'),
  ('R-1002', 3, 13, 'UDLOEBET', '2026-09-28 17:30:00', '2026-09-28 17:50:00', NULL, '2026-09-28 17:50:00'),
  ('R-1003', 1, 5, 'ANNULLERET', '2026-09-28 19:00:00', '2026-09-28 19:20:00', NULL, '2026-09-28 19:05:00');
