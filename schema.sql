PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS members (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  name TEXT NOT NULL,
  level TEXT CHECK(level IN ('大區','分公司','金牌')) NOT NULL,
  sponsor_id INTEGER REFERENCES members(id),
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
