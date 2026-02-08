from checkers.base_quali_checker import BaseQualiChecker
import re

class NumeroEditalChecker(BaseQualiChecker):
    check_name = "numero_edital"
    table_name = "processo_licitatorio"

    def check(self, record):
        if "processo_licitatorio" in record.keys() and 'numero_edital' in record['processo_licitatorio'].keys():
            # numero_edital = re.sub(r'[a-zA-Z]', '', record["processo_licitatorio"]["numero_edital"]).replace(' ','').replace("//","/").replace("-","/")
            # if not re.match(r"^\d+", numero_edital):
            #     return False,f"numero_edital ({numero_edital}) está fora do padrão."
            # record["processo_licitatorio"]["numero_edital"] = numero_edital
            if record["processo_licitatorio"]["numero_edital"] in ("indefinido","null",None):
                return False, f"numero_edital ({record['processo_licitatorio']['numero_edital']}) não pode ser nulo."
        return True, None
