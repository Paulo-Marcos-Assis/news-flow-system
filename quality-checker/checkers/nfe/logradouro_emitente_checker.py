from checkers.base_quali_checker import BaseQualiChecker

class LogradouroEmitenteChecker(BaseQualiChecker):
    check_name = "logradouro_emitente"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "logradouro_emitente" in record['nfe'].keys() and record['nfe']["logradouro_emitente"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["logradouro_emitente"],255):
                return False, f"Logradouro Emitente({record['nfe']['logradouro_emitente']}) fora do tamanho permitido."
        return True,None