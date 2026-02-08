from checkers.base_quali_checker import BaseQualiChecker
import re

class EmailChecker(BaseQualiChecker):
    check_name = "email"
    table_name = "estabelecimento"

    def check(self, record):
        if "estabelecimento" in record.keys() and "email" in record['estabelecimento'].keys() and record['estabelecimento']['email'] not in ("indefinido","null",None,""):
            if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", record['estabelecimento']['email']):
                return False, f"Email ({record['estabelecimento']['email']}) inválido."
        
        return True, None

