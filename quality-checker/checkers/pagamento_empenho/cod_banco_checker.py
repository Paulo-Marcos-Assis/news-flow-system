from checkers.base_quali_checker import BaseQualiChecker


class CodBancoChecker(BaseQualiChecker):
    check_name = "cod_banco"
    table_name = "pagamento_empenho"

    def check(self, record):
        if "pagamento_empenho" in record and record['pagamento_empenho'].get("cod_banco") not in ("indefinido", "null", None):
            cod_banco = record['pagamento_empenho']["cod_banco"]
            # Remove field if it is 0
            if str(cod_banco).strip() in ('0', '0.0'):
                del record['pagamento_empenho']["cod_banco"]
                return True, None
            if not self.is_valid_integer(cod_banco):
                return False, f"('pagamento_empenho') Código do banco pagador ({cod_banco}) inválido."
            record['pagamento_empenho']["cod_banco"] = int(cod_banco)

        return True, None