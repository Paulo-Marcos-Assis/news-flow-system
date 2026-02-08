from checkers.base_quali_checker import BaseQualiChecker

class InscSuframaDestinatarioChecker(BaseQualiChecker):
    check_name = "insc_suframa_destinatario"
    table_name = "tipo_licitacao"
    
    def check(self, record):
        if "nfe" in record.keys() and "insc_suframa_destinatario" in record['nfe'].keys() and record['nfe']["insc_suframa_destinatario"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["insc_suframa_destinatario"],30):
                return False, f"Inscrição Suframa do Destinatario({record['nfe']['insc_suframa_destinatario']}) fora do tamanho permitido."
        return True,None