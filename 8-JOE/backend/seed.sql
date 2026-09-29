-- Fiktive testdata
INSERT INTO setting (key, value, description) VALUES
  ('deposit_amount', 5, 'Pant pr. kop i DKK (antagelse – ikke besluttet)'),
  ('points_per_krone', 10, 'Point pr. krone pant ved godkendt retur (antagelse)'),
  ('points_value_kr', 0.1, 'Værdi af ét point ved indløsning i DKK');

INSERT INTO store (name, city, location_type) VALUES
  ('JOE Strøget', 'København', 'Gade'),
  ('JOE Fields', 'København S', 'Storcenter'),
  ('JOE CPH Airport T3', 'Kastrup', 'Lufthavn'),
  ('JOE Aarhus C', 'Aarhus', 'Gade');

INSERT INTO customer (name, email, points) VALUES
  ('Sofie App-bruger', 'sofie@test.dk', 150),
  ('Jonas App-bruger', 'jonas@test.dk', 50),
  ('Maria App-bruger', 'maria@test.dk', 0);

INSERT INTO drink (name, price) VALUES
  ('Joe''s Club (juice)', 59), ('Pick Me Up', 59), ('Cafe Latte', 45), ('Green Shield', 62), ('Iced Americano', 42);

INSERT INTO sale_order (receipt_no, store_id, customer_id, drink_id, price, deposit, created_at) VALUES
  ('K-100001', 1, 1, 1, 59, 5, '2026-09-25 08:10:00'),
  ('K-100002', 1, 1, 3, 45, 5, '2026-09-26 08:05:00'),
  ('K-100003', 2, 2, 2, 59, 5, '2026-09-26 12:30:00'),
  ('K-100004', 3, NULL, 5, 42, 5, '2026-09-27 06:40:00'),
  ('K-100005', 1, 1, 4, 62, 5, '2026-09-28 09:15:00'),
  ('K-100006', 4, 3, 1, 59, 5, '2026-09-28 14:00:00');

INSERT INTO cup (code, order_id, status, issued_at, returned_at, returned_store_id) VALUES
  ('JOE-7F3A91C2', 1, 'RETURNERET', '2026-09-25 08:10:00', '2026-09-25 17:20:00', 1),
  ('JOE-1B77E0D4', 2, 'RETURNERET', '2026-09-26 08:05:00', '2026-09-26 10:02:00', 2),
  ('JOE-C41290AA', 3, 'UDLEVERET', '2026-09-26 12:30:00', NULL, NULL),
  ('JOE-99D0B3F1', 4, 'UDLEVERET', '2026-09-27 06:40:00', NULL, NULL),
  ('JOE-5E6A2C10', 5, 'UDLEVERET', '2026-09-28 09:15:00', NULL, NULL),
  ('JOE-0A11BEEF', 6, 'RETURNERET', '2026-09-28 14:00:00', '2026-09-28 14:35:00', 4);

INSERT INTO deposit_transaction (cup_id, customer_id, store_id, type, amount, points, created_at, note) VALUES
  (1, 1, 1, 'PANT_BETALT', 5, 0, '2026-09-25 08:10:00', 'K-100001'),
  (1, 1, 1, 'RETUR_GODKENDT', 5, 50, '2026-09-25 17:20:00', NULL),
  (2, 1, 1, 'PANT_BETALT', 5, 0, '2026-09-26 08:05:00', 'K-100002'),
  (2, 1, 2, 'RETUR_GODKENDT', 5, 50, '2026-09-26 10:02:00', 'Returneret i anden butik'),
  (3, 2, 2, 'PANT_BETALT', 5, 0, '2026-09-26 12:30:00', 'K-100003'),
  (4, NULL, 3, 'PANT_BETALT', 5, 0, '2026-09-27 06:40:00', 'K-100004 – kunde uden app'),
  (5, 1, 1, 'PANT_BETALT', 5, 0, '2026-09-28 09:15:00', 'K-100005'),
  (6, 3, 4, 'PANT_BETALT', 5, 0, '2026-09-28 14:00:00', 'K-100006'),
  (6, 3, 4, 'RETUR_GODKENDT', 5, 50, '2026-09-28 14:35:00', NULL),
  (NULL, 3, 4, 'POINT_INDLØST', 0, -50, '2026-09-29 08:00:00', 'Brugt på Cafe Latte');
