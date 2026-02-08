from checkers.base_quali_checker import BaseQualiChecker


class FaixaEtariaChecker(BaseQualiChecker):
    check_name = "faixa_etaria"
    table_name = "pessoa_fisica"

    def check(self, record):
        if "pessoa_fisica" in record and record['pessoa_fisica'].get("faixa_etaria") not in ("indefinido", "null", None):
            faixa_etaria = record['pessoa_fisica']['faixa_etaria']
            if not self.is_varchar(faixa_etaria, 5):
                return False, f"('pessoa_fisica') Faixa_etaria ({faixa_etaria}) de tamanho inválido (bpchar 5)."
            record['pessoa_fisica']['faixa_etaria'] = str(faixa_etaria)

        return True, None