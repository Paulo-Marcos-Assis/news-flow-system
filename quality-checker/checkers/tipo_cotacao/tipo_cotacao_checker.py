from checkers.base_quali_checker import BaseQualiChecker


class TipoCotacaoDescricaoChecker(BaseQualiChecker):
    check_name = "descricao"
    table_name = "tipo_cotacao"

    def check(self, record):
        if "tipo_cotacao" in record.keys() and "descricao" in record['tipo_cotacao'].keys() and record["tipo_cotacao"]["descricao"] not in ("indefinido", "null", None):
            descricao = record['tipo_cotacao']['descricao']

            success, rows, error, query = self.execute_db_query(
                "SELECT id_tipo_cotacao, similarity(unaccent(%s), unaccent(descricao)) AS similaridade FROM public.tipo_cotacao WHERE similarity(unaccent(%s), unaccent(descricao)) >= 0.8 ORDER BY similaridade DESC LIMIT 1;",
                params=(descricao, descricao)
                )
            
            if not success:
                return False, f"('tipo_cotacao') Erro ao consultar tabela 'tipo_cotacao': {error} | Query: {query}"
            
            if len(rows) != 0:
                best_match = rows[0]
                self.logger.info(f"('tipo_cotacao') Encontrada correspondência para a descrição do tipo da cotação: id{best_match[0]} - {descricao}")          
                record['tipo_cotacao'] = {"id_tipo_cotacao": best_match[0]}
            else:
                return False, f"('tipo_cotacao') Nenhuma correspondência encontrada para a descrição do tipo da cotação: {descricao}"

        return True, None