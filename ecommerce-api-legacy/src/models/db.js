const sqlite3 = require('sqlite3').verbose();
const settings = require('../config/settings');
const { hashPassword } = require('../utils/crypto');

let db;

function getDb() {
  if (!db) {
    throw new Error('Database not initialized');
  }
  return db;
}

function run(sql, params = []) {
  return new Promise((resolve, reject) => {
    getDb().run(sql, params, function onRun(err) {
      if (err) reject(err);
      else resolve({ lastID: this.lastID, changes: this.changes });
    });
  });
}

function get(sql, params = []) {
  return new Promise((resolve, reject) => {
    getDb().get(sql, params, (err, row) => {
      if (err) reject(err);
      else resolve(row);
    });
  });
}

function all(sql, params = []) {
  return new Promise((resolve, reject) => {
    getDb().all(sql, params, (err, rows) => {
      if (err) reject(err);
      else resolve(rows);
    });
  });
}

async function initDb() {
  db = new sqlite3.Database(settings.dbPath);

  await run(`CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT,
    pass TEXT
  )`);
  await run(`CREATE TABLE courses (
    id INTEGER PRIMARY KEY,
    title TEXT,
    price REAL,
    active INTEGER
  )`);
  await run(`CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    course_id INTEGER
  )`);
  await run(`CREATE TABLE payments (
    id INTEGER PRIMARY KEY,
    enrollment_id INTEGER,
    amount REAL,
    status TEXT
  )`);
  await run(`CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    action TEXT,
    created_at DATETIME
  )`);

  const adminHash = hashPassword('123');
  await run(
    'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
    ['Leonan', 'leonan@fullcycle.com.br', adminHash]
  );
  await run(
    'INSERT INTO courses (title, price, active) VALUES (?, ?, ?), (?, ?, ?)',
    ['Clean Architecture', 997.0, 1, 'Docker', 497.0, 1]
  );
  await run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [1, 1]);
  await run(
    'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
    [1, 997.0, 'PAID']
  );
}

module.exports = { initDb, getDb, run, get, all };
