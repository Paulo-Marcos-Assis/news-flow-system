from ..base_extractor import BaseExtractor

class TabelaItensECotacoesExtractor(BaseExtractor):

    field_name = "item_licitacao"
    scope = "item_licitacao"

    def extract(self, record):
        itens_processados = {}
            
        lista_de_itens_brutos = record.get('listItens', [])

        for item_bruto in lista_de_itens_brutos:
            numero_do_item_atual = item_bruto.get("numero")


            if numero_do_item_atual not in itens_processados:
                item_limpo = {
                    "numero_sequencial_item": numero_do_item_atual, 
                    "descricao_item_licitacao": item_bruto.get("denominacao"),
                    "qtd_item_licitacao": item_bruto.get("quantidade"), 
                    "descricao_unidade_medida": item_bruto.get("unidadeMedida"),
                    "valor_estimado_item": item_bruto.get("valorUnitarioEstimado"),
                    "situacao_item": item_bruto.get("situacao"),
                    "cotacao": [] # A lista de cotações começa vazia
                }
                itens_processados[numero_do_item_atual] = item_limpo
            
            # Itera sobre cada vencedor (cotação) e anexa ao item PAI
            for vencedor_bruto in item_bruto.get('listVencedores', []):
                
                cotacao_limpa = {
                    "numero_item": numero_do_item_atual,                    
                    "qt_item_cotado": vencedor_bruto.get("quantidade"),
                    "valor_cotado": vencedor_bruto.get("valorUnitario"),
                    "pessoa": {
                        "nome": vencedor_bruto.get("fornecedor")
                    }
                }
                
                eh_vencedor = (vencedor_bruto.get("situacao") == "Vencedor")
                if eh_vencedor:
                    cotacao_limpa["vencedor"] = True
                    cotacao_limpa["classificacao"] = 1
                else:
                    cotacao_limpa["vencedor"] = False
                    cotacao_limpa["classificacao"] = None
                
                itens_processados[numero_do_item_atual]["cotacao"].append(cotacao_limpa)

        return list(itens_processados.values())