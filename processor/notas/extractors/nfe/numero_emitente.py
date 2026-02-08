from ..base_extractor import BaseExtractor

class NumeroEmitenteExtractor(BaseExtractor):
    field_name = "numero_emitente"
    scope = "nfe"

    def extract(self, record):
        # Pega o valor da chave original (ex: "NUMERO_EMITENTE")
        valor = record.get("NUMERO_EMITENTE")
        
        # Se o valor for nulo ou uma string vazia, já retorna None de cara.
        if valor is None or (isinstance(valor, str) and valor.strip() == ''):
            return None
        
        try:
            # Tenta converter o valor para um número.
            # Usamos float() primeiro para lidar com casos que possam vir como "904.0",
            # e depois int() para garantir que o resultado final seja um número inteiro.
            return int(float(valor))
        except (ValueError, TypeError):
            # Se a conversão falhar (ex: para a string "s/n" ou "616 sala"),
            # o Python gera um erro. Nós o capturamos e retornamos None,
            # tratando todos os textos não-numéricos como nulos.
            return None