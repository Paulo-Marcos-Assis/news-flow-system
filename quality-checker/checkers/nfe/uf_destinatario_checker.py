from utils.uf_checker import UfChecker

class UfDestinatarioChecker(UfChecker):
    check_name = "uf_destinatario"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "uf_destinatario" in record['nfe'].keys() and record['nfe']["uf_destinatario"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["uf_destinatario"],3):
                return False, f"Unidade federativa do Destinatário {record['nfe']['uf_destinatario']}) maior que o esperado."
            checked_uf = self.uf_acronym_check(record['nfe']["uf_destinatario"])
            if checked_uf is None:
                return False, f"Unidade federativa do Destinatário {record['nfe']['uf_destinatario']}) desconhecida."
            record['nfe']["uf_destinatario"] = checked_uf
        return True,None