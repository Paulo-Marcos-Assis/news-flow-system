from checkers.base_quali_checker import BaseQualiChecker

class TipoOperacaoChecker(BaseQualiChecker):
    check_name = "tipo_operacao"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "tipo_operacao" in record['nfe'].keys() and record['nfe']["tipo_operacao"] not in ("indefinido","null",None,""): 
            if record['nfe']["tipo_operacao"].lower() != "e" and record['nfe']["tipo_operacao"].lower() != "s":
                return False, f"Tipo operação ({record['nfe']['tipo_operacao']}) fora do padrao 'e' ou 's'"
        return True,None