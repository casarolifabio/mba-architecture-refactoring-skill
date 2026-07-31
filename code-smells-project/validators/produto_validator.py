from config.settings import CATEGORIAS_VALIDAS


class ValidationError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def validate_produto_payload(dados, require_categoria_list=True):
    if not dados:
        raise ValidationError("Dados inválidos")
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", "geral")

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < 2:
        raise ValidationError("Nome muito curto")
    if len(nome) > 200:
        raise ValidationError("Nome muito longo")

    if require_categoria_list and categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError(
            "Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS)
        )

    return {
        "nome": nome,
        "descricao": descricao,
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
    }
