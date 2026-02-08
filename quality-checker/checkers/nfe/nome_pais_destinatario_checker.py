from checkers.base_quali_checker import BaseQualiChecker

class NomePaisDestinatarioChecker(BaseQualiChecker):
    check_name = "nome_pais_destinatario"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "nome_pais_destinatario" in record['nfe'].keys() and record['nfe']["nome_pais_destinatario"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["nome_pais_destinatario"],100):
                return False, f"Nome do País Destinatário{record['nfe']['nome_pais_destinatario']}) fora do tamanho permitido."
        return True,None