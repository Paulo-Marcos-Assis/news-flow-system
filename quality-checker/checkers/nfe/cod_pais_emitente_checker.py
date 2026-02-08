from checkers.base_quali_checker import BaseQualiChecker

class CodPaisEmitenteChecker(BaseQualiChecker):
    check_name = "cod_pais_emitente"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "cod_pais_emitente" in record['nfe'].keys() and record['nfe']["cod_pais_emitente"] not in ("indefinido","null",None,""):
            # Garante que o dado é String
            cod_str = str(record['nfe']['cod_pais_emitente'])
            if not cod_str.isdigit():
                return False, f"Código do país emitente ({record['nfe']['cod_pais_emitente']}) inválido"

        return True,None