const courseModel = require('../models/course.model');
const userModel = require('../models/user.model');
const enrollmentModel = require('../models/enrollment.model');
const { hashPassword } = require('../utils/crypto');
const { AppError } = require('../middlewares/error.middleware');

/**
 * Fluxo de checkout legado preservado:
 * 1) curso ativo
 * 2) user por email (cria se não existir)
 * 3) pagamento: cartão começando com "4" => PAID, senão DENIED
 * 4) enrollment + payment + audit
 */
async function processCheckout({ name, email, password, courseId, card }) {
  const course = await courseModel.findActiveById(courseId);
  if (!course) {
    throw new AppError('Curso não encontrado', 404);
  }

  let user = await userModel.findByEmail(email);
  let userId;

  if (!user) {
    const passwordHash = hashPassword(password);
    userId = await userModel.createUser(name, email, passwordHash);
  } else {
    userId = user.id;
  }

  // Regra legado: cartão iniciando com "4" => PAID. Gateway key em config (nunca logada).
  const status = String(card).startsWith('4') ? 'PAID' : 'DENIED';
  if (status === 'DENIED') {
    throw new AppError('Pagamento recusado', 400);
  }

  const enrollmentId = await enrollmentModel.createEnrollment(userId, courseId);
  await enrollmentModel.createPayment(enrollmentId, course.price, status);
  await enrollmentModel.createAuditLog(`Checkout curso ${courseId} por ${userId}`);

  return { msg: 'Sucesso', enrollment_id: enrollmentId };
}

async function buildFinancialReport() {
  const rows = await enrollmentModel.financialReportRows();
  const byCourse = new Map();

  for (const row of rows) {
    if (!byCourse.has(row.course_id)) {
      byCourse.set(row.course_id, {
        course: row.course_title,
        revenue: 0,
        students: [],
      });
    }

    const courseData = byCourse.get(row.course_id);
    if (row.enrollment_id == null) {
      continue;
    }

    if (row.payment_status === 'PAID') {
      courseData.revenue += row.payment_amount || 0;
    }

    courseData.students.push({
      student: row.student_name || 'Unknown',
      paid: row.payment_amount || 0,
    });
  }

  return Array.from(byCourse.values());
}

async function deleteUser(userId) {
  await userModel.deleteUser(userId);
}

module.exports = { processCheckout, buildFinancialReport, deleteUser };
