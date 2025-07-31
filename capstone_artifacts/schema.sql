CREATE TABLE Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    interests TEXT    -- Comma-separated list of activities/attractions
);

CREATE TABLE Properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address_line1 TEXT NOT NULL,
    address_line2 TEXT,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    zip_code TEXT NOT NULL,
    country TEXT NOT NULL DEFAULT 'USA',
    price_per_night REAL NOT NULL,
    amenities TEXT   -- Comma-separated list of basic amenities
);

CREATE TABLE Reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    property_id INTEGER NOT NULL,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    reservation_date DATE NOT NULL DEFAULT (DATE('now')),
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (property_id) REFERENCES Properties(id)
);