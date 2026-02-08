from utils.date_checker import DateChecker


class DataNascimentoChecker(DateChecker):
    check_name = "data_nascimento"
    table_name = "pessoa_fisica"

    def check(self, record):
        if "pessoa_fisica" in record and record['pessoa_fisica'].get("data_nascimento") not in ("indefinido", "null", None):
            date = record['pessoa_fisica']['data_nascimento']
            if not self.is_valid_date(date):
                return False, f"('pessoa_fisica') Data de nascimento ({date}) inválida."
            record['pessoa_fisica']['data_nascimento'] = self.return_str_date(date)
        return True, None