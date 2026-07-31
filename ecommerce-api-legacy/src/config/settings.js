/**
 * Configuração via environment variables.
 * Defaults são apenas para desenvolvimento local — não são secrets de produção.
 */
module.exports = {
  port: Number(process.env.PORT || 3000),
  dbPath: process.env.DB_PATH || ':memory:',
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || 'dev-payment-key', // placeholder local
  smtpUser: process.env.SMTP_USER || 'dev@localhost',
  dbUser: process.env.DB_USER || 'dev_user',
  dbPass: process.env.DB_PASS || 'dev_pass',
};
