from checkers.base_quali_checker import BaseQualiChecker

class ImEmitenteChecker(BaseQualiChecker):
    check_name = "im_emitente"
    table_name = "tipo_licitacao"
    
    def check(self, record):
        if "nfe" in record.keys() and "im_emitente" in record['nfe'].keys() and record['nfe']["im_emitente"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["im_emitente"],40):
                return False, f"Inscrição Municipal Emitente({record['nfe']['im_emitente']}) fora do tamanho permitido."
        return True,None