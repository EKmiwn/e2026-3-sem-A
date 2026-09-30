-- Fictional example data. Prices, ratings and reviews are prototype data and must be verified by Amitylux (K9).

INSERT INTO destination (name, country, description, high_season_months) VALUES
  ('Copenhagen', 'Denmark', 'Harbour city of design, food and royal history.', '6,7,8,12'),
  ('Rome', 'Italy', 'Ancient history, art and neighbourhood trattorias.', '4,5,6,7,9,10');

INSERT INTO product_type (code, name, short, group_form, flexibility, personalisation, booking_form, price_principle, best_for) VALUES
  ('public', 'Public small-group', 'Join a small group on a fixed tour.',
   'Shared with other travellers – max 12 guests', 'Fixed date, start time and route', 'Same content for everyone; the guide answers your questions',
   'Book a seat directly – confirmed when the seat is available', 'Fixed price per person', 'Solo travellers and couples who want a proven classic at a lower price'),
  ('private', 'Private', 'Your own guide, only your party.',
   'Only your own party', 'You choose date and start time; pace adapted on the day', 'Route and focus adapted to your interests within the tour',
   'Request – Amitylux confirms guide and time', 'Fixed price per group (up to the stated size)', 'Families, couples and friends who want their own pace'),
  ('customised', 'Customised', 'A programme designed with you.',
   'Your party – any size', 'Fully flexible – from half a day to several days', 'Designed from scratch with an Amitylux planner',
   'Structured request followed by a personal dialogue', 'Price on request after dialogue', 'Complex wishes: several services, special access, larger groups');

INSERT INTO value_claim (code, label, text, evidence) VALUES
  ('small_group', 'Small groups', 'Public tours have at most 12 guests; private tours are only your party.', 'Amitylux product rules – interview section 1 and 3'),
  ('local_guide', 'Local guides', 'Guides live in the city and are selected for their field of knowledge.', 'Interview section 4; company data – services'),
  ('personal', 'Personal attention', 'The guide adapts to questions, children and energy levels on the day.', 'Interview section 1 and 5; company data – customer satisfaction'),
  ('flexible', 'Flexibility', 'Private and customised: date, start time and pace are agreed with you.', 'Product definitions – interview section 3 and 6'),
  ('organised', 'One point of contact', 'One planner coordinates guides, tickets, transport and restaurants.', 'Interview section 3 and 8'),
  ('reviews', 'Guest reviews', 'Ratings shown next to each suggestion. In the prototype they are example data.', 'Company data – customer satisfaction (example data, must be verified)');

