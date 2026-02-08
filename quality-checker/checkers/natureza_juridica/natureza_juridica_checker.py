from checkers.base_quali_checker import BaseQualiChecker


class NaturezaJuridicaChecker(BaseQualiChecker):
    check_name = "descricao"
    table_name = "natureza_juridica"

    def check(self, record):
        if "natureza_juridica" in record.keys() and "descricao" in record['natureza_juridica'].keys() and record["natureza_juridica"]["descricao"] not in ("indefinido", "null", None):
            descricao = record['natureza_juridica']['descricao']

            success, rows, error, query = self.execute_db_query(
                "SELECT id_natureza_juridica, similarity(unaccent(%s), unaccent(descricao)) AS similaridade FROM public.natureza_juridica WHERE similarity(unaccent(%s), unaccent(descricao)) >= 0.8 ORDER BY similaridade DESC LIMIT 1;",
                params=(descricao, descricao)
                )
            
            if not success:
                return False, f"('natureza_juridica') Erro ao consultar tabela 'natureza_juridica': {error} | Query: {query}"
            
            if len(rows) != 0:          
                best_match = rows[0]
                record['natureza_juridica'] = {"id_natureza_juridica": best_match[0]}
            else:
                return False, f"('natureza_juridica') Nenhuma correspondência encontrada para a descrição da natureza jurídica: {descricao}"

        return True, None