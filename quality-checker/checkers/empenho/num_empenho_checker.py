from checkers.base_quali_checker import BaseQualiChecker


class NumEmpenhoChecker(BaseQualiChecker):
    check_name = "num_empenho"
    table_name = "empenho"

    def check(self, record):
        if "empenho" in record and record["empenho"].get("num_empenho") not in ("indefinido", "null", None):
            num_empenho = record["empenho"]["num_empenho"]
            if not self.is_valid_bigint(num_empenho):
                return False, f"('empenho') Número do empenho ({num_empenho}) inválido."
            record["empenho"]["num_empenho"] = int(num_empenho)

        return True, None