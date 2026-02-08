from utils.date_checker import DateChecker, MAX_FUTURE_YEARS


class DataVencimentoChecker(DateChecker):
    check_name = "data_vencimento"
    table_name = "contrato"

    def check(self, record):
        if "contrato" in record and record["contrato"].get("data_vencimento") not in ("indefinido", "null", None):
            date = record["contrato"]["data_vencimento"]
            reference_date = record["contrato"].get("data_assinatura")
            
            # Verifica se a data de vencimento do contrato é no máximo 30 anos após a data de assinatura - alguns contratos de concessão têm essa característica
            if not self.is_valid_date(date, allow_future_date=True, max_future_years=MAX_FUTURE_YEARS, reference_date=reference_date):
                return False, f"('contrato') Data de vencimento ({record['contrato']['data_vencimento']}) inválida."
            record["contrato"]["data_vencimento"] = self.return_str_date(date, allow_future_date=True, max_future_years=MAX_FUTURE_YEARS, reference_date=reference_date)

        return True, None