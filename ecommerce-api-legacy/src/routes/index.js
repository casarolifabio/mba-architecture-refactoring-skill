const express = require('express');
const checkoutController = require('../controllers/checkout.controller');

const router = express.Router();

router.post('/api/checkout', checkoutController.checkout);
router.get('/api/admin/financial-report', checkoutController.financialReport);
router.delete('/api/users/:id', checkoutController.deleteUser);

module.exports = router;
