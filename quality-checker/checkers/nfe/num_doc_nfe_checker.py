from checkers.base_quali_checker import BaseQualiChecker

class NumDocNfeChecker(BaseQualiChecker):
    check_name = "num_doc_nfe"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "num_doc_nfe" in record['nfe'].keys() and record['nfe']["num_doc_nfe"] not in ("indefinido","null",None,""):
            if not self.is_valid_integer(record['nfe']['num_doc_nfe']):
                return False, f"Número documento NFe ({record['nfe']['num_doc_nfe']}) inválida"
            
        return True,None