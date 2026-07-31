const { run, all } = require('./db');

async function createEnrollment(userId, courseId) {
  const result = await run(
    'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
    [userId, courseId]
  );
  return result.lastID;
}

async function createPayment(enrollmentId, amount, status) {
  const result = await run(
    'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
    [enrollmentId, amount, status]
  );
  return result.lastID;
}

async function createAuditLog(action) {
  await run(
    "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
    [action]
  );
}

/**
 * Relatório financeiro em uma única query (elimina N+1).
 */
async function financialReportRows() {
  return all(`
    SELECT
      c.id AS course_id,
      c.title AS course_title,
      e.id AS enrollment_id,
      u.name AS student_name,
      p.amount AS payment_amount,
      p.status AS payment_status
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN users u ON u.id = e.user_id
    LEFT JOIN payments p ON p.enrollment_id = e.id
    ORDER BY c.id, e.id
  `);
}

module.exports = {
  createEnrollment,
  createPayment,
  createAuditLog,
  financialReportRows,
};
