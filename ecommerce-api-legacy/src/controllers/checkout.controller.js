const checkoutService = require('../services/checkout.service');
const { validateCheckoutBody } = require('../validators/checkout.validator');

async function checkout(req, res, next) {
  try {
    const payload = validateCheckoutBody(req.body);
    const result = await checkoutService.processCheckout(payload);
    // Contrato de sucesso preservado.
    res.status(200).json(result);
  } catch (err) {
    next(err);
  }
}

async function financialReport(req, res, next) {
  try {
    const report = await checkoutService.buildFinancialReport();
    res.status(200).json(report);
  } catch (err) {
    next(err);
  }
}

async function deleteUser(req, res, next) {
  try {
    await checkoutService.deleteUser(req.params.id);
    // Preserva resposta textual do legado (mensagem atualizada: órfãos não ficam mais).
    res
      .status(200)
      .send('Usuário deletado. Matrículas e pagamentos relacionados foram removidos.');
  } catch (err) {
    next(err);
  }
}

module.exports = { checkout, financialReport, deleteUser };
