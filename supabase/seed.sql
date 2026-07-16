-- =============================================================================
-- gjejecmimin — seed / mock data
-- =============================================================================
-- Realistic MOCK data for local development and UI work. Prices are in EUR
-- (Kosovo's currency; Albanian stores are shown in EUR too for comparability).
--
-- IMPORTANT: this is fake data. It lands in exactly the same tables a real
-- scraping/ingestion pipeline will write to, so nothing downstream assumes the
-- data is mock. Re-running `supabase db reset` re-applies migrations + this seed.
--
-- Coverage goal: ~28 products across groceries / electronics / car-parts, each
-- with 2-4 price_observations from different stores, deliberately mixing all
-- three trust tiers (official / verified_retailer / crowdsourced) so every badge
-- state is visible in the UI.
-- =============================================================================

-- Deterministic-ish reset so the seed is idempotent across `db reset` runs.
truncate table
  price_observations,
  user_submissions,
  user_reputation,
  official_indices,
  canonical_products,
  stores
restart identity cascade;

-- ---------------------------------------------------------------------------
-- Stores
-- ---------------------------------------------------------------------------
-- `verified = true` stores feed the 'verified_retailer' tier. AutoStar Kosova
-- and the two Albanian shops are left unverified on purpose — their prices come
-- in as 'crowdsourced' below, which is what an unverified source should produce.
insert into stores (name, arbk_registration_id, category, city, verified) values
  ('Viva Fresh Store',    '810123456', 'supermarket', 'Prishtinë',  true),
  ('ETC Supermarket',     '810234567', 'supermarket', 'Prishtinë',  true),
  ('Interex',             '810345678', 'supermarket', 'Prizren',    true),
  ('Meridian Express',    '810456789', 'supermarket', 'Ferizaj',    true),
  ('Gjirafa50',           '810567890', 'electronics', 'Prishtinë',  true),
  ('Neptun',              '810678901', 'electronics', 'Prishtinë',  true),
  ('Foleja Elektronike',  '811111222', 'electronics', 'Pejë',       true),
  ('AutoPjesë Blloku',    '811222333', 'car_parts',   'Prishtinë',  true),
  ('AutoStar Kosova',     null,        'car_parts',   'Mitrovicë',  false),
  ('Conad Tirana',        null,        'supermarket', 'Tiranë',     true),
  ('NeoTek',              null,        'electronics', 'Tiranë',     false),
  ('Tregu i Gjelbër',     null,        'market',      'Prishtinë',  false);

-- ---------------------------------------------------------------------------
-- Canonical products (28)
-- ---------------------------------------------------------------------------
insert into canonical_products (name, canonical_name, category, brand, unit) values
  -- groceries (12)
  ('Coca-Cola 1.5L',              'coca-cola-1.5l',        'groceries',   'Coca-Cola', '1.5L'),
  ('Whole Milk (Qumësht) 1L',     'milk-vita-1l',          'groceries',   'Vita',      '1L'),
  ('Sunflower Oil (Vaj) 1L',      'sunflower-oil-1l',      'groceries',   'Vegetalé',  '1L'),
  ('White Sugar (Sheqer) 1kg',    'sugar-1kg',             'groceries',   'Agrokosova','1kg'),
  ('White Bread (Bukë) 500g',     'bread-500g',            'groceries',   'Furra',     '500g'),
  ('Eggs (Vezë) 10pcs',           'eggs-10',               'groceries',   'Ferma',     '10pcs'),
  ('Nescafé Gold 200g',           'nescafe-gold-200g',     'groceries',   'Nescafé',   '200g'),
  ('Barilla Spaghetti 500g',      'spaghetti-barilla-500g','groceries',   'Barilla',   '500g'),
  ('Basmati Rice (Oriz) 1kg',     'rice-1kg',              'groceries',   'Riso',      '1kg'),
  ('Butter (Gjalpë) 250g',        'butter-250g',           'groceries',   'President', '250g'),
  ('Ground Coffee (Kafe) 200g',   'coffee-ground-200g',    'groceries',   'Solis',     '200g'),
  ('Mineral Water (Ujë) 1.5L',    'water-1.5l',            'groceries',   'Rugove',    '1.5L'),
  -- electronics (9)
  ('Apple iPhone 15 128GB',       'iphone-15-128gb',       'electronics', 'Apple',     '128GB'),
  ('Samsung Galaxy A55 256GB',    'samsung-galaxy-a55',    'electronics', 'Samsung',   '256GB'),
  ('Sony WH-1000XM5 Headphones',  'sony-wh1000xm5',        'electronics', 'Sony',      'each'),
  ('LG 55" 4K UHD Smart TV',      'lg-55-4k-tv',           'electronics', 'LG',        '55"'),
  ('Xiaomi Redmi Note 13 128GB',  'redmi-note-13',         'electronics', 'Xiaomi',    '128GB'),
  ('Logitech MX Master 3S',       'logitech-mx-master-3s', 'electronics', 'Logitech',  'each'),
  ('Dell XPS 13 Laptop',          'dell-xps-13',           'electronics', 'Dell',      'each'),
  ('PlayStation 5 Slim',          'ps5-slim',              'electronics', 'Sony',      'each'),
  ('Anker PowerCore 20000mAh',    'anker-powerbank-20000', 'electronics', 'Anker',     'each'),
  -- car parts (7)
  ('Bosch Wiper Blades 24"',      'bosch-wiper-24',        'car_parts',   'Bosch',     'pair'),
  ('Castrol EDGE 5W-30 4L',       'castrol-5w30-4l',       'car_parts',   'Castrol',   '4L'),
  ('Brake Pads Front (VW Golf)',  'brake-pads-golf-front', 'car_parts',   'ATE',       'set'),
  ('NGK Spark Plugs (set of 4)',  'ngk-spark-plugs-4',     'car_parts',   'NGK',       'set'),
  ('Michelin Tyre 205/55 R16',    'michelin-205-55-r16',   'car_parts',   'Michelin',  'each'),
  ('Bosch Car Battery 12V 70Ah',  'bosch-battery-70ah',    'car_parts',   'Bosch',     'each'),
  ('Air Filter (VW Golf 7)',      'air-filter-golf7',      'car_parts',   'Mann',      'each');

-- ---------------------------------------------------------------------------
-- Official statistical indices
-- ---------------------------------------------------------------------------
insert into official_indices (source, category, period, value, unit) values
  ('ASK',    'groceries', '2026-06',  108.400, 'index'),
  ('ASK',    'food',      '2026-Q2',  107.900, 'index'),
  ('INSTAT', 'food',      '2026-06',  112.300, 'index'),
  ('BQK',    'cpi',       '2026-06',    2.400, '%');

-- ---------------------------------------------------------------------------
-- Price observations
-- ---------------------------------------------------------------------------
-- Rows are given as a VALUES list keyed by product canonical_name and store
-- name, then joined to resolve FKs. Official-tier rows have a NULL store
-- (store_name = NULL) — they represent an authoritative reference price rather
-- than a specific shop's shelf price.
insert into price_observations
  (product_id, store_id, price, currency, observed_at, trust_tier,
   source_id, geo_city, geo_region, raw_source_text, confidence_score)
select
  p.id,
  s.id,
  v.price,
  'EUR',
  now() - (v.days_ago || ' days')::interval,
  v.trust_tier::trust_tier,
  v.source_id,
  v.geo_city,
  v.geo_region,
  v.raw_source_text,
  v.confidence_score
from (values
  -- canonical_name, store_name, price, days_ago, trust_tier, source_id, geo_city, geo_region, raw_source_text, confidence
  -- ---- groceries ----
  ('coca-cola-1.5l',        'Viva Fresh Store',   1.19, 2, 'verified_retailer', 'scrape:vivafresh:8841', 'Prishtinë', 'Kosovë',    'Coca-Cola PET 1.5L',                0.96),
  ('coca-cola-1.5l',        'ETC Supermarket',    1.25, 4, 'verified_retailer', 'scrape:etc:1122',       'Prishtinë', 'Kosovë',    'CocaCola 1,5 L',                    0.95),
  ('coca-cola-1.5l',        'Tregu i Gjelbër',    1.10, 1, 'crowdsourced',      'sub:usr_1042',          'Prishtinë', 'Kosovë',    'coca cola 1.5l te tregu',           0.55),
  ('coca-cola-1.5l',        'Conad Tirana',       1.30, 6, 'crowdsourced',      'sub:usr_1088',          'Tiranë',    'Shqipëri',  'Coca Cola 1.5L Conad',              0.60),

  ('milk-vita-1l',          null,                 1.05,10, 'official',          'ASK:CPI-milk-2026-06',  'Kosovë',    'Kosovë',    'ASK avg retail price, milk 1L, Jun 2026', 1.00),
  ('milk-vita-1l',          'Viva Fresh Store',   1.09, 3, 'verified_retailer', 'scrape:vivafresh:2210', 'Prishtinë', 'Kosovë',    'Qumësht Vita 3.2% 1L',              0.94),
  ('milk-vita-1l',          'Interex',            1.15, 5, 'verified_retailer', 'scrape:interex:77',     'Prizren',   'Kosovë',    'Vita milk 1L',                      0.90),
  ('milk-vita-1l',          'Tregu i Gjelbër',    1.00, 2, 'crowdsourced',      'sub:usr_2201',          'Prishtinë', 'Kosovë',    'qumesht vita 1L',                   0.50),

  ('sunflower-oil-1l',      null,                 1.79,12, 'official',          'ASK:CPI-oil-2026-06',   'Kosovë',    'Kosovë',    'ASK avg price, sunflower oil 1L',   1.00),
  ('sunflower-oil-1l',      'ETC Supermarket',    1.85, 4, 'verified_retailer', 'scrape:etc:oil',        'Prishtinë', 'Kosovë',    'Vaj luledielli 1L',                 0.92),
  ('sunflower-oil-1l',      'Meridian Express',   1.75, 6, 'verified_retailer', 'scrape:meridian:oil',   'Ferizaj',   'Kosovë',    'Vaj 1L',                            0.90),

  ('sugar-1kg',             null,                 0.95,12, 'official',          'ASK:CPI-sugar-2026-06', 'Kosovë',    'Kosovë',    'ASK avg price, white sugar 1kg',    1.00),
  ('sugar-1kg',             'Viva Fresh Store',   0.99, 3, 'verified_retailer', 'scrape:vivafresh:sugar','Prishtinë', 'Kosovë',    'Sheqer i bardhë 1kg',               0.93),
  ('sugar-1kg',             'Tregu i Gjelbër',    0.90, 1, 'crowdsourced',      'sub:usr_3110',          'Prishtinë', 'Kosovë',    'sheqer 1kg',                        0.50),

  ('bread-500g',            null,                 0.55,11, 'official',          'ASK:CPI-bread-2026-06', 'Kosovë',    'Kosovë',    'ASK avg price, white bread 500g',   1.00),
  ('bread-500g',            'ETC Supermarket',    0.60, 2, 'verified_retailer', 'scrape:etc:bread',      'Prishtinë', 'Kosovë',    'Bukë e bardhë 500g',                0.90),
  ('bread-500g',            'Interex',            0.58, 5, 'verified_retailer', 'scrape:interex:bread',  'Prizren',   'Kosovë',    'buke 500g',                         0.88),

  ('eggs-10',               'Viva Fresh Store',   1.99, 3, 'verified_retailer', 'scrape:vivafresh:eggs', 'Prishtinë', 'Kosovë',    'Vezë 10 copë',                      0.92),
  ('eggs-10',               'Meridian Express',   2.10, 4, 'verified_retailer', 'scrape:meridian:eggs',  'Ferizaj',   'Kosovë',    'veze 10',                           0.90),
  ('eggs-10',               'Tregu i Gjelbër',    1.80, 1, 'crowdsourced',      'sub:usr_4021',          'Prishtinë', 'Kosovë',    'veze ferme 10 cope',                0.60),

  ('nescafe-gold-200g',     'Viva Fresh Store',   6.49, 4, 'verified_retailer', 'scrape:vivafresh:nesc', 'Prishtinë', 'Kosovë',    'Nescafé Gold 200g',                 0.95),
  ('nescafe-gold-200g',     'ETC Supermarket',    6.79, 6, 'verified_retailer', 'scrape:etc:nescafe',    'Prishtinë', 'Kosovë',    'Nescafe Gold 200 g',                0.93),
  ('nescafe-gold-200g',     'Tregu i Gjelbër',    6.00, 2, 'crowdsourced',      'sub:usr_5533',          'Prishtinë', 'Kosovë',    'nescafe gold',                      0.45),

  ('spaghetti-barilla-500g','ETC Supermarket',    1.29, 3, 'verified_retailer', 'scrape:etc:barilla',    'Prishtinë', 'Kosovë',    'Barilla Spaghetti n.5 500g',        0.94),
  ('spaghetti-barilla-500g','Conad Tirana',       1.19, 7, 'crowdsourced',      'sub:usr_5590',          'Tiranë',    'Shqipëri',  'Barilla Spaghetti 500g',            0.60),

  ('rice-1kg',              'Interex',            1.49, 5, 'verified_retailer', 'scrape:interex:rice',   'Prizren',   'Kosovë',    'Oriz 1kg',                          0.90),
  ('rice-1kg',              'Viva Fresh Store',   1.55, 3, 'verified_retailer', 'scrape:vivafresh:rice', 'Prishtinë', 'Kosovë',    'Oriz Basmati 1kg',                  0.90),
  ('rice-1kg',              'Tregu i Gjelbër',    1.40, 2, 'crowdsourced',      'sub:usr_6120',          'Prishtinë', 'Kosovë',    'oriz 1kg',                          0.50),

  ('butter-250g',           'Viva Fresh Store',   2.29, 3, 'verified_retailer', 'scrape:vivafresh:butt', 'Prishtinë', 'Kosovë',    'Gjalpë President 250g',             0.92),
  ('butter-250g',           'Meridian Express',   2.39, 5, 'verified_retailer', 'scrape:meridian:butter','Ferizaj',   'Kosovë',    'gjalpe 250g',                       0.90),

  ('coffee-ground-200g',    null,                 2.60,11, 'official',          'ASK:CPI-coffee-2026-06','Kosovë',    'Kosovë',    'ASK avg price, ground coffee 200g', 1.00),
  ('coffee-ground-200g',    'ETC Supermarket',    2.75, 4, 'verified_retailer', 'scrape:etc:coffee',     'Prishtinë', 'Kosovë',    'Kafe e bluar Solis 200g',           0.90),
  ('coffee-ground-200g',    'Tregu i Gjelbër',    2.50, 1, 'crowdsourced',      'sub:usr_7420',          'Prishtinë', 'Kosovë',    'kafe solis 200g',                   0.50),

  ('water-1.5l',            'Viva Fresh Store',   0.45, 2, 'verified_retailer', 'scrape:vivafresh:water','Prishtinë', 'Kosovë',    'Ujë Rugove 1.5L',                   0.95),
  ('water-1.5l',            'Interex',            0.49, 5, 'verified_retailer', 'scrape:interex:water',  'Prizren',   'Kosovë',    'uje rugove 1.5l',                   0.90),
  ('water-1.5l',            'Tregu i Gjelbër',    0.40, 1, 'crowdsourced',      'sub:usr_8810',          'Prishtinë', 'Kosovë',    'uje 1.5l',                          0.50),

  -- ---- electronics ----
  ('iphone-15-128gb',       'Gjirafa50',        849.00, 3, 'verified_retailer', 'scrape:gjirafa50:iph15','Prishtinë', 'Kosovë',    'Apple iPhone 15 128GB',             0.97),
  ('iphone-15-128gb',       'Neptun',           879.00, 5, 'verified_retailer', 'scrape:neptun:iph15',   'Prishtinë', 'Kosovë',    'iPhone 15 128 GB',                  0.96),
  ('iphone-15-128gb',       'Foleja Elektronike',869.00,6, 'verified_retailer', 'scrape:foleja:iph15',   'Pejë',      'Kosovë',    'iPhone15 128gb',                    0.90),
  ('iphone-15-128gb',       'NeoTek',           830.00, 2, 'crowdsourced',      'sub:usr_9001',          'Tiranë',    'Shqipëri',  'iphone 15 128 (cmim ne dyqan)',     0.55),

  ('samsung-galaxy-a55',    'Gjirafa50',        379.00, 3, 'verified_retailer', 'scrape:gjirafa50:a55',  'Prishtinë', 'Kosovë',    'Samsung Galaxy A55 256GB',          0.96),
  ('samsung-galaxy-a55',    'Neptun',           399.00, 5, 'verified_retailer', 'scrape:neptun:a55',     'Prishtinë', 'Kosovë',    'Galaxy A55',                        0.95),
  ('samsung-galaxy-a55',    'Foleja Elektronike',389.00,4, 'verified_retailer', 'scrape:foleja:a55',     'Pejë',      'Kosovë',    'samsung a55 256',                   0.90),

  ('sony-wh1000xm5',        'Gjirafa50',        329.00, 4, 'verified_retailer', 'scrape:gjirafa50:xm5',  'Prishtinë', 'Kosovë',    'Sony WH-1000XM5',                   0.95),
  ('sony-wh1000xm5',        'Neptun',           349.00, 6, 'verified_retailer', 'scrape:neptun:xm5',     'Prishtinë', 'Kosovë',    'Sony WH1000XM5 kufje',              0.93),
  ('sony-wh1000xm5',        'NeoTek',           310.00, 2, 'crowdsourced',      'sub:usr_9102',          'Tiranë',    'Shqipëri',  'sony xm5 kufje',                    0.50),

  ('lg-55-4k-tv',           'Gjirafa50',        549.00, 5, 'verified_retailer', 'scrape:gjirafa50:lg55', 'Prishtinë', 'Kosovë',    'LG 55" UHD 4K Smart TV',            0.94),
  ('lg-55-4k-tv',           'Neptun',           579.00, 6, 'verified_retailer', 'scrape:neptun:lg55',    'Prishtinë', 'Kosovë',    'LG 55 inch 4K',                     0.93),
  ('lg-55-4k-tv',           'Foleja Elektronike',559.00,7, 'verified_retailer', 'scrape:foleja:lg55',    'Pejë',      'Kosovë',    'LG 55 4k tv',                       0.90),

  ('redmi-note-13',         'Gjirafa50',        199.00, 3, 'verified_retailer', 'scrape:gjirafa50:rn13', 'Prishtinë', 'Kosovë',    'Xiaomi Redmi Note 13 128GB',        0.95),
  ('redmi-note-13',         'Foleja Elektronike',209.00,5, 'verified_retailer', 'scrape:foleja:rn13',    'Pejë',      'Kosovë',    'redmi note 13',                     0.90),
  ('redmi-note-13',         'NeoTek',           189.00, 2, 'crowdsourced',      'sub:usr_9203',          'Tiranë',    'Shqipëri',  'redmi note 13 128',                 0.50),

  ('logitech-mx-master-3s', 'Gjirafa50',         99.00, 4, 'verified_retailer', 'scrape:gjirafa50:mx3s', 'Prishtinë', 'Kosovë',    'Logitech MX Master 3S',             0.95),
  ('logitech-mx-master-3s', 'Neptun',           109.00, 6, 'verified_retailer', 'scrape:neptun:mx3s',    'Prishtinë', 'Kosovë',    'MX Master 3S maus',                 0.90),

  ('dell-xps-13',           'Gjirafa50',       1199.00, 5, 'verified_retailer', 'scrape:gjirafa50:xps13','Prishtinë', 'Kosovë',    'Dell XPS 13 i7 16GB',               0.94),
  ('dell-xps-13',           'Neptun',          1249.00, 7, 'verified_retailer', 'scrape:neptun:xps13',   'Prishtinë', 'Kosovë',    'Dell XPS13',                        0.92),

  ('ps5-slim',              'Gjirafa50',        499.00, 3, 'verified_retailer', 'scrape:gjirafa50:ps5',  'Prishtinë', 'Kosovë',    'PlayStation 5 Slim',                0.96),
  ('ps5-slim',              'Neptun',           519.00, 5, 'verified_retailer', 'scrape:neptun:ps5',     'Prishtinë', 'Kosovë',    'PS5 Slim',                          0.94),
  ('ps5-slim',              'NeoTek',           489.00, 2, 'crowdsourced',      'sub:usr_9304',          'Tiranë',    'Shqipëri',  'ps5 slim disk',                     0.55),

  ('anker-powerbank-20000', 'Gjirafa50',         39.90, 4, 'verified_retailer', 'scrape:gjirafa50:ank20','Prishtinë', 'Kosovë',    'Anker PowerCore 20000mAh',          0.94),
  ('anker-powerbank-20000', 'Foleja Elektronike', 42.00,5, 'verified_retailer', 'scrape:foleja:ank20',   'Pejë',      'Kosovë',    'anker 20000 mah',                   0.90),

  -- ---- car parts ----
  ('bosch-wiper-24',        'AutoPjesë Blloku',  14.90, 4, 'verified_retailer', 'scrape:autoblloku:wp24','Prishtinë', 'Kosovë',    'Bosch Aerotwin 24"',                0.90),
  ('bosch-wiper-24',        'AutoStar Kosova',   12.50, 3, 'crowdsourced',      'sub:usr_7710',          'Mitrovicë', 'Kosovë',    'fshirese xhami bosch 24',           0.55),

  ('castrol-5w30-4l',       'AutoPjesë Blloku',  32.00, 5, 'verified_retailer', 'scrape:autoblloku:cas4','Prishtinë', 'Kosovë',    'Castrol EDGE 5W-30 4L',             0.92),
  ('castrol-5w30-4l',       'AutoStar Kosova',   29.90, 4, 'crowdsourced',      'sub:usr_7711',          'Mitrovicë', 'Kosovë',    'castrol 5w30 4l',                   0.50),

  ('brake-pads-golf-front', 'AutoPjesë Blloku',  34.50, 5, 'verified_retailer', 'scrape:autoblloku:brk', 'Prishtinë', 'Kosovë',    'ATE brake pads VW Golf front',      0.90),
  ('brake-pads-golf-front', 'AutoStar Kosova',   30.00, 3, 'crowdsourced',      'sub:usr_7712',          'Mitrovicë', 'Kosovë',    'ferrota golf para',                 0.50),

  ('ngk-spark-plugs-4',     'AutoPjesë Blloku',  18.00, 6, 'verified_retailer', 'scrape:autoblloku:ngk', 'Prishtinë', 'Kosovë',    'NGK spark plugs set/4',             0.90),
  ('ngk-spark-plugs-4',     'AutoStar Kosova',   16.50, 4, 'crowdsourced',      'sub:usr_7713',          'Mitrovicë', 'Kosovë',    'kandela ngk 4 cope',                0.50),

  ('michelin-205-55-r16',   'AutoPjesë Blloku',  89.00, 5, 'verified_retailer', 'scrape:autoblloku:mic', 'Prishtinë', 'Kosovë',    'Michelin Primacy 205/55 R16',       0.90),
  ('michelin-205-55-r16',   'AutoStar Kosova',   82.00, 3, 'crowdsourced',      'sub:usr_7714',          'Mitrovicë', 'Kosovë',    'goma michelin 205 55 16',           0.55),

  ('bosch-battery-70ah',    'AutoPjesë Blloku',  95.00, 6, 'verified_retailer', 'scrape:autoblloku:bat', 'Prishtinë', 'Kosovë',    'Bosch S4 12V 70Ah',                 0.90),
  ('bosch-battery-70ah',    'AutoStar Kosova',   88.00, 4, 'crowdsourced',      'sub:usr_7715',          'Mitrovicë', 'Kosovë',    'akumulator bosch 70ah',             0.50),

  ('air-filter-golf7',      'AutoPjesë Blloku',  11.50, 5, 'verified_retailer', 'scrape:autoblloku:air', 'Prishtinë', 'Kosovë',    'Mann air filter Golf 7',            0.90),
  ('air-filter-golf7',      'AutoStar Kosova',    9.90, 3, 'crowdsourced',      'sub:usr_7716',          'Mitrovicë', 'Kosovë',    'filter ajri golf 7',                0.50)
) as v(canonical_name, store_name, price, days_ago, trust_tier,
       source_id, geo_city, geo_region, raw_source_text, confidence_score)
join canonical_products p on p.canonical_name = v.canonical_name
left join stores s on s.name = v.store_name;

-- ---------------------------------------------------------------------------
-- A few user submissions + reputation rows (crowdsource pipeline sample)
-- ---------------------------------------------------------------------------
insert into user_submissions (user_id, product_id, store_id, price, photo_url, status, submitted_at)
select
  v.user_id::uuid,
  p.id,
  s.id,
  v.price,
  v.photo_url,
  v.status::submission_status,
  now() - (v.days_ago || ' days')::interval
from (values
  ('11111111-1111-1111-1111-111111111111', 'coca-cola-1.5l', 'Tregu i Gjelbër', 1.10, 'https://picsum.photos/seed/sub1/400/300', 'verified', 1),
  ('22222222-2222-2222-2222-222222222222', 'eggs-10',        'Tregu i Gjelbër', 1.80, 'https://picsum.photos/seed/sub2/400/300', 'verified', 1),
  ('33333333-3333-3333-3333-333333333333', 'ps5-slim',       'NeoTek',          489.00,'https://picsum.photos/seed/sub3/400/300', 'pending',  2),
  ('22222222-2222-2222-2222-222222222222', 'water-1.5l',     'Tregu i Gjelbër', 0.20, null,                                      'rejected', 3)
) as v(user_id, canonical_name, store_name, price, photo_url, status, days_ago)
join canonical_products p on p.canonical_name = v.canonical_name
left join stores s on s.name = v.store_name;

insert into user_reputation (user_id, confirmed_count, rejected_count, trust_score) values
  ('11111111-1111-1111-1111-111111111111', 42, 3,  0.930),
  ('22222222-2222-2222-2222-222222222222', 12, 5,  0.706),
  ('33333333-3333-3333-3333-333333333333', 0,  0,  0.000);
