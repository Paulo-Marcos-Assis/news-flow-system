from ..base_extractor import BaseExtractor

class TabelaItensECotacoesExtractor(BaseExtractor):
    field_name = "itens_e_cotacoes_completo"
    scope = "item_licitacao"

    def extract(self, record):
        # Listas para cada tabela de destino
        itens_finais = []
        cotacoes_finais = []

        for item_bruto in record.get('listItens', []):
            numero_do_item_atual = item_bruto.get("numero")

            # 1. Monta o objeto para a tabela 'item_licitacao'
            item_limpo = {
                "numero_item": numero_do_item_atual,
                "descricao_item_licitacao": item_bruto.get("denominacao"),
                "qtd_item_licitacao": item_bruto.get("quantidade"),
                "descricao_unidade_medida": item_bruto.get("unidadeMedida"),
                "valor_estimado_item": item_bruto.get("valorUnitarioEstimado"),
                #"situacao_item": item_bruto.get("situacao") # Usando o nome de coluna sugerido
                #TODO: DESCOMENTAR ACIMA QUANDO COLUNA NOVA na tabela 'item_licitacao' coluna 'situacao_item' ESTIVER CRIADA
            }
            itens_finais.append(item_limpo)

            # 2. Monta os objetos para a tabela 'cotacao'
            for vencedor_bruto in item_bruto.get('listVencedores', []):
                cotacao_limpa = {
                    "numero_item_licitacao": numero_do_item_atual, # Chave para ligar à tabela de itens
                    #"nome_fornecedor": vencedor_bruto.get("fornecedor"), #TODO:A inserção deve ser feita na tabela pessoa, e depois relacionada com cotação utilizando a chave estrangeira com pessoa.
                    "qtd_item_cotado": vencedor_bruto.get("quantidade"),
                    "valor_cotado": vencedor_bruto.get("valorUnitario"),
                }
                eh_vencedor = (vencedor_bruto.get("situacao") == "Vencedor")

                if eh_vencedor:
                    cotacao_limpa["vencedor"] = True
                    cotacao_limpa["classificacao"] = 1
                else:
                    cotacao_limpa["vencedor"] = False
                    cotacao_limpa["classificacao"] = None 
                    # Você pode definir uma classificação padrão para não-vencedores
                    # ou simplesmente não adicionar a chave. None é uma boa opção.
                    
                cotacoes_finais.append(cotacao_limpa)
        
        # O retorno é um dicionário com as duas tabelas
        return {
            "item_licitacao": itens_finais,
            "cotacao": cotacoes_finais
        }