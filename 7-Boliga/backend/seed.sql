-- Fiktive testdata (simuleret Boliga.dk-, DinGeo- og Tvangsauktioner-data)
INSERT INTO property (address, postcode, city, property_type, size_m2, rooms, built_year, energy_label, list_price, listed_date, ai_valuation, sales_channel) VALUES
  ('Solsikkevej 12', '2650', 'Hvidovre', 'Villa', 142, 5, 1962, 'D', 5495000, '2026-05-02', 5210000, 'Mægler'),
  ('Strandlodsvej 44, 3. tv', '2300', 'København S', 'Ejerlejlighed', 78, 3, 2008, 'B', 3995000, '2026-08-20', 4050000, 'Mægler'),
  ('Kildebakken 7', '2860', 'Søborg', 'Rækkehus', 115, 4, 1978, 'C', 4295000, '2026-03-11', 4020000, 'Selvsalg'),
  ('Åboulevarden 88, 2. th', '1960', 'Frederiksberg C', 'Ejerlejlighed', 96, 3, 1905, 'D', 5750000, '2026-09-05', 5690000, 'Mægler'),
  ('Engtoften 3', '2650', 'Hvidovre', 'Villa', 168, 6, 1998, 'C', 6250000, '2026-07-01', 6300000, 'Mægler'),
  ('Kalvebod Brygge 30, 5. mf', '1560', 'København V', 'Ejerlejlighed', 110, 4, 2016, 'A2015', 7495000, '2026-04-18', 6980000, 'Mægler');

INSERT INTO price_change (property_id, changed_date, old_price, new_price) VALUES
  (1, '2026-07-01', 5895000, 5695000),
  (1, '2026-08-25', 5695000, 5495000),
  (3, '2026-06-15', 4495000, 4295000),
  (6, '2026-07-20', 7995000, 7495000);

INSERT INTO geo_data (property_id, flood_risk, cloudburst_risk, radon_risk, noise_db, school_m, station_m, grocery_m, green_area_m, burglary_index, broadband_mbit) VALUES
  (1, 'middel', 'høj', 'lav', 52, 450, 1200, 300, 250, 115, 1000),
  (2, 'høj', 'middel', 'lav', 58, 700, 350, 150, 100, 90, 1000),
  (3, 'lav', 'lav', 'middel', 48, 300, 900, 500, 150, 80, 500),
  (4, 'lav', 'middel', 'lav', 64, 250, 400, 80, 300, 105, 1000),
  (5, 'lav', 'middel', 'lav', 45, 800, 1500, 600, 200, 110, 1000),
  (6, 'høj', 'høj', 'lav', 61, 1100, 500, 200, 400, 95, 1000);

INSERT INTO area_sale (postcode, address, sold_date, price, size_m2, days_on_market) VALUES
  ('2650', 'Rosenvænget 4', '2026-06-10', 5100000, 140, 65),
  ('2650', 'Birkeholmvej 19', '2026-07-22', 5850000, 155, 48),
  ('2650', 'Hvidovrevej 201', '2026-08-30', 4400000, 120, 110),
  ('2300', 'Artillerivej 60, 2. th', '2026-07-01', 3700000, 72, 35),
  ('2300', 'Amagerbrogade 12, 4. tv', '2026-08-15', 4200000, 85, 28),
  ('2860', 'Søborg Hovedgade 150', '2026-05-20', 3900000, 110, 90),
  ('2860', 'Vandtårnsvej 33', '2026-08-02', 4350000, 120, 60),
  ('1960', 'H.C. Ørsteds Vej 20, 1. tv', '2026-08-01', 5400000, 90, 21),
  ('1960', 'Rosenørns Allé 9, 3. th', '2026-09-01', 6100000, 100, 30),
  ('1560', 'Kalvebod Brygge 40, 3. th', '2026-06-01', 6800000, 105, 75),
  ('1560', 'Havnegade 2, 4. mf', '2026-08-10', 7100000, 112, 50);

INSERT INTO auction (postcode, address, auction_date, min_bid) VALUES
  ('2650', 'Hvidovrevej 88', '2026-10-20', 3100000),
  ('2860', 'Gladsaxevej 12', '2026-11-04', 2600000);

INSERT INTO user (name, email) VALUES
  ('Familien Hansen', 'hansen@test.dk'),
  ('Mads Køber', 'mads@test.dk');

INSERT INTO saved_property (user_id, property_id, note, saved_at) VALUES
  (1, 1, 'God have – men prisen?', '2026-09-20 20:14:00'),
  (1, 5, NULL, '2026-09-21 19:02:00');
