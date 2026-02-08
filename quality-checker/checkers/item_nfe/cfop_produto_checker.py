from checkers.base_quali_checker import BaseQualiChecker


class CfopProdutoChecker(BaseQualiChecker):
    check_name = "cfop_produto"
    table_name = "item_nfe"

    def check(self, record):
        if "item_nfe" in record.keys():
            for item in record['item_nfe']:
                if "cfop_produto" in item.keys() and item["cfop_produto"] not in ("indefinido","null",None,""):
                    cfop_str = str(item['cfop_produto'])
                    if not cfop_str.isdigit():
                        return False, f"CFOP do produto ({item['cfop_produto']}) Não contém apenas dígitos"
                    item['cfop_produto'] = cfop_str

        return True,None
