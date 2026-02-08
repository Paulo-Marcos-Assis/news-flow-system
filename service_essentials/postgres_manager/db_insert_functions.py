import os
import json
from postgres_manager.postgres_base_client import PostgreSqlClient 
import logging
from pprint import pprint
# from config.constants import SENHA, USER, HOST, BANCO, PORT
from postgres_manager.helpers import is_postgres_type, coerce_postgres_type


def prep_data(host, port, user, pwd, db, data_dir=None):
    '''
    Carrega e define o nome da tabela
    Formato (exemplo): {
            "tabela1": {
                "att1": "valor1"
            },
            "tabela2": {
                "att2": "valor2",
                "att3": "valor3",
            }
        }
    Chama type_correction
    Se passar: 
        Divide o df nos atributos que vão para o estático e para o dinâmico
    '''

    # Pega os arquivos do diretório que for apontado ou o padrão
    data_jsons = []
    if not data_dir:
        data_dir = os.path.join(os.getcwd(), "tests", "data_test")
        # print(data_dir)
    for raiz, dirs, arquivos in os.walk(data_dir):
        for nome in arquivos:
            if "json" in nome:
                path = os.path.join(raiz, nome)
                json_arq = json.load(open(path, "r", encoding="utf-8"))
                # print(json.dumps(json_arq, indent=4, ensure_ascii=False))
                data_jsons.append(json_arq) 

    
    # Conexão com o bd
    try: 
        client = PostgreSqlClient(host, port, user, pwd, db)
        if client.engine.begin():
            print("Connected to Static Database")
    except ConnectionError as e:
        logging.error("Connection error")
        raise e
    
    # Checa se os tipos estão todos corretor antes do envio
    checked_data = {}
    for j in data_jsons:               
        for key, value in j.items():
            checked_data[key] = type_correction(client, key, value)
    

    # Envio para a base estática


def type_correction(client, table_name: str, data: dict):
    ''' 
    Puxa o schema da tabela no banco e bate com o os atributos da tabela apresentada
    Imprime todas as correções
    Separa campos que não batem
    Retorna dic dos att estáticos e dinamicos
    [Faltante] Ainda não trata tabelas fixas, que idealmente devem ser identificadas
    '''
    
    try: 
        schema = client.get_schema(table_name, "teste")
        print(f'\nType correction table : {table_name}')
    except Exception as e:
        logging.error("Error during schema loading")
        print(e)

    # Checagem de tipos
    checked_columns = {}
    error_columns = {}
    dynamic_columns = {}
    for column in schema:
        if column['column_name'] in list(data.keys()):
            if is_postgres_type(data[column['column_name']], column['data_type']):
                checked_columns[column['column_name']] = data[column['column_name']]
            else:
                correct_value = coerce_postgres_type(data[column['column_name']], column['data_type'])
                if correct_value:
                    data[column['column_name']] = correct_value
                    checked_columns[column['column_name']] = data[column['column_name']]
                else: 
                    error_columns[column['column_name']] = data[column['column_name']]
       
            
    for key in list(data.keys()):
        if key not in list(checked_columns.keys()):
            dynamic_columns[key] = data[key]

    if error_columns:
        logging.exception(f"Columns {error_columns} can be type corrected")
        raise Exception()

    pprint(f"Colunas estático: {checked_columns}")
    pprint(f"Colunas dinâmico: {dynamic_columns}")
    return [checked_columns, dynamic_columns]