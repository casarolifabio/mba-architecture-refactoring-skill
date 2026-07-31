const { get, run, all } = require('./db');

async function findByEmail(email) {
  return get('SELECT id, name, email, pass FROM users WHERE email = ?', [email]);
}

async function findById(id) {
  return get('SELECT id, name, email FROM users WHERE id = ?', [id]);
}

async function createUser(name, email, passwordHash) {
  const result = await run(
    'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
    [name, email, passwordHash]
  );
  return result.lastID;
}

async function deleteUser(id) {
  // Limpa dependências para preservar integridade (finding P2-L2).
  const enrollments = await all('SELECT id FROM enrollments WHERE user_id = ?', [id]);
  for (const enr of enrollments) {
    await run('DELETE FROM payments WHERE enrollment_id = ?', [enr.id]);
  }
  await run('DELETE FROM enrollments WHERE user_id = ?', [id]);
  await run('DELETE FROM users WHERE id = ?', [id]);
}

module.exports = { findByEmail, findById, createUser, deleteUser };
