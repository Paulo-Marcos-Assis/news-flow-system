from ..base_verifier import BaseVerifier
class GtinProdutoVerifier(BaseVerifier):
    scope = "item"
    field_name = "gtin_produto"

    def verify(self, record):
        # Primeiro, verifica se o registro é nulo, vazio ou "nan"
        if record is None or str(record).strip().lower() in ['', 'nan']:
            return True, None
        
        # Força string e remove espaços/quebras
        record = str(record).strip()
        
        # Lista de tamanhos válidos considerando ter .00 no dado por causa do
        tamanhos_validos = [8, 12, 13, 14]

        # Verifica se o tamanho do código NÃO ESTÁ na lista de tamanhos válidos
        if len(record) not in tamanhos_validos: 
            return True, None
            
        return True, None