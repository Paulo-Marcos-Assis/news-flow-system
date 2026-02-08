from checkers.base_quali_checker import BaseQualiChecker


class CodAgenciaChecker(BaseQualiChecker):
    check_name = "cod_agencia"
    table_name = "pagamento_empenho"

    def check(self, record):
        if "pagamento_empenho" in record and record['pagamento_empenho'].get("cod_agencia") not in ("indefinido", "null", None):
            cod_agencia = record['pagamento_empenho']["cod_agencia"]
            # Remove field if it is 0
            if str(cod_agencia).strip() in ('0', '0.0'):
                del record['pagamento_empenho']["cod_agencia"]
                return True, None
            if not self.is_valid_integer(cod_agencia):
                return False, f"('pagamento_empenho') Código da agência bancária pagadora ({cod_agencia}) inválido."
            record['pagamento_empenho']["cod_agencia"] = int(cod_agencia)

        return True, None