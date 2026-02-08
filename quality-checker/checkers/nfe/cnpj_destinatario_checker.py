from utils.cnpj_checker import CnpjChecker

class CnpjDestinatarioChecker(CnpjChecker):
    check_name = "cnpj_destinatario"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "cnpj_destinatario" in record['nfe'].keys() and record['nfe']["cnpj_destinatario"] not in ("indefinido","null",None,""): 
            # Checa CNJP e remove símbolos, caso tenha
            checked_cnpj = self.cnpj_check(record['nfe']['cnpj_destinatario'])
            if checked_cnpj is None:
                return False, f"Cnpj destinatario({record['nfe']['cnpj_destinatario']}) inválido."
            record['nfe']["cnpj_destinatario"] = checked_cnpj
        return True,None
