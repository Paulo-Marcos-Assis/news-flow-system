from checkers.base_quali_checker import BaseQualiChecker

class NomeMunEmitenteChecker(BaseQualiChecker):
    check_name = "nome_mun_emitente"
    table_name = "tipo_licitacao"
    
    def check(self, record):
        if "nfe" in record.keys() and "nome_mun_emitente" in record['nfe'].keys() and record['nfe']["nome_mun_emitente"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["nome_mun_emitente"],255):
                return False, f"Nome do Município Emitente{record['nfe']['nome_mun_emitente']}) fora do tamanho permitido."
        return True,None