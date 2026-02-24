"""'
Cliente Orient DB que aplica as regras do banco dinâmico Céos V0
"""

from service_essentials.orientdb_manager.orient_base_client import OrientDBClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Result
import logging
import json
from datetime import datetime, date


class CeosOrientDBClient(OrientDBClient):
    def __init__(self, host, port, username, password, graph_name, storage=None):
        super().__init__(host, port, username, password, graph_name, storage=None)
        self.edges = ["contains_attribute", "related_to"]
        # Cache de classes já criadas para evitar verificações repetidas
        self._created_classes_cache = set()
        self._config()  # Configura coisas básicas do modelo ceos

    def _ensure_attribute_class_exists(self):
        """Garante que a classe attribute existe no OrientDB."""
        try:
            if super().create_vertex_class("attribute"):
                logging.info("Classe 'attribute' criada com sucesso")
                self._created_classes_cache.add("attribute")
                try:
                    command = "CREATE PROPERTY attribute.date_updated DATETIME;"
                    super().execute_command(command)
                    logging.info("Propriedade date_updated criada para attribute")
                except Exception as prop_error:
                    logging.debug(f"Propriedade date_updated já existe para attribute: {prop_error}")
            else:
                # Classe já existe
                self._created_classes_cache.add("attribute")
                logging.debug("Classe 'attribute' já existe")
        except Exception as e:
            logging.error(f"Erro ao criar classe attribute: {e}")
            raise
    
    def _config(self):
        try:
            logging.debug(
                "Configuring (adding basic relationships, vertex classes and labels...)"
            )
            # Cria a classe attribute se não existir
            self._ensure_attribute_class_exists()
            
            for edge in self.edges:
                super().create_edge_class(edge)
        except Exception as e:
            logging.exception("Error during base configuring.")
            raise e

    def add_object_vertex(self, id_object, obj_class, date_updated):
        """
        Cria vértice de objeto. Otimizado com cache de classes e INSERT com UPSERT.
        """
        try:
            # limpando
            obj_class = obj_class.lower().strip()
        except ValueError as e:
            print(f"Error: {e}")
            return None

        # OTIMIZAÇÃO: Só cria classe se não estiver no cache
        if obj_class not in self._created_classes_cache:
            create_obj_class = super().create_vertex_class(obj_class)
            if create_obj_class:
                try:
                    # Cria propriedades e índice em um único comando batch
                    batch_cmd = f"CREATE PROPERTY {obj_class}.date_updated DATETIME; CREATE PROPERTY {obj_class}.id_object INTEGER; create index id_object_{obj_class} on {obj_class}(id_object) UNIQUE INTEGER;"
                    self.execute_command(batch_cmd)
                except Exception as e:
                    # Propriedades/índices podem já existir, ignora erro
                    logging.debug(f"Propriedades já existem para {obj_class}: {e}")
            self._created_classes_cache.add(obj_class)

        # Verifica se já existe antes de criar
        exists = super().vertex_exists(obj_class, "id_object", id_object)
        if exists:
            # Retorna o RID existente ao invés de lançar exceção
            return exists[0]["@rid"]

        # Cria novo vértice
        attributes = {}
        attributes["id_object"] = id_object
        attributes["date_updated"] = date_updated
        result = self.create_vertex(obj_class, attributes)

        return result["@rid"]

    def add_attribute_vertex(
        self,
        rid_object,
        source_name,
        id_original,
        attribute_name,
        attribute_value,
        date_updated,
    ):
        try:
            # limpando
            source_name = source_name.lower().strip()
            if not id_original:
                raise ValueError("IDs can't be null.")
            if not attribute_name or not attribute_value:
                raise ValueError("Attribute name or value can't be null.")
        except ValueError as e:
            print(f"Error: {e}")
            return None

        result = []
        attributes = {}
        attributes["id_original"] = id_original
        attributes["attribute_name"] = attribute_name
        attributes["attribute_value"] = attribute_value
        attributes["id_source"] = source_name
        attributes["date_updated"] = date_updated
        result_vertex = super().create_vertex("attribute", attributes)
        # adicionando a aresta
        result_edge = super().create_edge(
            rid_object, result_vertex["@rid"], self.edges[0]
        )

        self.alter_object_vertex(date_updated, rid_object=rid_object)

        result.append(result_vertex)
        result.append(result_edge)
        return result

    def add_attributes_batch(self, rid_object, attributes_list):
        """
        Versão otimizada: busca atributos existentes UMA vez e usa cache para lookup O(1)
        Reduz complexidade de O(N*M) para O(N+M)
        """
        import time
        if not attributes_list:
            return []

        start_time = time.time()
        results = []
        
        # OTIMIZAÇÃO 1: Buscar todos os atributos existentes UMA vez (já com dados completos)
        t1 = time.time()
        try:
            existing_attributes = self.get_outgoing_attributes(rid_object)
        except Exception as e:
            # Se a classe attribute não existe, cria ela
            if "Class not found: attribute" in str(e):
                logging.warning("Classe 'attribute' não encontrada, criando...")
                self._ensure_attribute_class_exists()
                existing_attributes = []  # Primeira vez, não há atributos
            else:
                raise
        logging.info(f"[PERF] get_outgoing_attributes: {time.time() - t1:.3f}s")
        
        # OTIMIZAÇÃO 2: Criar índice em memória para lookup O(1)
        # Chave: (id_source, attribute_name) -> rid
        # Agora os dados já vêm completos da query otimizada, sem necessidade de get_vertex_by_rid
        existing_attrs_map = {}
        for attr_data in existing_attributes:
            try:
                if attr_data and '@rid' in attr_data:
                    key = (attr_data.get('id_source'), attr_data.get('attribute_name'))
                    existing_attrs_map[key] = attr_data['@rid']
            except:
                continue

        # OTIMIZAÇÃO 3: Separar operações de CREATE e UPDATE para batch
        vertices_to_create = []
        vertices_to_update = []
        
        for attr in attributes_list:
            try:
                source_name = attr.get("source_name") or "unknown"
                source_name = source_name.lower().strip()
                id_original = attr["id_original"]
                attribute_name = attr["attribute_name"]
                attribute_value = attr["attribute_value"]
                date_updated = attr["date_updated"]

                if not id_original or not source_name:
                    continue
                if not attribute_name or not attribute_value:
                    continue

                vertex_props = {
                    "id_original": id_original,
                    "attribute_name": attribute_name,
                    "attribute_value": attribute_value,
                    "id_source": source_name,
                    "date_updated": date_updated
                }

                # Lookup O(1) no cache ao invés de loop O(M)
                lookup_key = (source_name, attribute_name)
                if lookup_key in existing_attrs_map:
                    # Atributo existe - adicionar para update
                    rid = existing_attrs_map[lookup_key]
                    vertices_to_update.append((rid, vertex_props))
                else:
                    # Atributo novo - adicionar para create
                    vertices_to_create.append(vertex_props)

            except Exception as e:
                logging.warning(f"Erro ao processar atributo: {e}")
                continue

        # OTIMIZAÇÃO 4: Executar updates em batch
        t2 = time.time()
        for rid, props in vertices_to_update:
            try:
                vertex = self.update_vertex(rid, props)
                results.append({"vertex": vertex, "operation": "update"})
            except Exception as e:
                logging.warning(f"Erro ao atualizar vértice {rid}: {e}")
        if vertices_to_update:
            logging.info(f"[PERF] updates ({len(vertices_to_update)}): {time.time() - t2:.3f}s")

        # OTIMIZAÇÃO 5: Executar creates + edges em batch usando transação
        if vertices_to_create:
            t3 = time.time()
            try:
                created_vertices = self._create_attributes_and_edges_batch(rid_object, vertices_to_create)
                for vertex in created_vertices:
                    results.append({"vertex": vertex, "operation": "create"})
                logging.info(f"[PERF] batch create ({len(vertices_to_create)}): {time.time() - t3:.3f}s")
            except Exception as e:
                logging.error(f"Erro ao criar atributos em batch: {e}")
                # Fallback: criar um por um
                t4 = time.time()
                for vertex_props in vertices_to_create:
                    try:
                        vertex = self.create_vertex("attribute", vertex_props)
                        if vertex:
                            edge = self.create_edge(rid_object, vertex["@rid"], self.edges[0])
                            results.append({"vertex": vertex, "edge": edge, "operation": "create"})
                    except:
                        continue
                logging.info(f"[PERF] fallback create ({len(vertices_to_create)}): {time.time() - t4:.3f}s")

        # Atualizar objeto principal com a última data (opcional)
        if attributes_list:
            t5 = time.time()
            last_date = attributes_list[-1]["date_updated"]
            self.alter_object_vertex(last_date, rid_object=rid_object)
            logging.info(f"[PERF] alter_object_vertex: {time.time() - t5:.3f}s")

        logging.info(f"[PERF] add_attributes_batch TOTAL: {time.time() - start_time:.3f}s")
        return results

    def get_outgoing_attributes(self, vertex_id):
        """
        Busca todos os atributos conectados a um objeto.
        Retorna lista com @rid, id_source e attribute_name já incluídos.
        """
        # Opção 1: Usando subquery (mais compatível)
        command = f"""
        SELECT @rid, id_source, attribute_name, attribute_value, id_original, date_updated 
        FROM attribute 
        WHERE @rid IN (SELECT out('contains_attribute') FROM {vertex_id})
        """
        
        # Opção 2: Se a Opção 1 não funcionar bem, use traverse
        # command = f"""
        # SELECT @rid, id_source, attribute_name, attribute_value, id_original, date_updated 
        # FROM (TRAVERSE out('contains_attribute') FROM {vertex_id} MAXDEPTH 1) 
        # WHERE @class = 'attribute'
        # """
        
        result = self.execute_command(command)
        return result["result"] if isinstance(result.get("result"), list) else []
    
    def _create_attributes_and_edges_batch(self, rid_object, attributes_list):
        import json

        '''begin;
            let account = create vertex Account set name = 'Luke';
            let city = select from City where name = 'London';
            let e = create edge Lives from $account to $city;
            commit retry 100;
            return $e;'''
        
        if not attributes_list:
            return []
            
        commands = []
        commands.append('begin;')

        for i, props in enumerate(attributes_list):
            props_str = ', '.join([
                f"{k} = {json.dumps(v, ensure_ascii=False)}"
                for k, v in props.items()
            ])
            
            # 1. REMOÇÃO DOS PARÊNTESES no CREATE
            commands.append(f"\nlet $attr{i} = create vertex attribute set {props_str};")
            commands.append(f"let $edge{i} = create edge contains_attribute from {rid_object} to $attr{i};")
        
        return_vars = ", ".join([f"$attr{i}" for i in range(len(attributes_list))])
        commands.append('commit retry 100;')
        commands.append(f"return [{return_vars}];")
        
        # 2. SEPARADOR CORRETO: Usar quebra de linha para scripts multilinhas
        script = "\n".join(commands)
        # script = f"SCRIPT sql\n{script_body}"
        
        try:
            # Se este formato ainda falhar, tente prefixar com "SCRIPT sql\n"
            result = self.execute_script(script)
            return result.get("result", [])
            
        except Exception as e:
            import logging
            logging.error(f"Erro no batch de atributos: {e}")
            logging.error(f"Script executado:\n{script}")
            raise


    def get_object_vertex(self, id_object, obj_class):
        """
        Busca vértice de objeto. Otimizado para não verificar existência de classe toda vez.
        A classe será criada apenas quando necessário (no add_object_vertex).
        """
        try:
            result = self.vertex_exists(obj_class, "id_object", id_object)
            if result:
                return result[0]["@rid"]
            else:
                return result
        except Exception as e:
            # Se a classe não existe, retorna False (será criada no add_object_vertex)
            if "not found" in str(e).lower() or "doesn't exist" in str(e).lower():
                return False
            raise

    def alter_object_vertex(
        self, date_updated, obj_class=None, id_object=None, rid_object=None
    ):
        try:
            if not id_object and not rid_object:
                raise ValueError("ids can't be null.")
        except ValueError as e:
            print(f"Error: {e}")
            return None

        try:
            if id_object:
                rid = self.get_object_vertex(id_object, obj_class)
                if not rid:
                    raise Exception("object doesnt exists")
                attributes["id_object"] = id_object
            else:
                rid = rid_object
            attributes = {}
            attributes["date_updated"] = date_updated
            result = self.update_vertex(rid, attributes)
            if result:
                return True
            else:
                raise False
        except Exception as e:
            print(e)

    def remove_vertexes(
        self, id_vertex=None, property=None, property_name=None, vertex_class=None
    ):
        if id_vertex:
            command = f"DELETE VERTEX WHERE @rid = {id_vertex}"
            result = super().execute_command(command)
            return result.get("result")
        elif property and property_name and vertex_class:
            command = (
                f"DELETE VERTEX {vertex_class} WHERE {property_name} = '{property}'"
            )
            result = super().execute_command(command)
            return result.get("result")
        return None

    def _remove_vertex_class(self, vertex_class):
        command = f"DROP CLASS {vertex_class}"
        result = super().execute_command(command)
        return result["result"][0] if result.get("result") else None

    def send_to_dynamic_database(
        self,
        id_object,
        id_original,
        table_name: str,
        data: dict,
        source: str,
        change_object_vertex=False,
        ):
        import time
        start_time = time.time()
        date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            t1 = time.time()
            object = self.get_object_vertex(
                id_object, table_name
            )  # retorna o rid do vertex
            t1_elapsed = time.time() - t1
            logging.info(f"[PERF] get_object_vertex: {t1_elapsed:.3f}s (objeto {'existe' if object else 'não existe'})")
            
            if object:
                if change_object_vertex:
                    new_object = self.alter_object_vertex(object, id_object, date_added)
                    if new_object:
                        pass
                        # print("Objeto substituido, novo rid: ", object)
                if data:
                    data = self.remove_fks_from_attributes(data)
                    dict_list = []
                    for key, value in data.items():
                        dict_list.append({"source_name": source, 
                                          "id_original": id_original, 
                                          "attribute_name": key, 
                                          "attribute_value": value, 
                                          "date_updated": date_added})
                    t2 = time.time()
                    result = self.add_attributes_batch(object, dict_list) # Inserção em batch
                    logging.info(f"[PERF] add_attributes_batch call: {time.time() - t2:.3f}s")
                logging.info(f"[PERF] send_to_dynamic_database (existing): {time.time() - start_time:.3f}s")
                return object  # Retorna o ID orient do vertex de objeto
            else:
                # caso de primeira inserção
                logging.info(
                    f"Objeto {table_name} sendo adicionado, params:\n [id_object: {id_object}, id_original: {id_original}, id_postgres_source: {source}]"
                )

                t3 = time.time()
                object = self.add_object_vertex(id_object, table_name, date_added)
                logging.info(f"[PERF] add_object_vertex: {time.time() - t3:.3f}s")
                
                if object:
                    logging.info("Nodo de objeto adicionado:", object)
                    if data:
                        data = self.remove_fks_from_attributes(data)
                        dict_list = []
                        for key, value in data.items():
                            dict_list.append({"source_name": source, "id_original": id_original, "attribute_name": key, "attribute_value": value, "date_updated": date_added})
                        t4 = time.time()
                        result = self.add_attributes_batch(object, dict_list)
                        logging.info(f"[PERF] add_attributes_batch call (new): {time.time() - t4:.3f}s")
                        logging.info("Adicionando nodo de atributo: ", result)

                logging.info(f"[PERF] send_to_dynamic_database (new): {time.time() - start_time:.3f}s")
                return object  # Retorna o ID orient do vertex de objeto
        except Exception as e:
            logging.exception(e)

    def add_relationship_edge(self, source_value, from_rid=None, to_rid=None, batch_pairs=None):
        """
        Adiciona relacionamentos entre vértices usando RIDs.
        
        Args:
            from_rid: RID ou lista de RIDs de origem
            to_rid: RID ou lista de RIDs de destino
            batch_pairs: Lista de pares [[from_rid, to_rid], [from_rid, [to_rid1, to_rid2]], ...]
        
        Returns:
            bool: True se pelo menos um relacionamento foi criado/existe
        """
        edge_class = self.edges[1]
        
        # -----------------------------
        # MODO BATCH: Lista de pares
        # -----------------------------
        if batch_pairs:
            commands = []
            commands.append('begin;')
            
            var_counter = 0
            return_vars = []
            
            for pair in batch_pairs:
                if len(pair) != 2:
                    continue
                    
                fr = pair[0]
                tr = pair[1]
                
                # VALIDAÇÃO: Pula pares com RIDs vazios/inválidos
                if not fr or not tr:
                    continue
                
                # Normalizar to_rid para lista
                if isinstance(tr, str):
                    to_rids = [tr]
                else:
                    to_rids = list(tr) if hasattr(tr, '__iter__') else [tr]
                
                # Criar comandos para cada combinação
                for to_rid_item in to_rids:
                    # VALIDAÇÃO: Pula RIDs vazios ou inválidos
                    if not to_rid_item or str(to_rid_item).strip() == '' or str(to_rid_item).strip() == 'None':
                        continue
                    
                    from_rid_clean = str(fr).strip()
                    to_rid_clean = str(to_rid_item).strip()
                    
                    # VALIDAÇÃO FINAL: Verifica formato básico de RID (#cluster:position)
                    if not (from_rid_clean.startswith('#') and ':' in from_rid_clean):
                        continue
                    if not (to_rid_clean.startswith('#') and ':' in to_rid_clean):
                        continue
                    
                    # Usa lógica IF NOT EXISTS para evitar duplicatas sem queries adicionais
                    # Isso é muito mais rápido que verificar edge_exists() para cada par
                    commands.append(f"\nlet $e{var_counter} = SELECT FROM E WHERE out = {from_rid_clean} AND in = {to_rid_clean} AND @class = '{edge_class}';")
                    commands.append(f"\nlet $e{var_counter}_created = IF($e{var_counter}.size() = 0, create edge {edge_class} from {from_rid_clean} to {to_rid_clean} set id_source = '{source_value}', $e{var_counter});")
                    return_vars.append(f"$e{var_counter}_created")
                    var_counter += 1
            
            # Se nenhum edge válido foi criado, retorna True (sucesso vazio)
            if var_counter == 0:
                logging.info("[OrientDB] Nenhum edge válido para criar no batch (todos filtrados por validação)")
                return True
            
            # Adicionar commit e return
            commands.append('commit retry 100;')
            if return_vars:
                return_vars_str = ", ".join(return_vars)
                commands.append(f"return [{return_vars_str}];")
            
            # Montar script
            script = "".join(commands)
            
            logging.info(f"[OrientDB] Executando batch com {var_counter} edges")
            
            try:
                result = self.execute_script(script)
                logging.info(f"[OrientDB] Batch executado com sucesso: {var_counter} edges processados")
                return result is not None
            except Exception as e:
                logging.exception(f"Erro no batch: {e}")
                logging.error(f"Script executado:\n{script}")
                return False
        
        # -----------------------------
        # MODO SIMPLES: from_rid e to_rid
        # -----------------------------
        if from_rid and to_rid:
            # Normaliza para listas
            if isinstance(from_rid, str):
                from_rids = [from_rid]
            else:
                from_rids = list(from_rid)
                
            if isinstance(to_rid, str):
                to_rids = [to_rid]
            else:
                to_rids = list(to_rid)
            
            results = []
            
            # Caso 1: tamanhos iguais → mapear 1–1
            if len(from_rids) == len(to_rids):
                for fr, tr in zip(from_rids, to_rids):
                    if not self.edge_exists(fr, tr, edge_class):
                        results.append(self.create_edge(fr, tr, edge_class))
                    else:
                        results.append(True)
            else:
                # Caso 2: 1:n ou n:1
                for fr in from_rids:
                    for tr in to_rids:
                        if not self.edge_exists(fr, tr, edge_class):
                            results.append(self.create_edge(fr, tr, edge_class))
                        else:
                            results.append(True)
            
            return any(results)
        
        return None

    # utils
    def remove_fks_from_attributes(self, data: dict):
        new_data = {}
        for key, value in data.items():
            if not key.startswith("id_"):
                new_data[key] = value
        return new_data

    def execute_script(self, script):
        url = f"{self.base_url}/batch/{self.graph_name}"

        payload = {
            "transaction": True,
            "operations": [
                {
                    "type": "script",
                    "language": "SQL",
                    "script": script
                }
            ]
        }

        return self.send_request(url, "POST", payload)


    # Métodos de pesquisa úteis (adc mais de acordo com a demanda)

    def vertex_classes(self):
        command = f"SELECT expand(classes) FROM metadata:schema"
        result = super().execute_command(command)
        return result["result"][0] if result.get("result") else None

    def class_exists(self, vertex_class):
        command = f"SELECT FROM (SELECT expand(classes) FROM metadata:schema) WHERE name = '{vertex_class}'"
        result = super().execute_command(command)
        return result["result"][0] if result.get("result") else None

    def get_all_same_class(self, vertex_class):
        command = f"SELECT FROM '{vertex_class}'"
        result = super().execute_command(command)
        return result["result"][0] if result.get("result") else None
        return result["result"][0] if result.get("result") else None

    def get_all_same_source(self, source_name):
        pass

