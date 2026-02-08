from utils.date_checker import DateChecker


class DataPublicacaoJustificativaChecker(DateChecker):
    check_name = "data_publicacao_justificativa"
    table_name = "pagamento_empenho"
    
    def check(self, record):
        if "pagamento_empenho" in record and record['pagamento_empenho'].get("data_publicacao_justificativa") not in ("indefinido", "null", None):
            date = record['pagamento_empenho']["data_publicacao_justificativa"]
            if not self.is_valid_date(date):
                return False, f"('pagamento_empenho') Data de publicação da justificativa do empenho ({date}) inválida."
            record['pagamento_empenho']["data_publicacao_justificativa"] = self.return_str_date(date)

        return True, None