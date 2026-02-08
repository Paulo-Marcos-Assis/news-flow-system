from utils.uf_checker import UfChecker

class UfEmitenteChecker(UfChecker):
    check_name = "uf_emitente"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "uf_emitente" in record['nfe'].keys() and record['nfe']["uf_emitente"] not in ("indefinido","null",None,""):
            if not self.is_varchar(record['nfe']["uf_emitente"],3):
                return False, f"Unidade federativa do Emitente {record['nfe']['uf_emitente']}) maior que o esperado."
            checked_uf = self.uf_acronym_check(record['nfe']["uf_emitente"])
            if checked_uf is None:
                return False, f"Unidade federativa do Emitente {record['nfe']['uf_emitente']}) desconhecida."
            record['nfe']["uf_emitente"] = checked_uf
        return True,None