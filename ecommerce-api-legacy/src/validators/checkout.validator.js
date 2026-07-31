const { AppError } = require('../middlewares/error.middleware');

function validateCheckoutBody(body) {
  if (!body || typeof body !== 'object') {
    throw new AppError('Bad Request', 400);
  }

  const name = body.usr;
  const email = body.eml;
  const password = body.pwd;
  const courseId = body.c_id;
  const card = body.card;

  // Preserva regra legado: u, e, cid, cc obrigatórios (truthy); pwd opcional.
  if (!name || !email || !courseId || !card) {
    throw new AppError('Bad Request', 400);
  }

  return {
    name,
    email,
    password: password || '123456',
    courseId,
    card: String(card),
  };
}

module.exports = { validateCheckoutBody };
