const { get, all } = require('./db');

async function findActiveById(courseId) {
  return get('SELECT * FROM courses WHERE id = ? AND active = 1', [courseId]);
}

async function findAll() {
  return all('SELECT * FROM courses');
}

module.exports = { findActiveById, findAll };
