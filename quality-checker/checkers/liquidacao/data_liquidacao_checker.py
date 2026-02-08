from utils.date_checker import DateChecker


class DataLiquidacaoChecker(DateChecker):
    check_name = "data_liquidacao"
    table_name = "liquidacao"

    def check(self, record):
        if "liquidacao" in record and record["liquidacao"].get("data_liquidacao") not in ("indefinido", "null", None):
            if not self.is_valid_date(record["liquidacao"]["data_liquidacao"]):
                return False, f"('liquidacao') Data de liquidação ({record['liquidacao']['data_liquidacao']}) inválida."
            record["liquidacao"]["data_liquidacao"] = self.return_str_date(record["liquidacao"]["data_liquidacao"])

        return True, None