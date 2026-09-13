-- Create demo tables and insert sample data
CREATE TABLE IF NOT EXISTS customers (
  id serial PRIMARY KEY,
  name text NOT NULL,
  email text,
  state text,
  birth_date date,
  is_active boolean,
  lifetime_value numeric,
  created_at timestamp
);

CREATE TABLE IF NOT EXISTS products (
  id serial PRIMARY KEY,
  name text NOT NULL,
  price numeric
);

CREATE TABLE IF NOT EXISTS orders (
  id serial PRIMARY KEY,
  customer_id integer REFERENCES customers(id),
  product_id integer REFERENCES products(id),
  qty integer DEFAULT 1
);

-- deterministic customers: 500 rows
INSERT INTO customers (name, email, state, birth_date, is_active, lifetime_value, created_at)
SELECT
  'Customer ' || g,
  -- deterministic: introduce NULLs (~3%) and some invalid emails (~2%)
  (CASE WHEN (g % 33) = 0 THEN NULL WHEN (g % 50) = 0 THEN 'invalid-email' ELSE ('customer' || g || '@example.com') END),
  (CASE WHEN (g % 64) = 0 THEN 'XX' WHEN (g % 127) = 0 THEN 'ZZ' ELSE (ARRAY['AL','SP','PE','BA','RJ'])[((g % 5) + 1)] END),
  (DATE '1970-01-01' + (g % 20000) * INTERVAL '1 day'),
  (CASE WHEN (g % 4) = 0 THEN true ELSE false END),
  -- lifetime_value: some NULLs deterministically (~2.5%)
  (CASE WHEN (g % 40) = 0 THEN NULL ELSE (g * 1.23) END),
  (now() - (g % 365) * INTERVAL '1 day')
FROM generate_series(1,500) g;

INSERT INTO products (name, price)
SELECT 'Product ' || g, (g * 1.5) FROM generate_series(1,10) g;

-- Ensure product_id/customer_id within valid ranges
-- deterministic orders
INSERT INTO orders (customer_id, product_id, qty)
SELECT ((g - 1) % 500) + 1, ((g - 1) % 10) + 1, ((g - 1) % 5) + 1 FROM generate_series(1,1000) g;
