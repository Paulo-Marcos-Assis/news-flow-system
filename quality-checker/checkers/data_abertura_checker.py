from .base_quali_checker import BaseQualiChecker

class DataAberturaDomChecker(BaseQualiChecker):
    check_name = "data_abertura"

    def check(self, record):
        if "data_abertura" in record.keys() and record["data_abertura"] not in ("indefinido","null",None,""): 
            if not self.is_valid_date(record["data_abertura"]):
                return False, f"Data de abertura ({record['data_abertura']}) inválida."
            record["data_abertura"] = self.format_date(record["data_abertura"])
        return True,None
