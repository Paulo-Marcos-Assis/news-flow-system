from checkers.base_quali_checker import BaseQualiChecker

class NomeMunDestinatarioChecker(BaseQualiChecker):
    check_name = "nome_mun_destinatario"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "nome_mun_destinatario" in record['nfe'].keys() and record['nfe']["nome_mun_destinatario"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["nome_mun_destinatario"],255):
                return False, f"Nome do Município Destinatário {record['nfe']['nome_mun_destinatario']}) fora do tamanho permitido."
        return True,None