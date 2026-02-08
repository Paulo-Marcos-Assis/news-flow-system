from utils.date_checker import DateChecker


class InidoneaDataPublicacaoChecker(DateChecker):
    check_name = "data_publicacao"
    table_name = "inidonea"

    def check(self, record):
        if "inidonea" in record and record["inidonea"].get("data_publicacao") not in ("indefinido", "null", None):
            date = record["inidonea"]["data_publicacao"]
            if not self.is_valid_date(date):
                return False, f"('inidonea') Data de publicação da inidoneidade ({date}) inválida."
            record["inidonea"]["data_publicacao"] = self.return_str_date(date)

        return True, None