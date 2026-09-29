-- Fiktive testdata
INSERT INTO green_coffee (name, origin, supplier, cost_per_kg, min_sacks) VALUES
  ('Yirgacheffe', 'Etiopien', 'Nordic Approach', 72.5, 2),
  ('Santos', 'Brasilien', 'Nordic Approach', 48.0, 2),
  ('Huila', 'Colombia', 'Kaffe Import ApS', 61.0, 1),
  ('Sidamo', 'Etiopien', 'Kaffe Import ApS', 69.0, 1);

INSERT INTO sack (green_coffee_id, lot_number, received_date, initial_kg, remaining_kg, status) VALUES
  (1, 'ET-26-03', '2026-08-28', 80, 5,  'REST'),
  (1, 'ET-26-04', '2026-09-10', 80, 80, 'PAA_LAGER'),
  (2, 'BR-26-07', '2026-09-01', 80, 30, 'I_BRUG'),
  (2, 'BR-26-08', '2026-09-15', 80, 80, 'PAA_LAGER'),
  (3, 'CO-26-02', '2026-09-05', 80, 55, 'I_BRUG'),
  (4, 'SI-26-01', '2026-09-20', 80, 80, 'PAA_LAGER');

INSERT INTO product (sku, name, bag_size_g, green_coffee_id, stock_bags, min_bags, price) VALUES
  ('FV-0210', 'Filter Helsingør', 250, 1, 88, 40, 95),
  ('ES-0110', 'Espresso Strandvejen', 250, 2, 120, 50, 89),
  ('FV-0320', 'Filter Huila', 250, 3, 18, 30, 99),
  ('ES-1000', 'Espresso Strandvejen 1 kg', 1000, 2, 12, 10, 329),
  ('BL-0500', 'Husets blanding', 500, NULL, 25, 15, 169);

INSERT INTO roast (sack_id, product_id, kg_used, bags_produced, performed_by, roasted_at) VALUES
  (1, 1, 25, 84, 'Anders', '2026-09-02 08:10:00'),
  (1, 1, 25, 83, 'Anders', '2026-09-09 08:05:00'),
  (1, 1, 25, 84, 'Mette',  '2026-09-16 08:20:00'),
  (3, 2, 25, 84, 'Mette',  '2026-09-12 09:00:00'),
  (3, 2, 25, 85, 'Anders', '2026-09-22 08:30:00'),
  (5, 3, 25, 84, 'Anders', '2026-09-18 10:00:00');

INSERT INTO sale (product_id, bags, channel, sold_at) VALUES
  (1, 60, 'WEBSHOP', '2026-09-10 12:00:00'),
  (1, 100, 'BUTIK',  '2026-09-20 16:00:00'),
  (2, 49, 'CAFE',    '2026-09-21 15:00:00'),
  (3, 66, 'BUTIK',   '2026-09-25 14:00:00'),
  (1, 83, 'WEBSHOP', '2026-09-27 11:00:00'),
  (5, 10, 'BUTIK',   '2026-09-27 13:30:00');

INSERT INTO movement (occurred_at, movement_type, entity_type, entity_id, quantity, unit, note) VALUES
  ('2026-09-16 08:20:00', 'RISTNING', 'sack', 1, -25, 'kg', 'Sæk ET-26-03 → Filter Helsingør'),
  ('2026-09-16 08:20:00', 'RISTNING', 'product', 1, 84, 'poser', 'Ristning fra ET-26-03'),
  ('2026-09-20 09:00:00', 'MODTAGET', 'sack', 6, 80, 'kg', 'Sæk SI-26-01 modtaget'),
  ('2026-09-22 08:30:00', 'RISTNING', 'sack', 3, -25, 'kg', 'Sæk BR-26-07 → Espresso Strandvejen'),
  ('2026-09-22 08:30:00', 'RISTNING', 'product', 2, 85, 'poser', 'Ristning fra BR-26-07'),
  ('2026-09-27 11:00:00', 'SALG', 'product', 1, -83, 'poser', 'Salg via WEBSHOP');
