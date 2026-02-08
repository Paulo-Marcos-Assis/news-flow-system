"""'
Cliente básico Orient DB pelo xaxa (original em PHP)
"""

import os
import json
import time
import requests
from service_essentials.utils.logger import Logger


class OrientDBClient:
    MEMORY = "memory"  # Nâo deve ser útil
    DISK = "plocal"

    def __init__(self, host=None, port=None, username=None, password=None, graph_name=None, storage=None):
        # Informações de conexão
        self.storage = storage or os.getenv("ORIENTDB_STORAGE", OrientDBClient.DISK).strip()
        self.host = host or os.getenv("HOST_ORIENT", "localhost").strip()
        self.port = port or int(os.getenv("PORT_ORIENT", "2480").strip())
        self.username = username or os.getenv("USERNAME_ORIENT", "root").strip()
        self.password = password or os.getenv("SENHA_ORIENT", "admin").strip()
        self.graph_name = graph_name or os.getenv("DATABASE_ORIENT", "").strip()

        if not graph_name:
            raise ValueError("Graph name cannot be null or empty.")
        self.graph_name = graph_name
        self.base_url = f"http://{self.host}:{self.port}"

        # Logger
        self.logger = Logger(None, log_to_console=True)

        # Sessão persistente com otimizações de conexão
        # A Session mantém conexões TCP abertas automaticamente:
        # - Se conexão estiver viva: reutiliza (keep-alive)
        # - Se conexão morreu/timeout: cria nova e mantém no pool
        # - Pool gerencia até 20 conexões simultâneas
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.headers.update({
            "Content-Type": "application/json",
            "Connection": "keep-alive"  # Mantém conexão aberta
        })
        
        # HTTPAdapter com pool de conexões:
        # - Reutiliza conexões existentes automaticamente
        # - Cria novas conexões quando necessário
        # - Fecha conexões ociosas após timeout
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,  # Número de pools de conexão (por host)
            pool_maxsize=20,      # Máximo de conexões no pool
            max_retries=3,        # Retries automáticos em caso de falha
            pool_block=False      # Não bloqueia se pool estiver cheio
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Métricas de conexão
        self.connection_time_total = 0.0
        self.connection_count = 0

    def send_request(self, url, method="GET", data=None, raise_exception=True):
        # Rastreia tempo de conexão HTTP
        start_time = time.time()
        try:
            if method == "GET":
                response = self.session.get(url, json=data)
            elif method == "POST":
                response = self.session.post(url, json=data)
            elif method == "DELETE":
                response = self.session.delete(url)
            else:
                response = self.session.request(method, url, json=data)
            
            # Registra tempo de conexão
            connection_time = time.time() - start_time
            self.connection_time_total += connection_time
            self.connection_count += 1

        except requests.RequestException as e:
            connection_time = time.time() - start_time
            self.connection_time_total += connection_time
            self.connection_count += 1
            raise Exception(f"Request error: {str(e)}")

        # Verifica erros na resposta
        result = response.json()
        if response.status_code >= 400 or "error" in result or "errors" in result:
            error_message = (
                result.get("error")
                or result.get("errors")
                or f"HTTP Error: {response.status_code}"
            )
            if raise_exception:
                raise Exception(
                    f"API Error: {json.dumps(error_message) if isinstance(error_message, (dict, list)) else error_message}"
                )
            else:
                return False
        return result

    #  Checa a existencia de um banco, testar primeiro
    def check_and_create_database(self):
        result = self.send_request(f"{self.base_url}/listDatabases")
        if self.graph_name not in result.get("databases", []):
            self.send_request(
                f"{self.base_url}/database/{self.graph_name}/plocal/graph", "POST"
            )

    # Executa comando SQL genérico, chama função de envio
    def execute_command(self, command):
        url = f"{self.base_url}/command/{self.graph_name}/sql"
        data = {"command": command}
        return self.send_request(url, "POST", data)

    # Checa se um nodo com tal propriedade existe, função de busca
    def vertex_exists(self, class_name, property_name, value):
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
            command = f"SELECT FROM {class_name} WHERE {property_name} = {value}"
        else:
            value = str(value).replace("'", "\\'")  # addslashes() do PHP
            command = f"SELECT FROM {class_name} WHERE {property_name} = '{value}'"

        result = self.execute_command(command)
        return result["result"] if result.get("result") else False

    # Checa se uma aresta específica existe entre dois nodos
    # Rid é o id gerado pelo OrientDB, se consegue com: rid = client.get_vertex_id(vertice)
    def edge_exists(self, from_rid, to_rid, edge_class=None):
        command = f"SELECT FROM E WHERE out = {from_rid} AND in = {to_rid}"
        if edge_class:
            command += f" AND @class = '{edge_class}'"
        command += " LIMIT 1"
        result = self.execute_command(command)
        return result["result"][0] if result.get("result") else False

    # Get rid vertice
    def get_vertex_id(self, vertex):
        return vertex.get("@rid")

    # Get rid aresta
    def get_edge_id(self, edge):
        return edge.get("@rid")
    
    def get_vertex_by_rid(self, rid):
        command = f"SELECT FROM {rid}"
        result = self.execute_command(command)
        return result["result"][0] if result.get("result") else None

    # Criar classe de vértices --> Acho que falta tratamento de erros
    def create_vertex_class(self, class_name, extends="V"):
        check_cmd = f"SELECT FROM (SELECT expand(classes) FROM metadata:schema) WHERE name = '{class_name}' LIMIT 1"
        result = self.execute_command(check_cmd)
        if result.get("result"):
            return None

        create_cmd = f"CREATE CLASS {class_name} EXTENDS {extends}"
        result = self.execute_command(create_cmd)
        return result["result"][0] if result.get("result") else None

    def create_edge_class(self, class_name, extends="E"):
        check_cmd = f"SELECT FROM (SELECT expand(classes) FROM metadata:schema) WHERE name = '{class_name}' LIMIT 1"
        result = self.execute_command(check_cmd)
        if result.get("result"):
            return result["result"][0]

        create_cmd = f"CREATE CLASS {class_name} EXTENDS {extends}"
        result = self.execute_command(create_cmd)
        return result["result"][0] if result.get("result") else None

    # Cria vértice
    # propriedades é um dic com as informações do vértice

    def create_vertex(self, class_name, properties):
        props = []
        for key, value in properties.items():
            serialized_value = json.dumps(value, ensure_ascii=False)
            props.append(f"{key} = {serialized_value}")
        
        command = f"CREATE VERTEX {class_name} SET {', '.join(props)}"
        result = self.execute_command(command)
        return result["result"][0] if result.get("result") else None
    
    def create_vertex_batch(self, class_name, list_of_properties):
        if not list_of_properties:
            return []

        # Monta a lista de comandos CREATE VERTEX
        # commands = []
        # for props in list_of_properties:
        #     serialized = []
        #     for key, value in props.items():
        #         serialized_value = json.dumps(value, ensure_ascii=False)
        #         serialized.append(f"{key} = {serialized_value}")
        #     commands.append({
        #         "type": "cmd",
        #         "language": "sql",
        #         "command": f"CREATE VERTEX {class_name} SET {', '.join(serialized)}"
        #     })
        # print(commands)
        sql_commands = "; ".join(
            f"CREATE VERTEX {class_name} SET {', '.join([f'{k} = {json.dumps(v)}' for k, v in props.items()])}"
            for props in list_of_properties
        )

        data = {
            "transaction": True,
            "operations": [{
                "type": "script",
                "language": "sql",
                "script": sql_commands
            }]
        }
        print(data)

        # Envia para /batch/{database}
        url = f"{self.base_url}/batch/{self.graph_name}"
        result = self.send_request(url, method="POST", data=data)
        # print(json.dumps(result, indent=2, ensure_ascii=False))
        return result.get("result", [])

    def update_vertex(self, rid, properties, max_retries=3):
        import time
        props = []
        for key, value in properties.items():

            serialized_value = json.dumps(value, ensure_ascii=False)
            props.append(f"{key} = {serialized_value}")
        command = f"UPDATE {rid} SET {', '.join(props)} RETURN AFTER @this"
        
        # Retry logic for concurrent modification exceptions
        for attempt in range(max_retries):
            try:
                result = self.execute_command(command)
                return result["result"][0] if result.get("result") else None
            except Exception as e:
                error_msg = str(e)
                if "OConcurrentModificationException" in error_msg and attempt < max_retries - 1:
                    # Exponential backoff: wait 0.1s, 0.2s, 0.4s
                    wait_time = 0.1 * (2 ** attempt)
                    self.logger.warning(f"Concurrent modification detected on {rid}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    raise

    
    def create_vertex_batch(self, class_name, list_of_properties):
        if not list_of_properties:
            return []

        # Monta a lista de comandos CREATE VERTEX
        # commands = []
        # for props in list_of_properties:
        #     serialized = []
        #     for key, value in props.items():
        #         serialized_value = json.dumps(value, ensure_ascii=False)
        #         serialized.append(f"{key} = {serialized_value}")
        #     commands.append({
        #         "type": "cmd",
        #         "language": "sql",
        #         "command": f"CREATE VERTEX {class_name} SET {', '.join(serialized)}"
        #     })
        # print(commands)
        sql_commands = "; ".join(
            f"CREATE VERTEX {class_name} SET {', '.join([f'{k} = {json.dumps(v)}' for k, v in props.items()])}"
            for props in list_of_properties
        )

        data = {
            "transaction": True,
            "operations": [{
                "type": "script",
                "language": "sql",
                "script": sql_commands
            }]
        }
        print(data)

        # Envia para /batch/{database}
        url = f"{self.base_url}/batch/{self.graph_name}"
        result = self.send_request(url, method="POST", data=data)
        # print(json.dumps(result, indent=2, ensure_ascii=False))
        return result.get("result", [])

    # Cria aresta
    # edge_class deve ser padronizado no trabalho
    def create_edge(self, from_vertex_id, to_vertex_id, edge_class="E"):
        command = f"CREATE EDGE {edge_class} FROM {from_vertex_id} TO {to_vertex_id}"
        result = self.execute_command(command)
        return result["result"][0] if result.get("result") else None

    # Apaga aresta usando id
    def remove_edge(self, from_id, to_id, edge_class="E"):
        command = f"DELETE EDGE FROM {from_id} TO {to_id}"
        if edge_class and edge_class != "E":
            command += f" WHERE @class = '{edge_class}'"
        result = self.execute_command(command)
        return result.get("result")

    # Puxa arestas que saem ou entram em um vértice
    def get_outgoing_targets(self, vertex_id):
        command = f"SELECT expand(out()) FROM {vertex_id}"
        result = self.execute_command(command)
        return result["result"] if isinstance(result.get("result"), list) else []

    def get_incoming_sources(self, vertex_id):
        command = f"SELECT expand(in()) FROM {vertex_id}"
        result = self.execute_command(command)
        return result["result"] if isinstance(result.get("result"), list) else []

    def get_connection_metrics(self):
        """
        Retorna métricas de tempo de conexão HTTP.
        """
        return {
            "total_time": round(self.connection_time_total, 3),
            "count": self.connection_count,
            "average_time": round(self.connection_time_total / self.connection_count, 3) if self.connection_count > 0 else 0
        }
    
    def reset_connection_metrics(self):
        """
        Reseta as métricas de conexão.
        """
        self.connection_time_total = 0.0
        self.connection_count = 0

    def count_connected_vertices(
        self, source_class, target_class, source_key_property="value"
    ):
        query = f"""
        SELECT {source_key_property},
               (SELECT count(*) as cnt 
                FROM (SELECT expand(out()) FROM $current) 
                WHERE @class = '{target_class}') as count 
        FROM {source_class}
        """
        result = self.execute_command(query)
        mapping = {}
        for record in result.get("result", []):
            key = record.get(source_key_property, "unknown")
            cnt = 0
            if (
                "count" in record
                and isinstance(record["count"], list)
                and record["count"]
            ):
                cnt = record["count"][0].get("cnt", 0)
            mapping[json.dumps(key) if isinstance(key, (dict, list)) else key] = cnt
        return mapping
