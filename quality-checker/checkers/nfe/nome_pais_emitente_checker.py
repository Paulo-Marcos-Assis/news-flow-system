from checkers.base_quali_checker import BaseQualiChecker

class NomePaisEmitenteChecker(BaseQualiChecker):
    check_name = "nome_pais_emitente"
    table_name = "tipo_licitacao"
    
    def check(self, record):
        if "nfe" in record.keys() and "nome_pais_emitente" in record['nfe'].keys() and record['nfe']["nome_pais_emitente"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["nome_pais_emitente"],55):
                return False, f"Nome do País Emitente {record['nfe']['nome_pais_emitente']}) fora do tamanho permitido."
        return True,None