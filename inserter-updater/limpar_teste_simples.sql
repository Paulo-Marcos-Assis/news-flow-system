-- Limpar todas as tabelas relacionadas ao teste usando TRUNCATE CASCADE
TRUNCATE TABLE 
    cotacao,
    processo_licitatorio_pessoa,
    pessoa_pessoa_juridica,
    pessoa_fisica,
    pessoa,
    item_licitacao,
    processo_licitatorio,
    empenho,
    liquidacao,
    pagamento_empenho,
    movimentacao_empenho,
    contrato,
    documento
RESTART IDENTITY CASCADE;
