from utils.date_checker import DateChecker


class DataEmpenhoChecker(DateChecker):
    check_name = "data_empenho"
    table_name = "empenho"

    def check(self, record):
        if "empenho" in record and record["empenho"].get("data_empenho") not in ("indefinido", "null", None):
            date = record["empenho"]["data_empenho"]
            if not self.is_valid_date(date):
                return False, f"('empenho') Data do empenho ({date}) inválida."
            record["empenho"]["data_empenho"] = self.return_str_date(date)

        return True, None