from checkers.base_quali_checker import BaseQualiChecker

class BairroEmitenteChecker(BaseQualiChecker):
    check_name = "bairro_emitente"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "bairro_emitente" in record['nfe'].keys() and record['nfe']["bairro_emitente"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["bairro_emitente"],255):
                return False, f"Bairro Emitente ({record['nfe']['bairro_emitente']}) fora do tamanho permitido."
        return True,None