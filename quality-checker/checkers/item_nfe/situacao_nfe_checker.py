from checkers.base_quali_checker import BaseQualiChecker


class SituacaoNfeChecker(BaseQualiChecker):
    check_name = "situacao_nfe"
    table_name = "item_licitacao"

    def check(self, record):
        if "item_nfe" in record.keys():
            for item in record['item_nfe']:
                if "situacao_nfe" in item.keys() and item["situacao_nfe"] not in ("indefinido","null",None,""):
                    if not self.is_valid_integer(item["situacao_nfe"]):
                        return False, f"Situação NFe ({item['situacao_nfe']}) não é do tipo integer."
        return True, None
