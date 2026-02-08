from utils.value_checker import ValueChecker


class CapitalSocialChecker(ValueChecker):
    check_name = "capital_social"
    table_name = "pessoa_juridica"

    def check(self, record):
        if "pessoa_juridica" in record and record['pessoa_juridica'].get("capital_social") not in ("indefinido", "null", None):
            capital_social = record['pessoa_juridica']['capital_social']
            if not self.value_check(capital_social):
                return False, f"('pessoa_juridica') O campo capital_social ({capital_social}) inválido"
            record['pessoa_juridica']['capital_social'] = float(self.normalize_value(capital_social))
        return True, None