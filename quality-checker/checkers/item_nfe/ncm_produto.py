from checkers.base_quali_checker import BaseQualiChecker


class NcmProdutoChecker(BaseQualiChecker):
    check_name = "ncm_produto"
    table_name = "item_licitacao"

    def check(self, record):
        if "item_nfe" in record.keys():
            for item in record['item_nfe']:
                if "ncm_produto" in item.keys() and item["ncm_produto"] not in ("indefinido","null",None,""):
                    ncm_str = str(item['ncm_produto'])
                    if not ncm_str.isdigit():
                        return False, f"NCM do produto ({item['ncm_produto']}) não contém apenas dígitos"
                    item['ncm_produto'] = ncm_str

        return True,None
