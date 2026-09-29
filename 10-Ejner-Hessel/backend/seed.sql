-- Fiktive testdata – ingen rigtige kundeoplysninger
INSERT INTO customer (name, email, phone, address) VALUES
  ('Lars Testesen', 'lars@test.dk', '20 00 00 01', 'Testvej 1, 2600 Glostrup'),
  ('Mette Prøvesen', 'mette@test.dk', '20 00 00 02', 'Prøvegade 5, 4000 Roskilde');

INSERT INTO workshop (name, address, brands) VALUES
  ('Ejner Hessel Glostrup', 'Hovedvejen 90, 2600 Glostrup', 'Mercedes-Benz,Renault,Dacia'),
  ('Ejner Hessel Roskilde', 'Københavnsvej 50, 4000 Roskilde', 'Renault,Dacia,Ford'),
  ('Ejner Hessel Ringsted', 'Nørretorv 10, 4100 Ringsted', 'Mercedes-Benz,Ford');

INSERT INTO car (customer_id, brand, model, registration, vin, year, fuel, mileage_km, ownership, next_service_date) VALUES
  (1, 'Mercedes-Benz', 'EQA 250+', 'EH 12 345', 'W1N2437011J000001', 2023, 'El', 32000, 'Leaset', '2026-11-15'),
  (1, 'Dacia', 'Jogger', 'EH 55 102', 'UU1RJF00000000002', 2022, 'Benzin', 48500, 'Købt', '2026-10-10'),
  (2, 'Ford', 'Kuga PHEV', 'EH 77 881', 'WF0FXXWPMF0000003', 2021, 'Plug-in hybrid', 71200, 'Købt', '2027-01-20'),
  (2, 'Renault', 'Clio E-Tech', 'EH 90 300', 'VF1RJA00000000004', 2024, 'Hybrid', 12300, 'Leaset', '2027-03-01');

INSERT INTO service_history (car_id, date, type, workshop_id, mileage_km, price, description) VALUES
  (1, '2025-11-20', 'Årligt eftersyn', 1, 18000, 2495, 'Softwareopdatering, kabinefilter skiftet'),
  (2, '2024-10-02', 'Serviceeftersyn', 1, 21000, 2195, 'Olie og filter skiftet'),
  (2, '2025-10-08', 'Serviceeftersyn', 2, 35500, 2395, 'Olie, filter og bremsevæske'),
  (2, '2026-04-15', 'Hjulskift', 2, 42000, 350, 'Skift til sommerhjul'),
  (3, '2025-01-18', 'Serviceeftersyn', 2, 52000, 3295, 'Stort service, tændrør skiftet'),
  (3, '2026-01-22', 'Serviceeftersyn', 3, 64800, 2995, 'Olie og filter, bremseklodser foran');

INSERT INTO booking (car_id, workshop_id, date, time, service_type, notes, status) VALUES
  (2, 1, '2026-10-12', '08:00', 'Serviceeftersyn', 'Tjek venligst lyd fra forhjul', 'BEKRÆFTET'),
  (1, 1, '2026-11-16', '09:30', 'Årligt eftersyn', NULL, 'BEKRÆFTET'),
  (3, 2, '2026-09-24', '07:30', 'Fejlfinding', 'Motorlampe lyser', 'GENNEMFØRT');

INSERT INTO repair (car_id, description, status, estimated_ready, updated_at, message) VALUES
  (3, 'Motorlampe lyser – udskiftning af EGR-ventil', 'VENTER_PÅ_DELE', '2026-10-02', '2026-09-28 14:10:00', 'Reservedelen ankommer onsdag. Vi ringer, når bilen er klar.');

INSERT INTO document (customer_id, car_id, title, category, date, description) VALUES
  (1, 1, 'Leasingaftale EQA 250+', 'Aftale', '2023-05-01', '48 mdr., 15.000 km/år'),
  (1, 2, 'Købsaftale Dacia Jogger', 'Aftale', '2022-03-14', NULL),
  (1, 2, 'Faktura service okt. 2025', 'Faktura', '2025-10-08', '2.395 kr.'),
  (1, 1, 'Garantibevis batteri', 'Garanti', '2023-05-01', '8 år / 160.000 km'),
  (2, 3, 'Faktura service jan. 2026', 'Faktura', '2026-01-22', '2.995 kr.'),
  (2, 4, 'Leasingaftale Clio E-Tech', 'Aftale', '2024-02-01', '36 mdr.'),
  (2, NULL, 'Serviceaftale – Ejner Hessel Plus', 'Aftale', '2024-02-01', 'Fast pris på service');
