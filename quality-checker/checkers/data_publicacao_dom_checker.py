from .base_quali_checker import BaseQualiChecker

class DataPublicacaoDomChecker(BaseQualiChecker):
    check_name = "data_publicacao_dom"

    def check(self, record):
        if "data_publicacao_dom" in record.keys() and record["data_publicacao_dom"] not in ("indefinido","null",None,""): 
            if not self.is_valid_date(record["data_publicacao_dom"]):
                return False, f"Data da publicação no DOM ({record['data_publicacao_dom']}) inválida."
            record["data_publicacao_dom"] = self.format_date(record["data_publicacao_dom"])
        return True,None
