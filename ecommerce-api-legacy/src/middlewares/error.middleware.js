class AppError extends Error {
  constructor(message, status = 400) {
    super(message);
    this.status = status;
    this.expose = true;
  }
}

function errorMiddleware(err, req, res, _next) {
  const status = err.status || 500;
  const message = err.expose ? err.message : 'Internal Error';

  // Sucesso legado misturava texto e JSON; erros passam a JSON com a mesma mensagem.
  res.status(status).json({ error: message });
}

module.exports = { AppError, errorMiddleware };
