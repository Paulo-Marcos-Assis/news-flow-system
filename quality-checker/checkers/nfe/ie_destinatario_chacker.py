from checkers.base_quali_checker import BaseQualiChecker

class IeDestinatarioChecker(BaseQualiChecker):
    check_name = "ie_destinatario"
    table_name = "tipo_licitacao"
    
    def check(self, record):
        if "nfe" in record.keys() and "ie_destinatario" in record['nfe'].keys() and record['nfe']["ie_destinatario"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["ie_destinatario"],255):
                return False, f"Inscrição Estadual do destinatário({record['nfe']['ie_destinatario']}) fora do tamanho permitido."
        return True,None