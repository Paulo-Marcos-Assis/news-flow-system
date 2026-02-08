from ..base_nested_extractor import BaseNestedExtractor


class PessoaUnifiedExtractor(BaseNestedExtractor):
    """
    Creates unified pessoa objects from empenho and contrato data in processo_licitatorio.
    
    Groups by cnpj_cpf (from empenho.cnpj_cpf_credor or contrato.codigo_cic_contratado).
    
    Structure:
    processo_licitatorio:
      pessoa[]:
        nome: <credor/nome_contratado>
        pessoa_fisica: {cpf: ...} OR pessoa_pessoa_juridica: {cnpj: ...}
        empenho[]:
          - <empenho fields>
            liquidacao[]:
              - <liquidacao fields>
                pagamento_empenho: {...}  (when values match 1:1)
            pagamento_empenho[]:  (when values don't match - separate list)
              - {...}
        contrato[]:
          - <contrato fields>
    """
    field_name = "pessoa"
    scope = "processo_licitatorio"
    nested_key = None
    nested_scope = None

    def extract(self, record):
        parent_data = record.get(self.scope, {})
        empenhos = parent_data.get('empenho', []) or []
        contratos = parent_data.get('contrato', []) or []
        
        if not empenhos and not contratos:
            return None
        
        # Get extractors
        empenho_extractors = self.extractors_by_scope.get('empenho', {})
        contrato_extractors = self.extractors_by_scope.get('contrato', {})
        liquidacao_extractors = self.extractors_by_scope.get('liquidacao', {})
        pagamento_extractors = self.extractors_by_scope.get('pagamento_empenho', {})
        
        # Group by cnpj_cpf
        pessoas_dict = {}  # cnpj_cpf -> pessoa object
        
        # Process empenhos
        for empenho in empenhos:
            cnpj_cpf = empenho.get('cnpj_cpf_credor')
            if not cnpj_cpf:
                continue
            
            cnpj_cpf = str(cnpj_cpf).strip()
            
            # Create pessoa if not exists
            if cnpj_cpf not in pessoas_dict:
                pessoa = self._create_pessoa_from_empenho(empenho, cnpj_cpf)
                pessoas_dict[cnpj_cpf] = pessoa
            
            # Extract empenho with nested liquidacao/pagamento
            extracted_empenho = self._extract_empenho(
                empenho, empenho_extractors, liquidacao_extractors, pagamento_extractors
            )
            if extracted_empenho:
                if 'empenho' not in pessoas_dict[cnpj_cpf]:
                    pessoas_dict[cnpj_cpf]['empenho'] = []
                pessoas_dict[cnpj_cpf]['empenho'].append(extracted_empenho)
        
        # Process contratos
        for contrato in contratos:
            cnpj_cpf = contrato.get('codigo_cic_contratado')
            if not cnpj_cpf:
                continue
            
            cnpj_cpf = str(cnpj_cpf).strip()
            
            # Create pessoa if not exists
            if cnpj_cpf not in pessoas_dict:
                pessoa = self._create_pessoa_from_contrato(contrato, cnpj_cpf)
                pessoas_dict[cnpj_cpf] = pessoa
            
            # Extract contrato fields
            extracted_contrato = self._extract_with_extractors(
                {'contrato': contrato}, contrato_extractors, 'contrato'
            )
            if extracted_contrato:
                if 'contrato' not in pessoas_dict[cnpj_cpf]:
                    pessoas_dict[cnpj_cpf]['contrato'] = []
                pessoas_dict[cnpj_cpf]['contrato'].append(extracted_contrato)
        
        pessoas = list(pessoas_dict.values())
        return pessoas if pessoas else None

    def _create_pessoa_from_empenho(self, empenho, cnpj_cpf):
        """Create pessoa object from empenho data."""
        nome = empenho.get('credor')
        id_tipo_pessoa = empenho.get('id_tipo_pessoa_quem')
        
        try:
            id_tipo_pessoa = int(float(id_tipo_pessoa)) if id_tipo_pessoa else None
        except (ValueError, TypeError):
            id_tipo_pessoa = None
        
        pessoa = {'nome': nome}
        
        if id_tipo_pessoa in (1, 4):
            pessoa['pessoa_fisica'] = {'cpf': cnpj_cpf}
        elif id_tipo_pessoa in (2, 3):
            pessoa['pessoa_pessoa_juridica'] = {'cnpj': cnpj_cpf}
        
        if id_tipo_pessoa in (3, 4):
            pessoa['estrangeiro'] = True
        else:
            pessoa['estrangeiro'] = False
        
        return pessoa

    def _create_pessoa_from_contrato(self, contrato, cnpj_cpf):
        """Create pessoa object from contrato data."""
        nome = contrato.get('nome_contratado')
        id_tipo_pessoa = contrato.get('id_tipo_pessoa_contrato')
        
        try:
            id_tipo_pessoa = int(float(id_tipo_pessoa)) if id_tipo_pessoa else None
        except (ValueError, TypeError):
            id_tipo_pessoa = None
        
        pessoa = {'nome': nome}
        
        # Pessoa física: id_tipo_pessoa 1 or 4
        if id_tipo_pessoa in (1, 4):
            pessoa['pessoa_fisica'] = {'cpf': cnpj_cpf}
        # Pessoa jurídica: id_tipo_pessoa 2 or 3
        elif id_tipo_pessoa in (2, 3):
            pessoa['pessoa_pessoa_juridica'] = {'cnpj': cnpj_cpf}
        
        # estrangeiro = True if id_tipo_pessoa is 3 or 4
        if id_tipo_pessoa in (3, 4):
            pessoa['estrangeiro'] = True
        else:
            pessoa['estrangeiro'] = False
        
        return pessoa

    def _extract_empenho(self, empenho, empenho_extractors, liquidacao_extractors, pagamento_extractors):
        """Extract empenho with nested liquidacao and pagamento_empenho."""
        # Extract empenho base fields
        extracted = self._extract_with_extractors(
            {'empenho': empenho}, empenho_extractors, 'empenho'
        )
        if not extracted:
            extracted = {}
        
        # Get liquidacao and pagamento lists
        liq_list = empenho.get('liquidacao', []) or []
        pag_list = empenho.get('pagamento_empenho', []) or []
        
        # Check if pagamento matches liquidacao and get match info
        match_result = self._check_liquidacao_pagamento_match(liq_list, pag_list)
        is_matching = match_result['is_matching']
        match_mode = match_result.get('mode')
        pag_by_subempenho = match_result.get('pag_by_subempenho', {})
        
        # Extract liquidacoes
        if liq_list:
            extracted_liquidacoes = []
            for i, liq_item in enumerate(liq_list):
                extracted_liq = self._extract_with_extractors(
                    {'liquidacao': liq_item}, liquidacao_extractors, 'liquidacao'
                )
                if not extracted_liq:
                    extracted_liq = {}
                
                # If matching, include pagamento inside liquidacao
                if is_matching:
                    if match_mode == 'subempenho':
                        # Group by subempenho: nest all pagamentos with matching subempenho
                        sub_id = liq_item.get('id_subempenho_liquidacao')
                        if sub_id and sub_id in pag_by_subempenho:
                            nested_pags = []
                            for pag_item in pag_by_subempenho[sub_id]:
                                extracted_pag = self._extract_with_extractors(
                                    {'pagamento_empenho': pag_item}, pagamento_extractors, 'pagamento_empenho'
                                )
                                if extracted_pag:
                                    nested_pags.append(extracted_pag)
                            if nested_pags:
                                extracted_liq['pagamento_empenho'] = nested_pags
                            # Remove id_subempenho_liquidacao after linking
                            extracted_liq.pop('id_subempenho_liquidacao', None)
                    elif match_mode == 'direct' and i < len(pag_list):
                        # Direct 1:1 match
                        extracted_pag = self._extract_with_extractors(
                            {'pagamento_empenho': pag_list[i]}, pagamento_extractors, 'pagamento_empenho'
                        )
                        if extracted_pag:
                            extracted_liq['pagamento_empenho'] = extracted_pag
                
                if extracted_liq:
                    extracted_liquidacoes.append(extracted_liq)
            
            if extracted_liquidacoes:
                extracted['liquidacao'] = extracted_liquidacoes
        
        # If not matching, add pagamento_empenho as separate list in empenho
        if not is_matching and pag_list:
            extracted_pagamentos = []
            for pag_item in pag_list:
                extracted_pag = self._extract_with_extractors(
                    {'pagamento_empenho': pag_item}, pagamento_extractors, 'pagamento_empenho'
                )
                if extracted_pag:
                    extracted_pagamentos.append(extracted_pag)
            
            if extracted_pagamentos:
                extracted['pagamento_empenho'] = extracted_pagamentos
        
        return extracted if extracted else None

    def _check_liquidacao_pagamento_match(self, liq_list, pag_list):
        """Check if liquidacao and pagamento_empenho match by value.
        
        Supports two matching modes:
        1. Direct 1:1 match: when counts are equal and values match directly
        2. Subempenho grouping: when liquidacao has id_subempenho_liquidacao,
           group pagamentos by id_subempenho_pagamento_empenho and match
           the sum of pagamentos to each liquidacao value
        
        Returns:
            dict with keys:
                - is_matching: bool
                - mode: 'direct', 'subempenho', or None
                - pag_by_subempenho: dict mapping subempenho_id to list of pagamentos (only for subempenho mode)
        """
        if not liq_list or not pag_list:
            return {'is_matching': False, 'mode': None}
        
        # Check if liquidacoes have id_subempenho_liquidacao
        has_subempenho = any('id_subempenho_liquidacao' in liq for liq in liq_list)
        
        if has_subempenho:
            # Group pagamentos by id_subempenho_pagamento_empenho
            pag_by_subempenho = {}
            for pag in pag_list:
                sub_id = pag.get('id_subempenho_pagamento_empenho')
                if sub_id is None:
                    return {'is_matching': False, 'mode': None}
                if sub_id not in pag_by_subempenho:
                    pag_by_subempenho[sub_id] = []
                pag_by_subempenho[sub_id].append(pag)
            
            # Match each liquidacao to its pagamentos group by subempenho id
            for liq in liq_list:
                sub_id = liq.get('id_subempenho_liquidacao')
                if sub_id is None or sub_id not in pag_by_subempenho:
                    return {'is_matching': False, 'mode': None}
                
                liq_val = str(liq.get('valor_liquidacao', '')).replace(',', '.')
                try:
                    liq_float = float(liq_val)
                    pag_sum = sum(
                        float(str(p.get('valor_pagamento', '')).replace(',', '.'))
                        for p in pag_by_subempenho[sub_id]
                    )
                    if abs(liq_float - pag_sum) > 0.005:
                        return {'is_matching': False, 'mode': None}
                except (ValueError, TypeError):
                    return {'is_matching': False, 'mode': None}
            
            return {'is_matching': True, 'mode': 'subempenho', 'pag_by_subempenho': pag_by_subempenho}
        
        # Direct 1:1 match
        if len(liq_list) != len(pag_list):
            return {'is_matching': False, 'mode': None}
        
        for liq, pag in zip(liq_list, pag_list):
            liq_val = str(liq.get('valor_liquidacao', '')).replace(',', '.')
            pag_val = str(pag.get('valor_pagamento', '')).replace(',', '.')
            try:
                if abs(float(liq_val) - float(pag_val)) > 0.005:
                    return {'is_matching': False, 'mode': None}
            except (ValueError, TypeError):
                return {'is_matching': False, 'mode': None}
        
        return {'is_matching': True, 'mode': 'direct'}

    def _extract_with_extractors(self, temp_record, extractors, scope_name):
        """Extract fields using scope extractors."""
        if not extractors:
            return None
        
        extracted = {}
        for field_name, extractor in extractors.items():
            # Skip nested extractors that would cause recursion
            if field_name in ('pessoa', 'liquidacao', 'pagamento_empenho'):
                continue
            try:
                value = extractor.extract(temp_record)
                if value is not None:
                    extracted[field_name] = value
            except Exception:
                pass
        
        return extracted if extracted else None
