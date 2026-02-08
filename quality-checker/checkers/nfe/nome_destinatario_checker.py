from checkers.base_quali_checker import BaseQualiChecker

class NomeDestinatarioChecker(BaseQualiChecker):
    check_name = "nome_destinatario"
    table_name = "tipo_licitacao"
    
    def check(self, record):
        if "nfe" in record.keys() and "nome_destinatario" in record['nfe'].keys() and record['nfe']["nome_destinatario"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["nome_destinatario"],255):
                return False, f"Nome Destinatário({record['nfe']['nome_destinatario']}) fora do tamanho permitido."
        return True,None