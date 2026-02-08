from ..base_nested_extractor import BaseNestedExtractor


class PagamentoEmpenhoNestedExtractor(BaseNestedExtractor):
    field_name = "pagamento_empenho"
    scope = "empenho"
    nested_key = "pagamento_empenho"
    nested_scope = "pagamento_empenho"

    def extract(self, record):
        """Extract pagamento_empenho only when NOT matching 1:1 with liquidacao."""
        empenho_data = record.get(self.scope, {})
        
        liq_list = empenho_data.get('liquidacao', [])
        pag_list = empenho_data.get('pagamento_empenho', [])
        
        if not pag_list or not isinstance(pag_list, list):
            return None
        
        # Check if pagamento matches liquidacao 1:1
        is_matching = len(liq_list) == len(pag_list) and len(liq_list) > 0
        
        if is_matching:
            # Verify values match
            for liq, pag in zip(liq_list, pag_list):
                liq_val = liq.get('valor_liquidacao', '').replace(',', '.')
                pag_val = pag.get('valor_pagamento', '').replace(',', '.')
                try:
                    if abs(float(liq_val) - float(pag_val)) > 0.01:
                        is_matching = False
                        break
                except:
                    is_matching = False
                    break
        
        # If matching, skip - pagamento is inside liquidacao
        if is_matching:
            return None
        
        # Otherwise, use default extraction
        return super().extract(record)
