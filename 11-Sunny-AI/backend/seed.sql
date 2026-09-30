-- Fiktive eksempeldata fra kravspecifikationens punkt 9 (testuge 5.–9. oktober 2026).
-- Ingen rigtige opskrifter, kunder eller persondata. Mængder i tusindedele: 20 stk = 20000.

INSERT INTO bruger (navn, rolle) VALUES
  ('Bettina', 'Planlægger'),
  ('Niklas', 'Lageransvarlig'),
  ('Kontormedarbejder', 'Opslag');

INSERT INTO indstilling (noegle, vaerdi) VALUES ('beregningstidspunkt', '2026-10-05 09:00');

INSERT INTO snapshot (id, source, source_updated_at, imported_at, schema_version, beskrivelse) VALUES
  (1, 'demo', '2026-10-05 08:00', '2026-10-05 08:00', '1.0', 'Startdata fra den simulerede Uniconta-adapter');

INSERT INTO vare (id, varenummer, navn, type, basisenhed) VALUES
  (1, 'P1', 'Æblejuice 1 L', 'færdigvare', 'stk'),
  (2, 'P2', 'Gløgg 0,75 L', 'færdigvare', 'stk'),
  (3, 'P3', 'Ingefærshot 0,1 L', 'færdigvare', 'stk'),
  (4, 'R1', 'Æblemost', 'råvare', 'L'),
  (5, 'R2', 'Gløggbase', 'råvare', 'kg'),
  (6, 'R3', 'Ingefær', 'råvare', 'kg');

INSERT INTO produktionsrate (vare_id, enheder_pr_time) VALUES (1, 20), (2, 20), (3, 60);

-- Alle batches er frigivne, validerede og uden reservationer. R3 er ekstra demodata til udløbsadvarslen (F05).
INSERT INTO lagerbatch (snapshot_id, vare_id, batchnummer, fysisk_maengde, reserveret_maengde, udloebsdato) VALUES
  (1, 1, 'B-P1-001', 20000, 0, '2026-10-31'),
  (1, 4, 'B-R1-001', 60000, 0, '2026-10-31'),
  (1, 5, 'B-R2-001', 500000, 0, '2026-10-31'),
  (1, 6, 'B-R3-001', 15000, 0, '2026-10-09');

INSERT INTO ordrelinje (id, snapshot_id, ordre_id, kilde_id, vare_id, bestilt_maengde, leveringsdato, status, prioritet, saesonmaerke) VALUES
  (1, 1, 'O1', 'UC-ORD-1001', 1, 100000, '2026-10-05', 'åben', 'normal', 0),
  (2, 1, 'O2', 'UC-ORD-1002', 1, 60000, '2026-10-06', 'åben', 'normal', 0),
  (3, 1, 'O3', 'UC-ORD-1003', 2, 200000, '2026-10-07', 'åben', 'normal', 1),
  (4, 1, 'O4', 'UC-ORD-1004', 3, 50000, '2026-10-08', 'annulleret', 'normal', 0);

-- P1: 0,5 L R1 pr. stk · P2: 1 kg R2 pr. stk · P3: 0,05 kg R3 pr. stk
INSERT INTO ressourcebehov (ordrelinje_id, raavare_id, maengde_pr_enhed) VALUES
  (1, 4, 500), (2, 4, 500), (3, 5, 1000), (4, 6, 50);

INSERT INTO kapacitetsdag (dato, disponible_minutter) VALUES
  ('2026-10-05', 480), ('2026-10-06', 480), ('2026-10-07', 480), ('2026-10-08', 480), ('2026-10-09', 480);

INSERT INTO haendelse (type, timestamp, actor, detaljer) VALUES
  ('Snapshot indlæst', '2026-10-05 08:00', 'System', 'Snapshot #1 fra simuleret Uniconta-adapter');
