from utils.cnpj_checker import CnpjChecker

class EstabelecimentoCnpjChecker(CnpjChecker):
    check_name = "cnpj"
    table_name = "estabelecimento"

    def check(self, record):
        if "estabelecimento" in record.keys() and "cnpj" in record['estabelecimento'].keys() and record['estabelecimento']['cnpj'] not in ("indefinido","null",None,""):

            if not "cnpj_ordem" in record['estabelecimento'].keys() or record['estabelecimento']['cnpj́_ordem'] in ("indefinido","null",None,""):
                return False, "('estabelecimento') CNPJ sem sua ordem"

            if not "cnpj_dv" in record['estabelecimento'].keys() or record['estabelecimento']['cnpj_dv'] in ("indefinido","null",None,""):
                return False, "('estabelecimento') CNPJ sem seu dígito verificador"

            full_cnpj = record['estabelecimento']['cnpj'] + record['estabelecimento']['cnpj́_ordem'] + record['estabelecimento']['cnpj']
            checked_cnpj = self.cnpj_check(full_cnpj)
            if checked_cnpj is None:
                return False, f"('estabelecimento') CNPJ ({full_cnpj}) inválido."
            record['estabelecimento']['cnpj'] = checked_cnpj

        return True,None
