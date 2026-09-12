-- PostgreSQL schema generated from SQLAlchemy models.
-- Reference only: initialize the application with python -m app.init_db.
-- Python-side defaults are applied by the ORM. Do not use this as a data seed.


CREATE TABLE categories (
	id SERIAL NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
)

;

CREATE TABLE suppliers (
	id SERIAL NOT NULL, 
	name VARCHAR(160) NOT NULL, 
	phone VARCHAR(30) NOT NULL, 
	address VARCHAR(300) NOT NULL, 
	active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
)

;

CREATE TABLE units (
	id SERIAL NOT NULL, 
	name VARCHAR(60) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
)

;

CREATE TABLE users (
	id SERIAL NOT NULL, 
	username VARCHAR(80) NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(256) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	active BOOLEAN NOT NULL, 
	token_version INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (role IN ('manager','pharmacist','cashier')), 
	UNIQUE (username)
)

;

CREATE TABLE ai_logs (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	mode VARCHAR(30) NOT NULL, 
	prompt TEXT NOT NULL, 
	response TEXT NOT NULL, 
	sources TEXT NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	warning TEXT NOT NULL, 
	model VARCHAR(80) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

CREATE TABLE invoices (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	customer VARCHAR(120) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	total NUMERIC(16, 2) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	payment_method VARCHAR(20) NOT NULL, 
	request_key VARCHAR(80) NOT NULL, 
	request_hash VARCHAR(64) NOT NULL, 
	prescription_ref VARCHAR(200) NOT NULL, 
	cancel_reason VARCHAR(500) NOT NULL, 
	cancelled_by INTEGER, 
	PRIMARY KEY (id), 
	CHECK (status IN ('paid','cancelled')), 
	CHECK (total >= 0), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (request_key), 
	FOREIGN KEY(cancelled_by) REFERENCES users (id)
)

;

CREATE TABLE medicines (
	id SERIAL NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	name VARCHAR(180) NOT NULL, 
	category_id INTEGER NOT NULL, 
	unit_id INTEGER NOT NULL, 
	min_stock INTEGER NOT NULL, 
	prescription_required BOOLEAN NOT NULL, 
	active BOOLEAN NOT NULL, 
	information TEXT NOT NULL, 
	source VARCHAR(500) NOT NULL, 
	approved BOOLEAN NOT NULL, 
	approved_by INTEGER, 
	PRIMARY KEY (id), 
	CHECK (min_stock >= 0), 
	UNIQUE (code), 
	FOREIGN KEY(category_id) REFERENCES categories (id), 
	FOREIGN KEY(unit_id) REFERENCES units (id), 
	FOREIGN KEY(approved_by) REFERENCES users (id)
)

;
CREATE INDEX ix_medicines_name ON medicines (name);

CREATE TABLE procedures (
	id SERIAL NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	content TEXT NOT NULL, 
	approved BOOLEAN NOT NULL, 
	approved_by INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(approved_by) REFERENCES users (id)
)

;

CREATE TABLE batches (
	id SERIAL NOT NULL, 
	medicine_id INTEGER NOT NULL, 
	supplier_id INTEGER NOT NULL, 
	code VARCHAR(80) NOT NULL, 
	received_date DATE NOT NULL, 
	expiry_date DATE NOT NULL, 
	quantity INTEGER NOT NULL, 
	purchase_price NUMERIC(14, 2) NOT NULL, 
	sale_price NUMERIC(14, 2) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (medicine_id, code), 
	CHECK (quantity >= 0), 
	CHECK (purchase_price >= 0), 
	CHECK (sale_price >= 0), 
	CHECK (expiry_date > received_date), 
	FOREIGN KEY(medicine_id) REFERENCES medicines (id), 
	FOREIGN KEY(supplier_id) REFERENCES suppliers (id)
)

;
CREATE INDEX ix_batches_expiry_date ON batches (expiry_date);
CREATE INDEX ix_batches_medicine_id ON batches (medicine_id);

CREATE TABLE inventory_movements (
	id SERIAL NOT NULL, 
	batch_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	invoice_id INTEGER, 
	delta INTEGER NOT NULL, 
	balance INTEGER NOT NULL, 
	kind VARCHAR(30) NOT NULL, 
	reason VARCHAR(500) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(batch_id) REFERENCES batches (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(invoice_id) REFERENCES invoices (id)
)

;
CREATE INDEX ix_inventory_movements_batch_id ON inventory_movements (batch_id);

CREATE TABLE invoice_items (
	id SERIAL NOT NULL, 
	invoice_id INTEGER NOT NULL, 
	batch_id INTEGER NOT NULL, 
	medicine_name VARCHAR(180) NOT NULL, 
	unit_name VARCHAR(60) NOT NULL, 
	quantity INTEGER NOT NULL, 
	sale_price NUMERIC(14, 2) NOT NULL, 
	purchase_price NUMERIC(14, 2) NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (quantity > 0), 
	UNIQUE (invoice_id, batch_id), 
	FOREIGN KEY(invoice_id) REFERENCES invoices (id), 
	FOREIGN KEY(batch_id) REFERENCES batches (id)
)

;
CREATE INDEX ix_invoice_items_invoice_id ON invoice_items (invoice_id);