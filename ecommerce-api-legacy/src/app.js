const express = require('express');
const settings = require('./config/settings');
const { initDb } = require('./models/db');
const routes = require('./routes');
const { errorMiddleware } = require('./middlewares/error.middleware');

async function start() {
  const app = express();
  app.use(express.json());

  await initDb();
  app.use(routes);
  app.use(errorMiddleware);

  app.listen(settings.port, () => {
    console.log(`Frankenstein LMS rodando na porta ${settings.port}...`);
  });
}

start().catch((err) => {
  console.error('Falha ao iniciar aplicação:', err);
  process.exit(1);
});
