from checkers.base_quali_checker import BaseQualiChecker

class IeStEmitenteChecker(BaseQualiChecker):
    check_name = "ie_st_emitente"
    table_name = "tipo_licitacao"
    
    def check(self, record):
        if "nfe" in record.keys() and "ie_st_emitente" in record['nfe'].keys() and record['nfe']["ie_st_emitente"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["ie_st_emitente"],255):
                return False, f"Inscrição Estadual Substituto Tributário do Emitente({record['nfe']['ie_st_emitente']}) fora do tamanho permitido."
        return True,None