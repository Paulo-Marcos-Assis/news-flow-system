from ..base_nested_extractor import BaseNestedExtractor


class ItemLicitacaoExtractor(BaseNestedExtractor):
    field_name = "item_licitacao"
    scope = "processo_licitatorio"
    nested_key = "item_licitacao"
    nested_scope = "item_licitacao"

    def extract(self, record):
        """Extract item_licitacao with nested pessoa containing filtered cotacao."""
        parent_data = record.get(self.scope, {})
        
        items = parent_data.get('item_licitacao', [])
        participantes = parent_data.get('participante_licitacao', [])
        
        if not items or not isinstance(items, list):
            return None
        
        # Get extractors for item_licitacao scope
        item_extractors = self.extractors_by_scope.get('item_licitacao', {})
        cotacao_extractors = self.extractors_by_scope.get('cotacao', {})
        processo_licitatorio_pessoa_extractors = self.extractors_by_scope.get('processo_licitatorio_pessoa', {})
        
        results = []
        for item in items:
            item_id = item.get('id_item_licitacao')
            
            # Build temp record for item extractors
            temp_record = {'item_licitacao': item}
            
            # Extract item fields
            extracted_item = {}
            for field_name, extractor in item_extractors.items():
                # Skip pessoa extractor if it exists at item level - we handle it specially
                if field_name == 'pessoa':
                    continue
                try:
                    value = extractor.extract(temp_record)
                    if value is not None:
                        extracted_item[field_name] = value
                except Exception as e:
                    self.logger.warning(f"Error extracting {field_name}: {e}")
            
            # Find participantes with cotacao for this item
            pessoas = []
            for participante in participantes:
                cotacoes = participante.get('cotacao', [])
                # Filter cotacao for this specific item
                item_cotacoes = [c for c in cotacoes if c.get('id_item_licitacao') == item_id]
                
                if item_cotacoes:
                    # Build pessoa record
                    pessoa = {
                        'nome': participante.get('nome_participante')
                    }
                    
                    # Add pessoa_fisica or pessoa_pessoa_juridica
                    id_tipo_pessoa = str(participante.get('id_tipo_pessoa', ''))
                    if id_tipo_pessoa == '1':
                        pessoa['pessoa_fisica'] = {
                            'cpf': participante.get('codigo_cic_participante')
                        }
                    elif id_tipo_pessoa == '2':
                        pessoa['pessoa_pessoa_juridica'] = {
                            'cnpj': participante.get('codigo_cic_participante')
                        }
                    
                    # Extract processo_licitatorio_pessoa fields
                    processo_licitatorio_pessoa = {}
                    temp_part_record = {'participante_licitacao': participante, 'processo_licitatorio_pessoa': participante}
                    for field_name, extractor in processo_licitatorio_pessoa_extractors.items():
                        if field_name == 'pessoa':
                            continue
                        try:
                            value = extractor.extract(temp_part_record)
                            if value is not None:
                                processo_licitatorio_pessoa[field_name] = value
                        except:
                            pass
                    if processo_licitatorio_pessoa:
                        pessoa['processo_licitatorio_pessoa'] = processo_licitatorio_pessoa
                    
                    # Extract cotacao fields for this item's cotacoes
                    extracted_cotacoes = []
                    for cot in item_cotacoes:
                        temp_cot_record = {'cotacao': cot}
                        extracted_cot = {}
                        for field_name, extractor in cotacao_extractors.items():
                            try:
                                value = extractor.extract(temp_cot_record)
                                if value is not None:
                                    extracted_cot[field_name] = value
                            except:
                                pass
                        if extracted_cot:
                            extracted_cotacoes.append(extracted_cot)
                    
                    if extracted_cotacoes:
                        pessoa['cotacao'] = extracted_cotacoes
                    
                    pessoas.append(pessoa)
            
            if pessoas:
                extracted_item['pessoa'] = pessoas
            
            if extracted_item:
                results.append(extracted_item)
        
        return results if results else None
