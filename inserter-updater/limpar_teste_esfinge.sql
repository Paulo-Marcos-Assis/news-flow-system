-- Script para limpar dados de teste do esfinge1.json
-- Respeita a ordem de dependências de chaves estrangeiras

-- Limpar cotações (dependem de pessoa e item_licitacao)
DELETE FROM cotacao;

-- Limpar tabelas de relacionamento
DELETE FROM processo_licitatorio_pessoa;
DELETE FROM pessoa_pessoa_juridica;
DELETE FROM pessoa_fisica;

-- Limpar objeto_analise (depende de item_licitacao)
DELETE FROM objeto_analise;

-- Limpar empenho e suas dependências
DELETE FROM pagamento_empenho;
DELETE FROM liquidacao;
DELETE FROM movimentacao_empenho;
DELETE FROM empenho;

-- Limpar contratos
DELETE FROM contrato;

-- Limpar documentos
DELETE FROM documento;

-- Limpar itens de licitação
DELETE FROM item_licitacao;

-- Limpar processos licitatórios
DELETE FROM processo_licitatorio;

-- Limpar pessoas
DELETE FROM pessoa;

-- Limpar pessoa_juridica
DELETE FROM pessoa_juridica;

-- Resetar sequences
SELECT setval('pessoa_id_pessoa_seq', 1, false);
SELECT setval('processo_licitatorio_id_processo_licitatorio_seq', 1, false);
SELECT setval('item_licitacao_id_item_licitacao_seq', 1, false);
