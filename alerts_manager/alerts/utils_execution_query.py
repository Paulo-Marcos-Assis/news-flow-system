import psycopg2
from psycopg2 import sql

from typing import Any
from service_essentials.exceptions.fail_queue_exception import FailQueueException

class UtilsExecutionQuery:

    ALLOWED_OPERATIONS = {
        'LIKE': sql.SQL('LIKE'),
        'ILIKE': sql.SQL('ILIKE'),
        '=': sql.SQL('='),
        '>': sql.SQL('>'),
        '<': sql.SQL('<'),
        '>=': sql.SQL('>='),
        '<=': sql.SQL('<='),
        '+': sql.SQL('+'),
        '-': sql.SQL('-'),
        '/': sql.SQL('/'),
        '*': sql.SQL('*'),
        "IN": sql.SQL('IN'),
        "NOT_IN": sql.SQL('NOT IN'),
        "IS_NOT": sql.SQL('IS NOT')
    }

    ALLOWED_FUNCTIONS = {
        'COUNT': sql.SQL('COUNT ({})'),
        'COUNT_DISTINCT': sql.SQL('COUNT(DISTINCT {})'),
        'SUM': sql.SQL('SUM({})')
    }

    @staticmethod
    def validate_execution_alerta(metodo_analise: dict[str, Any], objetos_analise: dict[str, Any]) -> sql.Composed:

        valores_objetos_analise = ["unidade_gestora", "ente", "item_nfe", "documento", "item_licitacao", "pessoa", "processo_licitatorio"]

        if not set(objetos_analise.keys()).intersection(set(valores_objetos_analise)):
            raise FailQueueException(f"Os objetos de análise são inválidos.")

        where = [
            sql.SQL("ma.id_metodo_analise = {}").format(sql.Literal(metodo_analise['id_metodo_analise'])),
            sql.SQL("ma.versao = {}").format(sql.Literal(metodo_analise['versao']))
        ]

        for obj in objetos_analise:
            if obj in valores_objetos_analise:
                coluna_objeto = f"id_{obj}"
                where.append(sql.SQL("oa.{} = {}").format(sql.Identifier(coluna_objeto), sql.Literal(objetos_analise[obj])))

        query_alerta = sql.SQL(
            """
            SELECT
                a.id_alerta
            FROM
                alerta a
                    join execucao_metodo em on em.id_execucao_metodo = a.id_execucao_metodo
                    join metodo_analise ma on ma.id_metodo_analise = em.id_metodo_analise
                    join execucao_metodo_objeto_analise emoa on emoa.id_execucao_metodo = em.id_execucao_metodo
                    join objeto_analise oa on oa.id_objeto_analise = emoa.id_objeto_analise
            WHERE
                {where}
            """).format(
            where=sql.SQL(" AND ").join(where),
        )

        return query_alerta

    @staticmethod
    def get_simple_query(query_config: dict[str, Any], objetos_analise: dict[str, Any]) -> sql.Composed:

        query = query_config['query']
        tables = query['tables']

        subquery = None
        if 'subquery' in query_config:
            subquery = {'query': query_config['subquery']}

        fields = []

        where = []
        joins = []

        group_by = []
        having = []

        # SELECT
        for tb, tf in query['select'].items():
            if tb == 'calc_diff_dates':
                tb1 = tables[query['select']['calc_diff_dates']['field1']['table']]
                fd1 = query['select']['calc_diff_dates']['field1']['field']

                tb2 = tables[query['select']['calc_diff_dates']['field2']['table']]
                fd2 = query['select']['calc_diff_dates']['field2']['field']

                dates_diff = sql.SQL("date_part('year', age({}, {}))*12 + ").format(sql.Identifier(tb1, fd1), sql.Identifier(tb2, fd2))
                dates_diff += sql.SQL("date_part('month', age({}, {})) as diferenca ").format(sql.Identifier(tb1, fd1), sql.Identifier(tb2, fd2))

                fields.append(dates_diff)
            else:
                tb_alias = tables[tb]

                for f in tf:
                    field = sql.Identifier(tb_alias, f)
                    fields.append(field)

                    if 'group_by' in query:
                        group_by.append(field)

        # FROM
        if query['from'] != 'subquery':
            main_table = sql.SQL("{} {}").format(sql.Identifier(query['from']), sql.Identifier(tables[query['from']]))

            # WHERE
            for obj in objetos_analise:
                pk_obj = f"id_{obj}"
                where.append(sql.SQL("{} = {}").format(sql.Identifier(tables[obj], pk_obj), sql.Literal(objetos_analise[obj])))
        else:
            main_table = UtilsExecutionQuery.get_simple_query(subquery, objetos_analise)

        if 'join' in query:
            for j in query['join']:
                joins.append(sql.SQL("{} {} ON {} = {} ").format(sql.Identifier(j['left_table']), sql.Identifier(tables[j['left_table']]),
                                                                 sql.Identifier(tables[j['left_table']], j['left_on']),
                                                                 sql.Identifier(tables[j['right_table']], j['right_on'])))

        if 'where' in query:
            for w in query['where']:
                operation = UtilsExecutionQuery.ALLOWED_OPERATIONS[w['operation']]

                if operation:
                    if 'math_op' in w:
                        math_operation = UtilsExecutionQuery.ALLOWED_OPERATIONS[w['math_op']['op']]

                        field1 = sql.Identifier(tables[w['table']], w['math_op']['field1']) + sql.SQL("::numeric")
                        field2 = sql.SQL("NULLIF ({}, 0)").format(sql.Identifier(tables[w['table']], w['math_op']['field2']))
                        value = sql.Literal(w['value'])

                        where.append(sql.SQL("{} {} {} {} {}").format(field1, math_operation, field2, operation, value))
                    else:
                        if w['operation'] == 'IN' or w['operation'] == 'NOT_IN':
                            value = []

                            for v in w['value']:
                                value.append(sql.Literal(v))

                            where.append(sql.SQL("{} {} ({})").format(sql.Identifier(tables[w['table']], w['field']), operation, sql.SQL(", ").join(value)))
                        else:
                            where.append(sql.SQL("{} {} {}").format(sql.Identifier(tables[w['table']], w['field']), operation, sql.Literal(w['value'])))
                else:
                    raise FailQueueException(f"Operação SQL (WHERE) inválida.")

        # GROUP_BY
        if 'group_by' in query:
            for group in query['group_by']:
                function = UtilsExecutionQuery.ALLOWED_FUNCTIONS[group['group_field']['function']]

                if function:
                    group_field = function.format(
                        sql.Identifier(tables[group['group_field']['table']], group['group_field']['field']))

                    if 'filtering' in group:
                        table = tables[group['filtering']['table']]
                        fld = group['filtering']['field']
                        ftr = UtilsExecutionQuery.ALLOWED_OPERATIONS[group['filtering']['filter']]
                        vle = group['filtering']['value']

                        group_field += sql.SQL(" filter (where {} {} {})").format(sql.Identifier(table, fld), ftr, sql.Literal(vle))

                    fields.append(group_field + sql.SQL(" as {}").format(sql.Identifier(group['group_field']['col_alias'])))

                    if 'having' in group:
                        having_operation = UtilsExecutionQuery.ALLOWED_OPERATIONS[group['having']['operation']]

                        if having_operation:
                            having.append(group_field + sql.SQL(" {} {}").format(having_operation, sql.Literal(group['having']['value'])))
                        else:
                            raise FailQueueException(f"Operação SQL (HAVING) inválida.")
                else:
                    raise FailQueueException(f"Função SQL (GROUP_BY) inválida.")

        if not fields or not main_table or not where:
            raise FailQueueException(f"Erro de formatação da query")

        from_table = "({table}) as sq" if query['from'] == 'subquery' else "{table}"

        formatted_query = sql.SQL("SELECT {fields}").format(fields=sql.SQL(", ").join(fields))
        formatted_query += sql.SQL(" FROM " + from_table).format(table=main_table)

        if joins:
            formatted_query += sql.SQL(" JOIN {join}").format(join=sql.SQL("JOIN ").join(joins))

        formatted_query += sql.SQL(" WHERE {where}").format(where=sql.SQL(" AND ").join(where))

        if group_by:
            formatted_query += sql.SQL(" GROUP BY {group_by}").format(group_by=sql.SQL(", ").join(group_by))

        if having:
            formatted_query += sql.SQL(" HAVING {having}").format(having=sql.SQL(" AND ").join(having))

        return formatted_query