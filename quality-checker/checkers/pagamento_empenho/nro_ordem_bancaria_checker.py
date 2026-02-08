from checkers.base_quali_checker import BaseQualiChecker


class NroOrdemBancariaChecker(BaseQualiChecker):
    check_name = "nro_ordem_bancaria"
    table_name = "pagamento_empenho"

    def check(self, record):
        if "pagamento_empenho" in record and record['pagamento_empenho'].get("nro_ordem_bancaria") not in ("indefinido", "null", None):
            nro_ordem_bancaria = record['pagamento_empenho']["nro_ordem_bancaria"]
            # Remove field if it is 0
            if str(nro_ordem_bancaria).strip() in ('0', '0.0'):
                del record['pagamento_empenho']["nro_ordem_bancaria"]
                return True, None
            if not self.is_valid_integer(nro_ordem_bancaria):
                return False, f"('pagamento_empenho') Número da ordem bancária ({nro_ordem_bancaria}) inválido."
            record['pagamento_empenho']["nro_ordem_bancaria"] = int(nro_ordem_bancaria)

        return True, None