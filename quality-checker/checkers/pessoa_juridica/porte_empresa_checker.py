from checkers.base_quali_checker import BaseQualiChecker


class PorteEmpresaChecker(BaseQualiChecker):
    check_name = "porte_empresa"
    table_name = "pessoa_juridica"

    def check(self, record):
        if "pessoa_juridica" in record and record['pessoa_juridica'].get("porte_empresa") not in ("indefinido", "null", None):
            porte_empresa = record['pessoa_juridica']['porte_empresa']
            if not self.is_valid_integer(porte_empresa):
                return False, f"('pessoa_juridica') O campo porte_empresa ({porte_empresa}) deve ser um valor inteiro."
            record['pessoa_juridica']['porte_empresa'] = int(porte_empresa)

        return True, None