from utils.cnpj_checker import CnpjChecker


class PessoaJuridicaCnpjChecker(CnpjChecker):
    check_name = "cnpj"
    table_name = "pessoa_juridica"

    def check(self, record):
        if "pessoa_juridica" in record and record['pessoa_juridica'].get("cnpj") not in ("indefinido", "null", None):
            checked_cnpj = self.cnpj_check(record['pessoa_juridica']['cnpj'])
            if checked_cnpj is None:
                return False, f"('pessoa_juridica') CNPJ ({record['pessoa_juridica']['cnpj']}) inválido."
            if not self.is_varchar(checked_cnpj, 20):
                return False, f"('pessoa_juridica') CNPJ ({checked_cnpj}) fora do limite (varchar 20)."
            record['pessoa_juridica']['cnpj'] = checked_cnpj
        return True, None