import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")  # placeholder local; defina SECRET_KEY em produção
DEBUG = os.environ.get("DEBUG", "false").lower() in ("1", "true", "yes")
DATABASE = os.environ.get("DATABASE", "loja.db")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))

# Faixas de desconto do relatório de vendas (ex-magic numbers)
DISCOUNT_TIER_HIGH = 10000
DISCOUNT_RATE_HIGH = 0.1
DISCOUNT_TIER_MID = 5000
DISCOUNT_RATE_MID = 0.05
DISCOUNT_TIER_LOW = 1000
DISCOUNT_RATE_LOW = 0.02

CATEGORIAS_VALIDAS = [
    "informatica",
    "moveis",
    "vestuario",
    "geral",
    "eletronicos",
    "livros",
]

STATUS_PEDIDO_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]
