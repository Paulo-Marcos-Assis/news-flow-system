import json
import os
import sys

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service_essentials.queue_manager.queue_manager_factory import QueueManagerFactory

from service_essentials.utils.logger import Logger

output_queue = "alerts_manager"

# DB_CONFIG = {
#     "dbname": os.getenv("DATABASE_PG"),
#     "user": os.getenv("USERNAME_PG"),
#     "password": os.getenv("SENHA_PG"),
#     "host": "localhost",# os.getenv("HOST_PG"),
#     "port": 5433 # os.getenv("PORT_PG")
# }

# print(DB_CONFIG.get('dbname'))
# print(DB_CONFIG.get('user'))
# print(DB_CONFIG.get('password'))
# print(DB_CONFIG.get('host'))
# print(DB_CONFIG.get('port'))

DB_CONFIG = {
    "dbname": "local",
    "user": "admin",
    "password": "admin",
    "host": "localhost",
    "port": "5433"
}

pg_connection = None

"""Metodo para criar e armazenar a conexão com o PostgreSQL."""
try:
    print("Conectando ao banco de dados PostgreSQL...")
    pg_connection = psycopg2.connect(**DB_CONFIG)
    print("Conexão com o PostgreSQL estabelecida com sucesso.")
except psycopg2.Error as e:
    print(f"Falha ao conectar com o PostgreSQL na inicialização: {e}")
    pg_connection = None
    sys.exit(1)


def load_alerta_noticias_municipio():
    query = sql.SQL(
        """
            SELECT n.id_noticia, n.id_municipio
            FROM noticia_municipio n
        """
    )
    cursor.execute(query)
    result = cursor.fetchall()
    alerts_execute = []
    for r in result:
        alert = {
            "routing_key": "insert.*",
            "ids_gerados_db": {
                "data": {
                    "insert": {
                        "noticia_municipio": {
                            r['id_noticia'],
                            r['id_municipio']
                        }
                    },
                    "update": {}
                },
                "inserted_ids": {}
            }
        }
        alerts_execute.append(alert)
    return alerts_execute


def load_alerta_noticias_processo_licitatorio():
    query = sql.SQL(
        """
            SELECT id_noticia FROM noticia
            WHERE id_processo_licitatorio IS NOT NULL
        """
    )
    cursor.execute(query)
    result = cursor.fetchall()
    alerts_execute = []
    for r in result:
        alert = {
            "routing_key": "insert.*",
            "ids_gerados_db": {
                "data": {
                    "insert": {
                        "noticia": r['id_noticia']
                    },
                    "update": {}
                },
                "inserted_ids": {}
            }
        }
        alerts_execute.append(alert)
    return alerts_execute


def load_alerta_valor_previsto_contratado():
    query = sql.SQL(
        """
            SELECT
               c.id_processo_licitatorio
            FROM contrato c
            JOIN processo_licitatorio pl ON pl.id_processo_licitatorio = c.id_processo_licitatorio
            GROUP BY pl.valor_total_previsto,
                 c.id_processo_licitatorio
            HAVING (SUM(c.valor_contrato) - pl.valor_total_previsto)/ NULLIF(pl.valor_total_previsto, 0) >= 0.1
        """
    )
    cursor.execute(query)
    result = cursor.fetchall()
    alerts_execute = []
    for r in result:
        alert = {
            "routing_key": "insert.*",
            "ids_gerados_db": {
                "data": {
                    "insert": {
                        "processo_licitatorio": r['id_processo_licitatorio']
                    },
                    "update": {}
                },
                "inserted_ids": {}
            }
        }
        alerts_execute.append(alert)
    return alerts_execute


def load_alerta_vencedor_contumaz():
    query = sql.SQL(
        """
            SELECT
            	MIN(id_cotacao) AS id_cotacao
            FROM cotacao c
            WHERE c.id_pessoa IN (
            	SELECT sq.id_pessoa
            	FROM
            		(
            		SELECT p.id_pessoa,
            			COUNT (cot.id_cotacao) AS lances,
            			COUNT (cot.id_cotacao) filter (WHERE cot.vencedor = TRUE) AS vitorias
            		FROM
            			processo_licitatorio pl
            		JOIN item_licitacao il
            			ON il.id_processo_licitatorio = pl.id_processo_licitatorio
            		JOIN cotacao cot
            			ON cot.id_item_licitacao = il.id_item_licitacao
            		JOIN pessoa p
            			ON p.id_pessoa = cot.id_pessoa
            		JOIN modalidade_licitacao ml
            			ON ml.id_modalidade_licitacao = pl.id_modalidade_licitacao
            		WHERE
            			ml.descricao NOT IN ('Dispensa de Licitação', 'Inexigibilidade de Licitação', 'Regime Diferenciado de Contratação', 'Procedimento Licitatório Lei 13.303/06', 'Outras')
            		GROUP BY p.id_pessoa
            		HAVING COUNT (cot.id_cotacao) >= 10
            		) AS sq
            	WHERE sq.vitorias::numeric / NULLIF (sq.lances, 0) > 0.9
            	)
            GROUP BY c.id_pessoa
        """
    )
    cursor.execute(query)
    result = cursor.fetchall()
    alerts_execute = []
    for r in result:
        alert = {
            "routing_key": "insert.*",
            "ids_gerados_db": {
                "data": {
                    "insert": {
                        "cotacao": r['id_cotacao']
                    },
                    "update": {}
                },
                "inserted_ids": {}
            }
        }
        alerts_execute.append(alert)
    return alerts_execute


