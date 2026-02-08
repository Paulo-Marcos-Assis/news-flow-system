from checkers.base_quali_checker import BaseQualiChecker

class TipoUGChecker(BaseQualiChecker):
    check_name = "descricao"
    table_name = "tipo_ug"

    def check(self, record):
        if "tipo_ug" in record.keys() and "descricao" in record['tipo_ug'].keys() and record["tipo_ug"]["descricao"] not in ("indefinido", "null", None):
            descricao = record['tipo_ug']['descricao']

            success, rows, error, query = self.execute_db_query(
                "SELECT id_tipo_ug, similarity(unaccent(%s), unaccent(descricao)) AS similaridade FROM public.tipo_ug WHERE similarity(unaccent(%s), unaccent(descricao)) >= 0.8 ORDER BY similaridade DESC LIMIT 1;",
                params=(descricao, descricao)
                )
            
            if not success:
                return False, f"('tipo_ug') Erro ao consultar tabela 'tipo_ug': {error} | Query: {query}"
            
            if len(rows) != 0:          
                best_match = rows[0]
                record['tipo_ug'] = {"id_tipo_ug": best_match[0]}
            else:
                return False, f"('tipo_ug') Nenhuma correspondência encontrada para a descrição do tipo da unidade gestora: {descricao}"

        return True, None