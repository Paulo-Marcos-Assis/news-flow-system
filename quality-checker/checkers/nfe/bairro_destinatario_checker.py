from checkers.base_quali_checker import BaseQualiChecker

class BairroDestinatarioChecker(BaseQualiChecker):
    check_name = "bairro_destinatario"
    table_name = "nfe"

    def check(self, record):
        if "nfe" in record.keys() and "bairro_destinatario" in record['nfe'].keys() and record['nfe']["bairro_destinatario"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["bairro_destinatario"], 255):
                return False, f"Bairro Destinatario({record['nfe']['bairro_destinatario']}) fora do tamanho permitido."
        return True,None