from .base_quali_checker import BaseQualiChecker
import re

class NumeroEditalChecker(BaseQualiChecker):
    check_name = "numero_edital"

    def check(self, record):
        if record["numero_edital"]not in ("indefinido","null",None): 
            numero_edital = re.sub(r'[a-zA-Z]', '', record["numero_edital"]).replace(' ','').replace("//","/").replace("-","/")
            if not re.match(r"^\d+/\d{2,4}$", numero_edital):
                return False,f"numero_edital ({numero_edital}) está fora do padrão."
            record["numero_edital"] = numero_edital
        return True,None
