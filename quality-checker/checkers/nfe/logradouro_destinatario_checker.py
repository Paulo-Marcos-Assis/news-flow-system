from checkers.base_quali_checker import BaseQualiChecker

class LogradouroDestinatarioChecker(BaseQualiChecker):
    check_name = "logradouro_destinatario"
    table_name = "tipo_licitacao"
    
    def check(self, record):
        if "nfe" in record.keys() and "logradouro_destinatario" in record['nfe'].keys() and record['nfe']["logradouro_destinatario"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["logradouro_destinatario"],255):
                return False, f"Logradouro Destinatario({record['nfe']['logradouro_destinatario']}) fora do tamanho permitido."
        return True,None