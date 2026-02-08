from checkers.base_quali_checker import BaseQualiChecker

class CrtEmitenteChecker(BaseQualiChecker):
    check_name = "crt_emitente"
    table_name = "tipo_licitacao"
    
    def check(self, record):
        if "nfe" in record.keys() and "crt_emitente" in record['nfe'].keys() and record['nfe']["crt_emitente"] not in ("indefinido","null",None,""):
            if not self.is_valid_integer(record['nfe']["crt_emitente"]):
                return False, f"CRT Emitente({record['nfe']['crt_emitente']}) inválido."

        return True,None