def load_alerta_perdedor_contumaz():
    query = sql.SQL(
        """
            SELECT
            	MIN(id_cotacao) AS id_cotacao
            FROM cotacao c
            WHERE c.id_pessoa IN (
            	SELECT sq.id_pessoa
            	FROM
            		(
            		SELECT p.id_pessoa,
            			COUNT (cot.id_cotacao) AS lances,
            			COUNT (cot.id_cotacao) filter (WHERE cot.vencedor = FALSE) AS vitorias
            		FROM
            			processo_licitatorio pl
            		JOIN item_licitacao il
            			ON il.id_processo_licitatorio = pl.id_processo_licitatorio
            		JOIN cotacao cot
            			ON cot.id_item_licitacao = il.id_item_licitacao
            		JOIN pessoa p
            			ON p.id_pessoa = cot.id_pessoa
            		JOIN modalidade_licitacao ml
            			ON ml.id_modalidade_licitacao = pl.id_modalidade_licitacao
            		WHERE
            			ml.descricao NOT IN ('Dispensa de Licitação', 'Inexigibilidade de Licitação', 'Regime Diferenciado de Contratação', 'Procedimento Licitatório Lei 13.303/06', 'Outras')
            		GROUP BY p.id_pessoa
            		HAVING COUNT (cot.id_cotacao) >= 10
            		) AS sq
            	WHERE sq.vitorias::numeric / NULLIF (sq.lances, 0) > 0.9
            	)
            GROUP BY c.id_pessoa
        """
    )
    cursor.execute(query)
    result = cursor.fetchall()
    alerts_execute = []
    for r in result:
        alert = {
            "routing_key": "insert.*",
            "ids_gerados_db": {
                "data": {
                    "insert": {
                        "cotacao": r['id_cotacao']
                    },
                    "update": {}
                },
                "inserted_ids": {}
            }
        }
        alerts_execute.append(alert)
    return alerts_execute


def load_alerta_baixa_competitividade():
    query = sql.SQL(
        """
        select
            sq.id_item_licitacao
        from(
        select
            pl.id_processo_licitatorio,
            il.id_item_licitacao,
            count(cot.id_cotacao) as lances
        from
            processo_licitatorio pl
                join modalidade_licitacao ml on ml.id_modalidade_licitacao = pl.id_modalidade_licitacao
                join item_licitacao il on il.id_processo_licitatorio = pl.id_processo_licitatorio
                join cotacao cot on cot.id_item_licitacao = il.id_item_licitacao
        where
            pl.situacao = 'Homologada'
            and ml.descricao not in ('Convite', 'Dispensa de Licitação', 'Inexigibilidade de Licitação', 'Regime Diferenciado de Contratação', 'Procedimento Licitatório Lei 13.303/06', 'Outras')
        group by
            il.id_item_licitacao,
            pl.id_processo_licitatorio) sq
        where
            sq.lances < 10
                and not exists (
                    select
                        oa.id_item_licitacao
                    from
                        alerta a
                            join execucao_metodo em on em.id_execucao_metodo = a.id_execucao_metodo
                            join execucao_metodo_objeto_analise emoa on emoa.id_execucao_metodo = em.id_execucao_metodo
                            join objeto_analise oa on oa.id_objeto_analise = emoa.id_objeto_analise
                        where
                            oa.id_item_licitacao = sq.id_item_licitacao
                )
        """
    )

    cursor.execute(query)
    result = cursor.fetchall()

    alerts_execute = []

    for r in result:
        alert = {
            "routing_key": "insert.*",
            "ids_gerados_db": {
                "data": {
                    "insert": {
                        "item_licitacao": r['id_item_licitacao']
                    },
                    "update": {}
                },
                "inserted_ids": {}
            }
        }

        alerts_execute.append(alert)

    return alerts_execute


