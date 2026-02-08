from checkers.base_quali_checker import BaseQualiChecker

class NomeEmitenteChecker(BaseQualiChecker):
    check_name = "nome_emitente"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "nome_emitente" in record['nfe'].keys() and record['nfe']["nome_emitente"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["nome_emitente"],255):
                return False, f"Nome Emitente({record['nfe']['nome_emitente']}) fora do tamanho permitido."
        return True,None