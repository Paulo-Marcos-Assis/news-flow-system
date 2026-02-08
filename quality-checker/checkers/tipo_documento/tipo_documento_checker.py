from checkers.base_quali_checker import BaseQualiChecker

class TipoDocumentoChecker(BaseQualiChecker):
    check_name = "descricao"
    table_name = "tipo_documento"

    def check(self, record):
        if "tipo_documento" in record.keys():
            types_to_check = record["tipo_documento"]
            if not isinstance(types_to_check, list):
                types_to_check = [types_to_check]

            for t in types_to_check:
                if isinstance(t, dict) and 'descricao' in t and t.get("descricao") not in ("indefinido", "null", None):
                    descricao = t['descricao']

                    success, rows, error, query = self.execute_db_query(
                        "SELECT id_tipo_documento, similarity(unaccent(%s), unaccent(descricao)) AS similaridade FROM public.tipo_documento WHERE similarity(unaccent(%s), unaccent(descricao)) >= 0.8 ORDER BY similaridade DESC LIMIT 1;",
                        params=(descricao, descricao)
                        )
                    
                    if not success:
                        return False, f"('tipo_documento') Erro ao consultar tabela 'tipo_documento': {error} | Query: {query}"
                    
                    if len(rows) != 0:          
                        best_match = rows[0]
                        record['tipo_documento'] = {"id_tipo_documento": best_match[0]}
                    else:
                        return False, f"('tipo_documento') Nenhuma correspondência encontrada para a descrição do tipo do documento: {descricao}"

        return True, None