INSERT INTO experience (destination_id, type_code, title, description, location, experience_type, duration_hours, min_group, max_group, languages, interests, pace, practical, transport_modes, mobility_note, included, not_included, price_from, price_unit, value_points, local_alternative, local_note, rating, review_count, review_quote, review_source, needs_confirmation, catalogue_status, approved_by, approved_at) VALUES
  -- Copenhagen
  (1, 'public', 'Copenhagen Old Town Walk', 'The classic route through Nyhavn, Amalienborg and the medieval centre.', 'Nyhavn – Amalienborg – City centre', 'Walking tour', 2.5, 1, 12,
   'English,Danish,German', 'history,architecture', 'moderate', 'short_walks', 'walk', 'On foot, about 3 km with regular stops.',
   'Licensed local guide; route map', 'Entrance fees; food and drinks', 45, 'person', 'small_group;local_guide;reviews', 0, NULL,
   4.8, 312, 'Mette made 900 years of history feel alive.', 'Example data – fictional review', 'Seats on your date', 'approved', 'Amitylux product team (example)', '2026-09-15'),
  (1, 'public', 'Nordic Food Walk in Vesterbro', 'Tastings at five family-run producers in the old Meatpacking District.', 'Vesterbro – Kødbyen', 'Food tasting walk', 3, 1, 10,
   'English,Danish', 'food,local life', 'relaxed', 'kid_friendly,indoor_option,short_walks', 'walk,public_transport', 'On foot between producers, about 2 km. S-train to Dybbølsbro.',
   'Guide; five tastings; water', 'Extra drinks', 89, 'person', 'small_group;local_guide;reviews', 1, 'Vesterbro food producers outside the Nyhavn–Strøget core, where most sightseeing takes place.',
   4.9, 188, 'Best food tour we have ever taken.', 'Example data – fictional review', 'Seats on your date;Dietary adaptations', 'approved', 'Amitylux product team (example)', '2026-09-15'),
  (1, 'public', 'Design & Architecture Walk', 'From Danish Modern to the new harbour front – the stories behind the buildings.', 'Christiansborg – Royal Library – Islands Brygge', 'Walking tour', 2, 1, 12,
   'English', 'design,architecture', 'moderate', 'step_free,short_walks', 'walk,public_transport', 'Step-free route on foot, about 2.5 km. Metro at both ends.',
   'Guide; design map', 'Entrance fees', 55, 'person', 'small_group;local_guide;reviews', 0, NULL,
   4.7, 96, 'Changed how we looked at the whole city.', 'Example data – fictional review', 'Seats on your date', 'approved', 'Amitylux product team (example)', '2026-09-15'),
  (1, 'private', 'Private Royal Copenhagen', 'Palaces, the crown jewels and royal stories with your own guide – at your pace.', 'Rosenborg – Amalienborg', 'Private guided visit', 4, 1, 6,
   'English,Danish,German,Spanish,French', 'history,art', 'relaxed', 'kid_friendly,indoor_option', 'walk,public_transport', 'On foot between the palaces, about 1.5 km. Metro to Nørreport.',
   'Private guide; Rosenborg tickets', 'Meals; hotel pick-up', 480, 'group', 'local_guide;personal;flexible;reviews', 0, NULL,
   4.9, 96, 'Felt like visiting with a friend who knows everything.', 'Example data – fictional review', 'Guide in your language on your date;Rosenborg entry time', 'approved', 'Amitylux product team (example)', '2026-09-15'),
  (1, 'private', 'Harbour & Design by Bike', 'Cycle the new harbour districts, bridges and design icons with a local architect.', 'Nordhavn – Refshaleøen', 'Bike tour', 3, 1, 8,
   'English,Danish', 'design,architecture,nature', 'active', 'kid_friendly', 'bike', 'By bike on cycle lanes, about 12 km. Bikes and helmets provided.',
   'Private guide; bikes and helmets', 'Food', 360, 'group', 'local_guide;personal;flexible', 1, 'Nordhavn and Refshaleøen – newer harbour districts most visitors never reach.',
   4.7, 54, 'Perfect for our family – the kids loved it.', 'Example data – fictional review', 'Bike sizes for children;Weather', 'approved', 'Amitylux product team (example)', '2026-09-15'),
  (1, 'private', 'Nørrebro Local Life & Street Food', 'Street art, Superkilen and weekend food spots where locals actually go.', 'Nørrebro – Jægersborggade', 'Neighbourhood walk', 3, 1, 8,
   'English,Danish,Spanish', 'local life,food,art', 'relaxed', 'kid_friendly,short_walks', 'walk,public_transport', 'On foot, about 2 km. Metro to Nørrebros Runddel.',
   'Private guide; three tastings', 'Extra food and drinks', 320, 'group', 'local_guide;personal;flexible', 1, 'A residential neighbourhood with its own food and street culture, away from the classic sights.',
   4.8, 41, 'We saw a side of Copenhagen we would never have found.', 'Example data – fictional review', 'Guide in your language on your date', 'approved', 'Amitylux product team (example)', '2026-09-15'),
  (1, 'private', 'Canal Stories by Private Boat', 'Christianshavn and the old naval harbour from the water, with a guide on board.', 'Christianshavn – Holmen', 'Boat trip', 2, 1, 10,
   'English,Danish,German', 'history,nature,local life', 'relaxed', 'kid_friendly,short_walks', 'boat', 'By private boat from Christianshavn. Boarding requires a step down.',
   'Private boat and skipper; guide; blankets', 'Food and drinks', 650, 'group', 'local_guide;personal;flexible', 0, NULL,
   4.9, 37, 'The harbour at sunset with our own guide – unforgettable.', 'Example data – fictional review', 'Boat and skipper availability;Weather', 'approved', 'Amitylux product team (example)', '2026-09-15'),
  (1, 'customised', 'Tailor-made Copenhagen Day', 'A day designed around your party – culture, food, boats and special access combined.', 'Anywhere in Greater Copenhagen', 'Customised programme', 8, 1, 40,
   'English,Danish,German,Spanish,French,Italian', 'history,art,food,architecture,design,nature,local life', 'moderate', 'step_free,kid_friendly,short_walks,indoor_option', 'walk,bike,public_transport,car,boat', 'Chosen with you: on foot, bike, metro, private car or boat.',
   'Personal planner; matched guide; coordinated services', 'Flights and hotels; items not in the final proposal', NULL, 'request', 'local_guide;personal;flexible;organised;reviews', 0, NULL,
   5.0, 21, 'They thought of everything.', 'Example data – fictional review', 'Final price;Guide match;Special access;Restaurant tables', 'approved', 'Amitylux product team (example)', '2026-09-15'),
  (1, 'customised', 'Royal Palace After Hours', 'Private evening access to a royal palace. NOT approved – must never be suggested.', 'Amalienborg', 'Special access', 3, 1, 20,
   'English', 'history,art', 'relaxed', 'indoor_option', 'walk', NULL,
   'Guide; access', 'Everything else', NULL, 'request', 'organised', 0, NULL,
   NULL, 0, NULL, NULL, 'Special access', 'draft', NULL, NULL),
  -- Rome (K11: same structure, different local content)
  (2, 'public', 'Colosseum & Forum Small Group', 'The classic tour of ancient Rome with timed entry.', 'Colosseum – Roman Forum', 'Walking tour', 3, 1, 12,
   'English,Italian,Spanish', 'history,architecture', 'moderate', '', 'walk,public_transport', 'On foot on uneven ancient paving, about 3 km. Metro B to Colosseo.',
   'Licensed guide; entry tickets', 'Food; transport', 69, 'person', 'small_group;local_guide;reviews', 0, NULL,
   4.8, 540, 'Giulia answered every question.', 'Example data – fictional review', 'Seats on your date;Entry time slot', 'approved', 'Amitylux product team (example)', '2026-09-15'),
  (2, 'public', 'Testaccio Market & Local Kitchens', 'A morning in the market hall and the family trattorias of Testaccio.', 'Testaccio', 'Food tasting walk', 3, 1, 10,
   'English,Italian', 'food,local life', 'relaxed', 'step_free,kid_friendly,short_walks', 'walk,public_transport', 'Step-free on foot, about 1.5 km. Metro B to Piramide.',
   'Guide; six tastings', 'Extra drinks', 65, 'person', 'small_group;local_guide;reviews', 1, 'A working-class food quarter south of the centre where Romans shop and eat.',
   4.9, 211, 'We ate like locals for a morning.', 'Example data – fictional review', 'Seats on your date;Dietary adaptations', 'approved', 'Amitylux product team (example)', '2026-09-15'),
  (2, 'public', 'Trastevere Evening Food Tour', 'Supplì, pizza and gelato in one of Rome''s most atmospheric quarters.', 'Trastevere', 'Food tasting walk', 3.5, 1, 12,
   'English', 'food,local life', 'relaxed', 'short_walks', 'walk', 'On foot on cobblestones, about 2 km.',
   'Guide; dinner-sized tastings; wine', 'Extra drinks', 79, 'person', 'small_group;local_guide;reviews', 0, NULL,
   4.9, 402, 'We did not need dinner afterwards!', 'Example data – fictional review', 'Seats on your date', 'approved', 'Amitylux product team (example)', '2026-09-15'),
  (2, 'private', 'Private Vatican Early Entry', 'The Vatican Museums before general opening, with your own art historian.', 'Vatican Museums', 'Private guided visit', 3.5, 1, 8,
   'English,Italian,German,French,Spanish', 'art,history', 'moderate', 'step_free,indoor_option', 'walk,car', 'Mostly indoors and step-free with lifts. Private car to the entrance can be added.',
   'Private guide; early entry tickets', 'Hotel transfer', 620, 'group', 'local_guide;personal;flexible;reviews', 0, NULL,
   4.9, 133, 'The Sistine Chapel almost to ourselves.', 'Example data – fictional review', 'Early entry slot;Guide in your language on your date', 'approved', 'Amitylux product team (example)', '2026-09-15'),
  (2, 'private', 'Appian Way by E-bike', 'The ancient road, aqueducts and catacombs south of the centre.', 'Via Appia Antica', 'Bike tour', 4, 1, 8,
   'English,Italian', 'history,nature', 'active', '', 'bike', 'By e-bike, about 18 km partly on original Roman paving.',
   'Private guide; e-bikes and helmets', 'Catacomb ticket', 390, 'group', 'local_guide;personal;flexible', 1, 'Countryside inside the city, away from the crowded historic centre.',
   4.8, 77, 'A side of Rome we never knew.', 'Example data – fictional review', 'Catacomb entry time;Weather', 'approved', 'Amitylux product team (example)', '2026-09-15'),
  (2, 'customised', 'Tailor-made Roman Days', 'One or more days with private guides, a cooking class, transport and special access.', 'Rome and surroundings', 'Customised programme', 16, 1, 40,
   'English,Italian,German,Spanish,French,Danish', 'history,art,food,architecture,design,nature,local life', 'moderate', 'step_free,kid_friendly,short_walks,indoor_option', 'walk,bike,public_transport,car', 'Chosen with you: on foot, e-bike, metro or private car.',
   'Personal planner; matched guides; coordinated services', 'Flights and hotels; items not in the final proposal', NULL, 'request', 'local_guide;personal;flexible;organised;reviews', 0, NULL,
   4.9, 17, 'Our best family holiday ever.', 'Example data – fictional review', 'Final price;Guide match;Special access;Restaurant tables', 'approved', 'Amitylux product team (example)', '2026-09-15');

