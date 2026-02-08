from checkers.base_quali_checker import BaseQualiChecker

class NumeroDestinatarioChecker(BaseQualiChecker):
    check_name = "numero_destinatario"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "numero_destinatario" in record['nfe'].keys() and record['nfe']["numero_destinatario"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["numero_destinatario"],255):
                return False, f"Número do Destinatário{record['nfe']['numero_destinatario']}) fora do tamanho permitido."
        return True,None