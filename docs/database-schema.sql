-- Generated from SQLAlchemy metadata; monetary totals use BIGINT.
PRAGMA foreign_keys=ON;

CREATE TABLE market_prices (
	id INTEGER NOT NULL, 
	crop VARCHAR(50) NOT NULL, 
	region VARCHAR(60) NOT NULL, 
	price_tzs INTEGER NOT NULL, 
	observed_on DATE NOT NULL, 
	source VARCHAR(100) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (crop, region), 
	CHECK (price_tzs > 0)
);

CREATE TABLE revoked_tokens (
	jti VARCHAR(36) NOT NULL, 
	expires_at DATETIME NOT NULL, 
	PRIMARY KEY (jti)
);

CREATE TABLE users (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	active BOOLEAN NOT NULL, 
	phone VARCHAR(16) NOT NULL, 
	region VARCHAR(60) NOT NULL, 
	location VARCHAR(160) NOT NULL, 
	farm_size_acres INTEGER NOT NULL, 
	crop_categories VARCHAR(250) NOT NULL, 
	business_name VARCHAR(160) NOT NULL, 
	verification_note VARCHAR(300) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (role IN ('farmer','buyer','administrator','logistics','transporter')), 
	CHECK (status IN ('pending','approved','rejected')), 
	CHECK (farm_size_acres >= 0)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE INDEX ix_users_role ON users (role);

CREATE TABLE notifications (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	kind VARCHAR(30) NOT NULL, 
	message VARCHAR(500) NOT NULL, 
	read BOOLEAN NOT NULL, 
	sms_status VARCHAR(20) NOT NULL, 
	sms_reference VARCHAR(50) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_notifications_user_id ON notifications (user_id);

CREATE TABLE produce (
	id INTEGER NOT NULL, 
	farmer_id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	crop VARCHAR(50) NOT NULL, 
	description TEXT NOT NULL, 
	available_kg INTEGER NOT NULL, 
	price_tzs INTEGER NOT NULL, 
	harvest_date DATE NOT NULL, 
	active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (available_kg >= 0), 
	CHECK (price_tzs > 0), 
	FOREIGN KEY(farmer_id) REFERENCES users (id)
);

CREATE INDEX ix_produce_crop ON produce (crop);

CREATE INDEX ix_produce_farmer_id ON produce (farmer_id);

CREATE INDEX ix_produce_name ON produce (name);

CREATE TABLE purchase_orders (
	id INTEGER NOT NULL, 
	buyer_id INTEGER NOT NULL, 
	farmer_id INTEGER NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	total_tzs BIGINT NOT NULL, 
	idempotency_key VARCHAR(80) NOT NULL, 
	fingerprint VARCHAR(64) NOT NULL, 
	delivery_address VARCHAR(250) NOT NULL, 
	note VARCHAR(300) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (buyer_id, idempotency_key), 
	CHECK (total_tzs > 0), 
	CHECK (status IN ('pending_farmer_approval','accepted','awaiting_payment','paid','processing_delivery','in_transit','delivered','completed','rejected','cancelled','payment_failed','return_requested','returned')), 
	FOREIGN KEY(buyer_id) REFERENCES users (id), 
	FOREIGN KEY(farmer_id) REFERENCES users (id)
);

CREATE INDEX ix_purchase_orders_buyer_id ON purchase_orders (buyer_id);

CREATE INDEX ix_purchase_orders_farmer_id ON purchase_orders (farmer_id);

CREATE TABLE order_items (
	id INTEGER NOT NULL, 
	order_id INTEGER NOT NULL, 
	produce_id INTEGER NOT NULL, 
	quantity_kg INTEGER NOT NULL, 
	unit_price_tzs INTEGER NOT NULL, 
	produce_name VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (order_id, produce_id), 
	CHECK (quantity_kg > 0), 
	CHECK (unit_price_tzs > 0), 
	FOREIGN KEY(order_id) REFERENCES purchase_orders (id), 
	FOREIGN KEY(produce_id) REFERENCES produce (id)
);

CREATE INDEX ix_order_items_order_id ON order_items (order_id);

CREATE TABLE payments (
	id INTEGER NOT NULL, 
	order_id INTEGER NOT NULL, 
	buyer_id INTEGER NOT NULL, 
	provider VARCHAR(20) NOT NULL, 
	phone VARCHAR(16) NOT NULL, 
	amount_tzs BIGINT NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	reference VARCHAR(60) NOT NULL, 
	idempotency_key VARCHAR(80) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (buyer_id, idempotency_key), 
	CHECK (amount_tzs > 0), 
	CHECK (status IN ('pending','successful','failed','cancelled')), 
	CHECK (provider IN ('mpesa','airtel_money','tigo_pesa')), 
	FOREIGN KEY(order_id) REFERENCES purchase_orders (id), 
	FOREIGN KEY(buyer_id) REFERENCES users (id), 
	UNIQUE (reference)
);

CREATE INDEX ix_payments_order_id ON payments (order_id);

CREATE TABLE shipments (
	id INTEGER NOT NULL, 
	order_id INTEGER NOT NULL, 
	transporter_id INTEGER, 
	status VARCHAR(30) NOT NULL, 
	tracking_code VARCHAR(40) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (status IN ('pending_arrangement','awaiting_transporter','assignment_failed','assigned','ready_for_pickup','picked_up','in_transit','delivery_failed','delivered','return_requested','returned')), 
	UNIQUE (order_id), 
	FOREIGN KEY(order_id) REFERENCES purchase_orders (id), 
	FOREIGN KEY(transporter_id) REFERENCES users (id), 
	UNIQUE (tracking_code)
);

CREATE TABLE payment_receipts (
	id INTEGER NOT NULL, 
	payment_id INTEGER NOT NULL, 
	order_id INTEGER NOT NULL, 
	number VARCHAR(40) NOT NULL, 
	amount_tzs BIGINT NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (payment_id), 
	FOREIGN KEY(payment_id) REFERENCES payments (id), 
	UNIQUE (order_id), 
	FOREIGN KEY(order_id) REFERENCES purchase_orders (id), 
	UNIQUE (number)
);

CREATE TABLE tracking_events (
	id INTEGER NOT NULL, 
	shipment_id INTEGER NOT NULL, 
	actor_id INTEGER NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	location VARCHAR(160) NOT NULL, 
	note VARCHAR(300) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(shipment_id) REFERENCES shipments (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
);

CREATE INDEX ix_tracking_events_shipment_id ON tracking_events (shipment_id);

