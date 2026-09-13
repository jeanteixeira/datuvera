-- Create demo tables and insert sample data
CREATE TABLE IF NOT EXISTS customers (
  id serial PRIMARY KEY,
  name text NOT NULL,
  email text
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

INSERT INTO customers (name, email)
SELECT 'Customer ' || g, 'customer' || g || '@example.com' FROM generate_series(1,20) g;

INSERT INTO products (name, price)
SELECT 'Product ' || g, (g * 1.5) FROM generate_series(1,10) g;

-- Ensure product_id/customer_id within valid ranges
INSERT INTO orders (customer_id, product_id, qty)
SELECT (floor(random() * 20)::int) + 1, (floor(random() * 10)::int) + 1, (floor(random() * 5)::int) + 1 FROM generate_series(1,100) g;