def load_alerta_proximidade_datas():
    query = sql.SQL(
        """
        select
            plp.id_processo_licitatorio,
            plp.id_pessoa
        from
            processo_licitatorio pl
                join processo_licitatorio_pessoa plp on plp.id_processo_licitatorio = pl.id_processo_licitatorio
                join pessoa p on p.id_pessoa = plp.id_pessoa
                join pessoa_juridica pj on pj.id_pessoa = p.id_pessoa
                join estabelecimento est on est.cnpj = pj.cnpj
        where	
            pl.data_abertura_certame is not null
            and not exists (
                select
                    oa.id_processo_licitatorio,
                    oa.id_pessoa
                from
                    alerta a
                        join execucao_metodo em on em.id_execucao_metodo = a.id_execucao_metodo
                        join execucao_metodo_objeto_analise emoa on emoa.id_execucao_metodo = em.id_execucao_metodo
                        join objeto_analise oa on oa.id_objeto_analise = emoa.id_objeto_analise
                    where
                        oa.id_processo_licitatorio = plp.id_processo_licitatorio
                        and oa.id_pessoa = plp.id_pessoa
            )
        """
    )

    cursor.execute(query)
    result = cursor.fetchall()

    alerts_execute = []

    for r in result:
        alert = {
            "routing_key": "insert.*",
            "ids_gerados_db": {
                "data": {
                    "insert": {
                        "processo_licitatorio_pessoa": {
                            "processo_licitatorio": r['id_processo_licitatorio'],
                            "pessoa": r['id_pessoa']
                        }
                    },
                    "update": {}
                },
                "inserted_ids": {}
            }
        }

        alerts_execute.append(alert)

    return alerts_execute


def load_alerta_sig():
    query = sql.SQL(
        """
        SELECT 
        	spl.id_processo_licitatorio,
        	spl.id_sig
        FROM 
        	sig_processo_licitatorio spl
        JOIN 
        	processo_licitatorio pl ON pl.id_processo_licitatorio = spl.id_processo_licitatorio
        where not exists (
        	select
        		oa.id_processo_licitatorio
        	from
        		alerta a
        			join execucao_metodo em on em.id_execucao_metodo = a.id_execucao_metodo
        			join execucao_metodo_objeto_analise emoa on emoa.id_execucao_metodo = em.id_execucao_metodo
        			join objeto_analise oa on oa.id_objeto_analise = emoa.id_objeto_analise
        		where
        			oa.id_processo_licitatorio = spl.id_processo_licitatorio
        	)
        """
    )

    cursor.execute(query)
    result = cursor.fetchall()

    alerts_execute = []

    for r in result:
        alert = {
            "routing_key": "insert.*",
            "ids_gerados_db": {
                "data": {
                    "insert": {
                        "sig_processo_licitatorio": {
                            r['id_processo_licitatorio'],
                            r['id_sig']
                        }
                    },
                    "update": {}
                },
                "inserted_ids": {}
            }
        }

        alerts_execute.append(alert)

    return alerts_execute


def load_alerta_tipologia_83():
    query = sql.SQL(
        """
        SELECT 
        	pl.id_processo_licitatorio,
        	plp.id_pessoa,
        	COUNT(DISTINCT plp.id_pessoa) AS lances
        FROM 
        	processo_licitatorio pl
        		JOIN processo_licitatorio_pessoa plp ON plp.id_processo_licitatorio = pl.id_processo_licitatorio
        where not exists (
        	select
        		oa.id_processo_licitatorio
        	from
        		alerta a
        			join execucao_metodo em on em.id_execucao_metodo = a.id_execucao_metodo
        			join execucao_metodo_objeto_analise emoa on emoa.id_execucao_metodo = em.id_execucao_metodo
        			join objeto_analise oa on oa.id_objeto_analise = emoa.id_objeto_analise
        		where
        			oa.id_processo_licitatorio = pl.id_processo_licitatorio)
        GROUP BY
        	pl.id_processo_licitatorio,
        	plp.id_pessoa
        HAVING 
        	COUNT(DISTINCT plp.id_pessoa) < 3
        """
    )

    cursor.execute(query)
    result = cursor.fetchall()

    alerts_execute = []

    for r in result:
        alert = {
            "routing_key": "insert.*",
            "ids_gerados_db": {
                "data": {
                    "insert": {
                        "processo_licitatorio": r['id_processo_licitatorio']
                    },
                    "update": {}
                },
                "inserted_ids": {}
            }
        }

        alerts_execute.append(alert)

    return alerts_execute


with pg_connection.cursor(cursor_factory=RealDictCursor) as cursor:
    alerts = []

    alerts.extend(load_alerta_noticias_municipio())
    alerts.extend(load_alerta_noticias_processo_licitatorio())
    alerts.extend(load_alerta_vencedor_contumaz())
    alerts.extend(load_alerta_perdedor_contumaz())
    alerts.extend(load_alerta_valor_previsto_contratado())

    alerts.extend(load_alerta_baixa_competitividade())
    alerts.extend(load_alerta_proximidade_datas())
    alerts.extend(load_alerta_sig())
    alerts.extend(load_alerta_tipologia_83())

"""Metodo para fechar recursos (conexões) de forma limpa."""
print("Iniciando o desligamento do serviço de alertas...")
if pg_connection and not pg_connection.closed:
    pg_connection.close()
    print("Conexão com o PostgreSQL fechada.")

queue_manager = QueueManagerFactory.get_queue_manager()
queue_manager.connect()
print(f"Connecting to queue: {output_queue}...")
queue_manager.declare_queue(output_queue)
print("...connected to queues successfully.")

# enviar mensagens de coleta para a fila
for i, message in enumerate(alerts):
    print(f"Sending collecting message #{i} to {output_queue}: {message}")
    queue_manager.publish_message(output_queue, json.dumps(message, indent=4))