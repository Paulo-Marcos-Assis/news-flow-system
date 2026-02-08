from utils.uf_checker import UfChecker


class NomeUfChecker(UfChecker):
    check_name = "nome_uf"
    table_name = "municipio"

    def check(self, record):
        if "municipio" in record.keys() and "nome_uf" in record['municipio'].keys() and record['municipio']["nome_uf"] not in ("indefinido", "null", None, ""):
            checked_uf = self.uf_name_check(record['municipio']['nome_uf'])
            if checked_uf is None:
                return False, f"Nome unidade federativa ({record['municipio']['nome_uf']}) desconhecido."
            if not self.uf_compare(checked_uf, record['municipio']['sigla_uf']):
                return False, f"Nome unidade federativa ({record['municipio']['nome_uf']}) diferente de sigla da unidade federativa ({record['municipio']['sigla_uf']})."
            record['municipio']['nome_uf'] = checked_uf
        return True, None