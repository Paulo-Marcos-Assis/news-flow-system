from ..base_verifier import BaseVerifier
class UnidadeComercialVerifier(BaseVerifier):
    scope = "item"
    field_name = "unidade_comercial"

    dict_unidades = {
        "ampola",
        "balde",
        "bandeja",
        "barra",
        "bisnaga",
        "blister",
        "bloco",
        "bobina",
        "bolsa",
        "bombona",
        "caixa",
        "capsula",
        "cartela",
        "conjunto",
        "cm",
        "cm2",
        "cento",
        "comprimido",
        "display",
        "dragea",
        "duzia",
        "embalagem",
        "envelope",
        "fardo",
        "folha",
        "frasco",
        "frasco-ampola",
        "galao",
        "garrafa",
        "gramas",
        "jogo",
        "quilate",
        "kilograma",
        "kit",
        "lata",
        "litro",
        "metro2",
        "metro3",
        "metro",
        "mililitro",
        "milheiro",
        "mwh",
        "pacote",
        "palete",
        "par",
        "peca",
        "pote",
        "resma",
        "rolo",
        "saco",
        "sacola",
        "sache",
        "tambor",
        "tonelada",
        "tubo",
        "unidade",
        "vidro",
    }

    def verify(self, record) -> bool:
        """
        Retorna True se `record` estiver na lista de unidades permitidas.
        """
        if record in self.dict_unidades:
            return True, None
        else:
            return False, f"Unidade não reconhecida: {record}"