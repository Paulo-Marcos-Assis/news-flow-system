from checkers.base_quali_checker import BaseQualiChecker

class NumeroEmitenteChecker(BaseQualiChecker):
    check_name = "numero_emitente"
    table_name = "tipo_licitacao"
    
    def check(self, record):
        if "nfe" in record.keys() and "numero_emitente" in record['nfe'].keys() and record['nfe']["numero_emitente"] not in ("indefinido","null",None,""): 
            if not self.is_valid_integer(record['nfe']["numero_emitente"]):
                return False, f"Número do emitente ({record['nfe']['numero_emitente']}) fora do tamanho permitido."
        return True,None
