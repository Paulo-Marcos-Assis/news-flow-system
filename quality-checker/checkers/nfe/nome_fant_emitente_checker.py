from checkers.base_quali_checker import BaseQualiChecker

class NomeFantEmitenteChecker(BaseQualiChecker):
    check_name = "nome_fant_emitente"
    table_name = "tipo_licitacao"
    
    def check(self, record):
        if "nfe" in record.keys() and "nome_fant_emitente" in record['nfe'].keys() and record['nfe']["nome_fant_emitente"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["nome_fant_emitente"],255):
                return False, f"Nome Fantasia Emitente({record['nfe']['nome_fant_emitente']}) fora do tamanho permitido."
        return True,None