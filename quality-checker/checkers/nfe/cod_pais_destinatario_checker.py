from checkers.base_quali_checker import BaseQualiChecker

class CodPaisDestinatarioChecker(BaseQualiChecker):
    check_name = "cod_pais_destinatario"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "cod_pais_destinatario" in record['nfe'].keys() and record['nfe']["cod_pais_destinatario"] not in ("indefinido","null",None,""):
            # Garante que o dado é String
            cod_str = str(record['nfe']['cod_pais_destinatario'])
            if not cod_str.isdigit():
                return False, f"Código do país destinatário ({record['nfe']['cod_pais_destinatario']}) inválido"
            
        return True,None