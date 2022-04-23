DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS challenges;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    cookie TEXT NULL
);

INSERT INTO users (username, password) VALUES ('test_user', '12345');

CREATE TABLE challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    challenge TEXT NOT NULL,
    response TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
)