INSERT INTO addon (code, name, description, price_hint) VALUES
  ('guide_language', 'Guide in your language', 'A guide who speaks your preferred language', 'Included for private – requires confirmation'),
  ('museum', 'Museum or cultural visit', 'Tickets and guiding at a museum or site', 'Price principle: entry fee + guide time'),
  ('food', 'Food experience', 'Tasting, cooking class or restaurant booking', 'Price principle: per person'),
  ('transport', 'Private transport', 'Car or minivan with driver', 'Price principle: per half day'),
  ('boat', 'Boat trip', 'Private boat on the harbour or river', 'Price principle: per boat'),
  ('activity', 'Other activity', 'Bike, kayak, workshop or similar', 'Price on request');

INSERT INTO inquiry (reference, created_at, status, wanted_type, contact_name, contact_email, destination_id, travel_date, group_type, group_size, interests, pace, language, practical, experience_ids, addons, customer_unsure, notes) VALUES
  ('AMX-1001', '2026-09-24 10:12:00', 'IN_PROGRESS', 'customised', 'Laura Schmidt', 'laura@example.com', 1, '2026-10-14', 'family', 5, 'history,food', 'relaxed', 'German', 'kid_friendly', '4,2', 'food,boat', 'Whether a boat trip works with a 7-year-old', 'Two children aged 7 and 10.'),
  ('AMX-1002', '2026-09-28 18:40:00', 'NEW', 'private', 'James Carter', 'james@example.com', 2, '2026-11-03', 'couple', 2, 'art,history', 'moderate', 'English', 'step_free', '13', '', NULL, 'Anniversary trip.');
