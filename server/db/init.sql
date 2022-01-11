DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    credentials_id TEXT NULL
);

INSERT INTO users (username, password) VALUES ('test_user', '12345');