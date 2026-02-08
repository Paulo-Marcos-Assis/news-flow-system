from utils.uf_checker import UfChecker


class SiglaUfChecker(UfChecker):
    check_name = "sigla_uf"
    table_name = "municipio"

    def check(self, record):
        if "municipio" in record.keys() and "sigla_uf" in record['municipio'].keys() and record['municipio']["sigla_uf"] not in ("indefinido", "null", None, ""):
            checked_uf = self.uf_acronym_check(record['municipio']['sigla_uf'])
            if checked_uf is None:
                return False, f"Sigla unidade federativa ({record['municipio']['sigla_uf']}) desconhecida."
            record['municipio']['sigla_uf'] = checked_uf
        return True, None