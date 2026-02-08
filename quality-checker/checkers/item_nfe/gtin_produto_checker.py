from checkers.base_quali_checker import BaseQualiChecker


class GtinProdutoChecker(BaseQualiChecker):
    check_name = "gtin_produto"
    table_name = "item_licitacao"

    def check(self, record):
        if "item_nfe" in record.keys():
            for item in record['item_nfe']:
                if "gtin_produto" in item.keys() and item["gtin_produto"] not in ("indefinido","null",None,""):
                    gtin_str = str(item['gtin_produto'])
                    if not gtin_str.isdigit():
                        return False, f"gtin produto ({item['gtin_produto']}) não contém apenas dígitos"
                    item['gtin_produto'] = gtin_str

        return True,None