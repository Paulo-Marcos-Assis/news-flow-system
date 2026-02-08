from checkers.base_quali_checker import BaseQualiChecker

class CnaeEmitenteChecker(BaseQualiChecker):
    check_name = "cnae_emitente"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "cnae_emitente" in record['nfe'].keys() and record['nfe']["cnae_emitente"] not in ("indefinido","null",None,""): 
            if not self.is_valid_integer(record['nfe']["cnae_emitente"]):
                return False, f"Cnae Emitente ({record['nfe']['cnae_emitente']}) inválido."
        return True,None