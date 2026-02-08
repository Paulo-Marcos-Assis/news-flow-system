from checkers.base_quali_checker import BaseQualiChecker


class RegularizacaoOrcamentariaChecker(BaseQualiChecker):
    check_name = "regularizacao_orcamentaria"
    table_name = "empenho"

    def check(self, record):
        if "empenho" in record and record["empenho"].get("regularizacao_orcamentaria") not in ("indefinido", "null", None):
            if not self.is_bool(record["empenho"]["regularizacao_orcamentaria"]):
                return False, f"('empenho') Regularização orçamentária ({record['empenho']['regularizacao_orcamentaria']}) inválida (deve ser booleano)."

        return True, None