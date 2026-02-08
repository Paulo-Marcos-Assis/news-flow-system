from checkers.base_quali_checker import BaseQualiChecker


class PrestacaoContasChecker(BaseQualiChecker):
    check_name = "prestacao_contas"
    table_name = "empenho"

    def check(self, record):
        if "empenho" in record and record["empenho"].get("prestacao_contas") not in ("indefinido", "null", None):
            if not self.is_bool(record["empenho"]["prestacao_contas"]):
                return False, f"('empenho') Prestação de contas ({record['empenho']['prestacao_contas']}) inválida (deve ser booleano)."

        return True, None