from utils.date_checker import DateChecker


class InidoneaDataValidadeChecker(DateChecker):
    check_name = "data_validade"
    table_name = "inidonea"

    def check(self, record):
        if "inidonea" in record and record["inidonea"].get("data_validade") not in ("indefinido", "null", None):
            date = record["inidonea"]["data_validade"]
            if not self.is_valid_date(date, allow_future_date=True):
                return False, f"('inidonea') Data de término da inidoneidade ({date}) inválida."
            record["inidonea"]["data_validade"] = self.return_str_date(date, allow_future_date=True)

        return True, None