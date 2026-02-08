from checkers.base_quali_checker import BaseQualiChecker

class CodMunDestinatarioChecker(BaseQualiChecker):
    check_name = "cod_mun_destinatario"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "cod_mun_destinatario" in record['nfe'].keys() and record['nfe']["cod_mun_destinatario"] not in ("indefinido","null",None,""):
            # Garante que o dado é String
            cod_str = str(record['nfe']['cod_mun_destinatario'])
            if not cod_str.isdigit():
                return False, f"Código do município destinatário ({record['nfe']['cod_mun_destinatario']}) inválido"
            record['nfe']['cod_mun_destinatario'] = cod_str
            
        return True,None