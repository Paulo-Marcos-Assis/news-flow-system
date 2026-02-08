from utils.cnpj_checker import CnpjChecker

class CnpjEmitenteChecker(CnpjChecker):
    check_name = "cnpj_emitente"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "cnpj_emitente" in record['nfe'].keys() and record['nfe']["cnpj_emitente"] not in ("indefinido","null",None,""): 
            # Checa CNJP e remove símbolos, caso tenha
            checked_cnpj = self.cnpj_check(record['nfe']['cnpj_emitente'])
            if checked_cnpj is None:
                return False, f"Cnpj emitente({record['nfe']['cnpj_emitente']}) inválido."
            record['nfe']["cnpj_emitente"] = checked_cnpj
        return True,None
        