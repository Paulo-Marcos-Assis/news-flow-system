from checkers.base_quali_checker import BaseQualiChecker


class EstrangeiroChecker(BaseQualiChecker):
    check_name = "estrangeiro"
    table_name = "pessoa"

    def check(self, record):
        if "pessoa" in record and record['pessoa'].get("estrangeiro") not in ("indefinido", "null", None):
            if not self.is_bool(record['pessoa']['estrangeiro']):
                return False, f"('pessoa') O campo estrangeiro ({record['pessoa']['estrangeiro']}) deve ser um valor booleano."
            
        return True, None