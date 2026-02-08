from checkers.base_quali_checker import BaseQualiChecker


class CnaeDescricaoChecker(BaseQualiChecker):
    check_name = "descricao"
    table_name = "cnae"

    def check(self, record):
        if "cnae" in record.keys() and "descricao" in record['cnae'].keys() and record["cnae"]["descricao"] not in ("indefinido", "null", None):
            descricao = record['cnae']['descricao']

            success, rows, error, query = self.execute_db_query(
                "SELECT id_cnae, similarity(unaccent(%s), unaccent(descricao)) AS similaridade FROM public.cnae WHERE similarity(unaccent(%s), unaccent(descricao)) >= 0.8 ORDER BY similaridade DESC LIMIT 1;",
                params=(descricao, descricao)
                )
            
            if not success:
                return False, f"('cnae') Erro ao consultar tabela 'cnae': {error} | Query: {query}"
            
            if len(rows) != 0:          
                best_match = rows[0]
                record['cnae'] = {"id_cnae": best_match[0]}
            else:
                return False, f"('cnae') Nenhuma correspondência encontrada para a descrição CNAE: {descricao}"

        return True, None