from checkers.base_quali_checker import BaseQualiChecker

class CodMunEmitenteChecker(BaseQualiChecker):
    check_name = "cod_mun_emitente"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "cod_mun_emitente" in record['nfe'].keys() and record['nfe']["cod_mun_emitente"] not in ("indefinido","null",None,""):
            # Garante que o dado é String
            cod_str = str(record['nfe']['cod_mun_emitente'])
            if not cod_str.isdigit():
                return False, f"Código do município destinatário ({record['nfe']['cod_mun_emitente']}) inválido"
            record['nfe']['cod_mun_emitente'] = cod_str

        return True,None