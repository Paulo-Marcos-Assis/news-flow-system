from utils.date_checker import DateChecker


class DataAssinaturaChecker(DateChecker):
    check_name = "data_assinatura"
    table_name = "contrato"

    def check(self, record):
        if "contrato" in record and record["contrato"].get("data_assinatura") not in ("indefinido", "null", None):
            date = record["contrato"]["data_assinatura"]
            if not self.is_valid_date(date):
                return False, f"('contrato') Data de assinatura ({record['contrato']['data_assinatura']}) inválida."
            record["contrato"]["data_assinatura"] = self.return_str_date(date)

        return True, None