--
-- PostgreSQL database dump
--

\restrict ucowgYN9nPi6c7IOkyPUTTgOnTIB53qWv00APmAlMVsamFgCl6LO4APA2YEJ0lc

-- Dumped from database version 15.15
-- Dumped by pg_dump version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: audit; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA audit;


--
-- Name: dblink; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS dblink WITH SCHEMA public;


--
-- Name: EXTENSION dblink; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION dblink IS 'connect to other PostgreSQL databases from within a database';


--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';

CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA public; 

COMMENT ON EXTENSION unaccent IS 'text search dictionary that removes accents';


--
-- Name: adicionar_usuario(text, text, text, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.adicionar_usuario(cpf_adicionar text, nome_adicionar text, email_adicionar text, tipo_acesso_adicionar text) RETURNS text
    LANGUAGE plpgsql
    AS $_$
begin
	insert into audit.users (cpf, nome, email, tipo_acesso) values ($1::text, $2::text, $3::text, coalesce($4, 'completo'));
	update audit.users set cpf_crypt = pgp_sym_encrypt(cpf, 'ceos') where cpf = $1::text;
	return 'Adicionado!';
end
$_$;


--
-- Name: barra_busca_produto(text, date, date, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.barra_busca_produto(_termo text, _data_inicio date DEFAULT NULL::date, _data_fim date DEFAULT NULL::date, _limite_respostas integer DEFAULT 5) RETURNS TABLE(descricao_produto text, id_grupo bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        v.descricao_produto,
        v.id_grupo_bp::BIGINT
    FROM
        public.item_nfe v
	JOIN 
		public.nfe AS nf ON v.id_nfe = nf.id_nfe
    WHERE
        v.descricao_produto ILIKE _termo || '%' AND v.ncm_produto LIKE '3004%' AND v.id_grupo_bp is not null
        AND (
            _data_inicio IS NULL OR nf.data_emissao >= _data_inicio
        )
        AND (
            _data_fim IS NULL OR nf.data_emissao <= _data_fim
        )
    LIMIT _limite_respostas;
END;
$$;


--
-- Name: barra_busca_produto2(text, date, date, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.barra_busca_produto2(_termo text, _data_inicio date DEFAULT NULL::date, _data_fim date DEFAULT NULL::date, _limite_respostas integer DEFAULT 5) RETURNS TABLE(descricao_produto text, id_grupo bigint)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        v.descricao_produto,
        v.id_grupo_bp::BIGINT
    FROM
        public.item_nfe v
        JOIN public.nfe nf ON v.id_nfe = nf.id_nfe
    WHERE
        v.ncm_produto LIKE '3004%'
        AND v.id_grupo_bp IS NOT NULL
        AND (
            _data_inicio IS NULL OR nf.data_emissao >= _data_inicio
        )
        AND (
            _data_fim IS NULL OR nf.data_emissao <= _data_fim
        )
        -- 🔍 Para cada palavra, verifica se está contida na descrição
        AND NOT EXISTS (
            SELECT 1
            FROM regexp_split_to_table(_termo, '\s+') AS palavra
            WHERE v.descricao_produto ILIKE '%' || palavra || '%' = FALSE
        )
    LIMIT _limite_respostas;
END;
$$;


--
-- Name: bloquear_insert(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.bloquear_insert() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    RAISE EXCEPTION 'Inserções estão temporariamente desabilitadas nesta tabela.';
END;
$$;


--
-- Name: cancelar_remocao_item_bp(bigint, bigint, integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.cancelar_remocao_item_bp(p_id_pessoa bigint, p_id_grupo_bp bigint, p_id_banco_preco integer DEFAULT NULL::integer, p_id_nfe integer DEFAULT NULL::integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    DELETE FROM teste.items_removidos_bp
    WHERE
        id_pessoa = p_id_pessoa
        AND id_grupo_bp = p_id_grupo_bp
        AND id_banco_de_precos IS NOT DISTINCT FROM p_id_banco_preco
        AND id_nfe IS NOT DISTINCT FROM p_id_nfe;
END;
$$;


--
-- Name: consulta_empresas(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.consulta_empresas(cnpj_consulta text) RETURNS TABLE(id integer, nome text, cnpj text, porte_empresa text)
    LANGUAGE sql SECURITY DEFINER
    AS $$
select 
    pj.id_pessoa, 
    pj.razao_social, 
    pj.cnpj,
    case 
        when pj.porte_empresa = 0 then 'Não Informado'
        when pj.porte_empresa = 1 then 'Micro Empresa'
        when pj.porte_empresa = 3 then 'Pequeno Porte'
        when pj.porte_empresa = 5 then 'Demais'
    end as porte_empresa


from pessoa_juridica as pj where  pj.cnpj = cnpj_consulta
--where regexp_replace(pj.cpf_ou_cnpj, '[^0-9]', '', 'g') = regexp_replace(cnpj_consulta, '[^0-9]', '', 'g')
 -- and pj.eh_pessoa_juridica is true;
$$;


--
-- Name: consulta_usuarios(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.consulta_usuarios(consultado text) RETURNS TABLE(tipo_acesso text, cpf text)
    LANGUAGE plpgsql SECURITY DEFINER ROWS 1
    AS $$

declare
	funcao text;
BEGIN
	funcao := (select u.nome from audit.users u where u.cpf = consultado);
	insert into audit.log_painel (usuario, consulta) VALUES (funcao, 'login');
	return query (select u.tipo_acesso, u.cpf from audit.users u where u.cpf = consultado);
END;
$$;


--
-- Name: empresas_por_licitacao(integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.empresas_por_licitacao(id_processo integer) RETURNS TABLE(id integer, cnpj character varying, nome_empresa text, capital_social double precision, porte_empresa text, cpf_ou_cnpj text, cotacoes text, valor_total_cotacao numeric, valor_total_vencido numeric, vencedores text, id_pessoa text, nome text, cargo text, idade text, cpf text)
    LANGUAGE sql SECURITY DEFINER
    AS $$
SELECT
	co.id_pessoa,
    pes_jur.cnpj AS cnpj,
    pes_juridica.razao_social AS nome_empresa,
    CAST(pes_juridica.capital_social AS double precision) AS capital_social,
    CASE
        WHEN pes_juridica.porte_empresa = 0 THEN 'Não Informado'
        WHEN pes_juridica.porte_empresa = 1 THEN 'Micro Empresa'
        WHEN pes_juridica.porte_empresa = 2 THEN 'Pequeno Porte'
        WHEN pes_juridica.porte_empresa = 3 THEN 'Demais'
    END AS porte_empresa,
    CASE 
        WHEN length(pes_juridica.cnpj::text) = 11 THEN 'cpf'
        ELSE 'cnpj'
    END AS cpf_ou_cnpj,

    -- lista de ids de cotações (itens)
    STRING_AGG(DISTINCT co.id_item_licitacao::text, ', ') AS cotacoes,
    -- soma total das cotações
    ROUND(SUM(co.valor_cotado)::numeric, 2) AS valor_total_cotacao,

    -- soma apenas dos vencedores
    ROUND(SUM(CASE WHEN co.vencedor IS TRUE THEN co.valor_cotado ELSE 0 END)::numeric, 2) AS valor_total_vencido,

    STRING_AGG(co.id_item_licitacao::text, ', ') FILTER (WHERE co.vencedor IS TRUE) AS vencedores,
	
	--array_agg(co.id_item_licitacao) FILTER (WHERE co.vencedor IS TRUE) AS vencedores
	STRING_AGG(pessoa_fisica.id_pessoa::text, ',') as id_pessoa,
	STRING_AGG(pess.nome::text, ',') as nome,
	STRING_AGG(pes_fis_est.cargo::text, ',') as cargo,
    STRING_AGG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, pessoa_fisica.data_nascimento))::text, ',') as idade,
	STRING_AGG(pessoa_fisica.cpf::text, ',') as cpf
	
	
			
FROM
    cotacao co
	LEFT JOIN pessoa_juridica as pes_juridica
		ON pes_juridica.id_pessoa = co.id_pessoa
    LEFT JOIN pessoa_pessoa_juridica as pes_jur 
        ON co.id_pessoa = pes_jur.id_pessoa
    left JOIN item_licitacao il
        ON co.id_item_licitacao = il.id_item_licitacao
	left Join estabelecimento as est
		on est.cnpj = pes_juridica.cnpj
	left join pessoa_fisica_estabelecimento as pes_fis_est
		on pes_fis_est.id_estabelecimento = est.id_estabelecimento 
	left  join pessoa_fisica as pessoa_fisica
		on pessoa_fisica.cpf = pes_fis_est.cpf
	left join pessoa as pess
		on pess.id_pessoa = pes_jur.id_pessoa
WHERE 
    il.id_processo_licitatorio = id_processo
GROUP BY
    pes_jur.cnpj,
	pes_juridica.cnpj,
    pes_juridica.razao_social,
    pes_juridica.capital_social,
	co.id_pessoa,
	co.vencedor,
    pes_juridica.porte_empresa;
$$;


--
-- Name: func_alertas_licitacao(bigint); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.func_alertas_licitacao(id_licitacao bigint) RETURNS TABLE(id_alerta bigint, id_processo_licitatorio bigint, nome text, nivel smallint, id_categoria integer, categoria text, descricao_categoria text, descricao_curta text, descricao_longa text, data_ultima_execucao date, cpf text, pessoas_fisicas text, empresas text, produtos text, metodo_analise text)
    LANGUAGE sql SECURITY DEFINER
    AS $$
	SELECT al.id_alerta, fa.id_processo_licitatorio, al.nome, al.nivel, CA.id_categoria_alerta, CA.nome as categoria, CA.descricao as descricao_categoria, al.descricao_curta, al.descricao_longa, al.data_ultima_execucao, 
    STRING_AGG(us_al.cpf, ', ') AS usuarios_ignoraram, --    COUNT(us_al.id_usuario) AS qtd_usuarios_ignoraram
	STRING_AGG(pessoa.id_pessoa::text, ', ') AS pessoas_fisicas,
    STRING_AGG(pessoa.id_pessoa::text, ', ') AS empresas,
	STRING_AGG(DISTINCT item.id_item_licitacao::text, ', ') AS produtos,
	met_analise.metodologia
	

	FROM alerta al
	LEFT JOIN categoria_alerta CA ON CA.id_categoria_alerta = al.id_categoria_alerta
	LEFT JOIN usuario_alerta_ignorado us_al ON us_al.id_alerta = al.id_alerta
	LEFT JOIN processo_licitatorio_pessoa proc_lic_pes ON proc_lic_pes.id_processo_licitatorio = id_licitacao
	LEFT JOIN pessoa pessoa ON pessoa.id_pessoa = proc_lic_pes.id_pessoa  
	LEFT JOIN pessoa_fisica pessoa_fisica ON pessoa_fisica.id_pessoa = pessoa.id_pessoa 
	LEFT JOIN pessoa_juridica pessoa_juridica ON pessoa_juridica.id_pessoa = pessoa.id_pessoa 
	LEFT JOIN item_licitacao item ON item.id_processo_licitatorio = id_licitacao
	LEFT JOIN execucao_alerta ex_alerta ON ex_alerta.id_alerta = al.id_alerta
	LEFT JOIN metodo_analise met_analise ON met_analise.id_metodo_analise = ex_alerta.id_metodo_analise
	left join destino_alerta da ON da.id_alerta = al.id_alerta
	left join fonte_alerta fa ON fa.id_fonte_alerta = da.id_fonte_alerta
	
	WHERE fa.id_processo_licitatorio = id_licitacao  
	
	group by al.id_alerta, fa.id_processo_licitatorio, al.nome, al.nivel, CA.id_categoria_alerta, CA.nome, met_analise.metodologia
$$;


--
-- Name: func_sobre_alertas(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.func_sobre_alertas() RETURNS TABLE(id_categoria_alerta integer, nome text, descricao text)
    LANGUAGE sql
    AS $$
SELECT id_categoria_alerta, nome, descricao FROM categoria_alerta
WHERE id_categoria_alerta <> 1
$$;


--
-- Name: get_entes(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_entes() RETURNS TABLE(ente text, id_ente integer)
    LANGUAGE sql
    AS $$
SELECT ente, id_ente FROM ente
$$;


--
-- Name: get_item(integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_item(p_id_item_licitacao integer, p_id_processo_licitatorio integer) RETURNS TABLE(id_documento integer, v_min_6m double precision, v_med_6m double precision, v_max_6m double precision, v_min_12m double precision, v_med_12m double precision, v_max_12m double precision, q1 double precision, q2 double precision, q3 double precision, q4 double precision, q5 double precision, q6 double precision)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        fonte_alerta.id_documento,
        estatisticas_alinhadas.v_min_6m,
        estatisticas_alinhadas.v_med_6m,
        estatisticas_alinhadas.v_max_6m,
        estatisticas_alinhadas.v_min_12m,
        estatisticas_alinhadas.v_med_12m,
        estatisticas_alinhadas.v_max_12m,
        estatisticas_alinhadas.q1,
        estatisticas_alinhadas.q2,
        estatisticas_alinhadas.q3,
        estatisticas_alinhadas.q4,
        estatisticas_alinhadas.q5,
        estatisticas_alinhadas.q6
    FROM
        item_licitacao AS item_lic
    JOIN item_nfe AS item_nfe ON item_lic.id_item_licitacao = item_nfe.id_item_licitacao
    JOIN banco_de_precos AS banco_precos ON item_nfe.id_item_nfe = banco_precos.id_item_nfe
    JOIN fonte_alerta AS fonte_alerta ON item_nfe.id_item_nfe = fonte_alerta.id_item_nfe
    CROSS JOIN LATERAL (
        SELECT
            MAX(estatisticas.valor_estatistica) FILTER (WHERE estatisticas.tipo_estatistica = 'valor_minimo_6m') AS v_min_6m,
            MAX(estatisticas.valor_estatistica) FILTER (WHERE estatisticas.tipo_estatistica = 'valor_medio_6m')  AS v_med_6m,
            MAX(estatisticas.valor_estatistica) FILTER (WHERE estatisticas.tipo_estatistica = 'valor_maximo_6m') AS v_max_6m,
            MAX(estatisticas.valor_estatistica) FILTER (WHERE estatisticas.tipo_estatistica = 'valor_minimo_12m') AS v_min_12m,
            MAX(estatisticas.valor_estatistica) FILTER (WHERE estatisticas.tipo_estatistica = 'valor_medio_12m')  AS v_med_12m,
            MAX(estatisticas.valor_estatistica) FILTER (WHERE estatisticas.tipo_estatistica = 'valor_maximo_12m') AS v_max_12m,
            MAX(estatisticas.valor_estatistica) FILTER (WHERE estatisticas.tipo_estatistica = 'quartil1') AS q1,
            MAX(estatisticas.valor_estatistica) FILTER (WHERE estatisticas.tipo_estatistica = 'quartil2') AS q2,
            MAX(estatisticas.valor_estatistica) FILTER (WHERE estatisticas.tipo_estatistica = 'quartil3') AS q3,
            MAX(estatisticas.valor_estatistica) FILTER (WHERE estatisticas.tipo_estatistica = 'quartil4') AS q4,
            MAX(estatisticas.valor_estatistica) FILTER (WHERE estatisticas.tipo_estatistica = 'quartil5') AS q5,
            MAX(estatisticas.valor_estatistica) FILTER (WHERE estatisticas.tipo_estatistica = 'quartil6') AS q6
        FROM
            estatistica_item_bp AS estatisticas
        WHERE
            estatisticas.id_banco_de_precos = banco_precos.id_banco_de_precos
    ) AS estatisticas_alinhadas
    WHERE
        item_lic.id_item_licitacao = p_id_item_licitacao
        AND item_lic.id_processo_licitatorio = p_id_processo_licitatorio;
END;
$$;


--
-- Name: get_nfe_and_items_by_id(integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_nfe_and_items_by_id(p_id_nfe integer) RETURNS TABLE(id_nfe integer, cnpj_emitente text, nome_emitente character varying, ie_emitente character varying, uf_emitente character varying, cnpj_destinatario text, nome_destinatario character varying, ie_destinatario character varying, uf_destinatario character varying, chave_acesso text, num_serie_nfe integer, data_emissao date, id_item_nfe integer, descricao_produto text, quantidade_comercial double precision, unidade_comercial character varying, valor_unitario_comercial double precision, ncm_produto character varying)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id_nfe,
        a.cnpj_emitente,
        a.nome_emitente,    
        a.ie_emitente,      
        a.uf_emitente,      
        a.cnpj_destinatario,
        a.nome_destinatario,
        a.ie_destinatario,
        a.uf_destinatario,
        a.chave_acesso,
		a.num_serie_nfe,
		a.data_emissao,
        b.id_item_nfe,
        b.descricao_produto,
        b.quantidade_comercial,
        b.unidade_comercial,
        b.valor_unitario_comercial,
		b.ncm_produto
    FROM
        public.nfe a
    LEFT JOIN
        item_nfe b ON a.id_nfe = b.id_nfe
    WHERE
        a.id_nfe = p_id_nfe; 
END;
$$;


--
-- Name: get_unidadegestora(integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_unidadegestora(entrada_ente integer) RETURNS TABLE(nome_ug text, id_unidade_gestora integer)
    LANGUAGE sql
    AS $$
    SELECT ug.nome_ug, ug.id_unidade_gestora
    FROM unidade_gestora ug
    WHERE ug.id_ente = entrada_ente;
$$;


--
-- Name: impedir_alteracao(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.impedir_alteracao() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    RAISE EXCEPTION 'Tabela MUNICIPIO bloqueada para manutenção/segurança.';
END;
$$;


--
-- Name: item_tabela(bigint, bigint); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.item_tabela(id_licitacao bigint, id_empresa bigint) RETURNS TABLE(id_item bigint, descricao_item text, vencedor boolean, valor_cotado_item double precision, qnt integer)
    LANGUAGE sql SECURITY DEFINER
    AS $$
    select 
		c.id_item_licitacao as id_item,
		descricao_item_licitacao as descricao,
		vencedor as vencedor,
		valor_cotado as valor,
		qt_item_cotado as quantidade
	from
		cotacao c join (select id_item_licitacao, descricao_item_licitacao, id_processo_licitatorio from item_licitacao) p
		on c.id_item_licitacao = p.id_item_licitacao
	where 
		id_pessoa = id_empresa 
	and
		p.id_processo_licitatorio = id_licitacao
	order by c.id_item_licitacao
$$;


--
-- Name: itens_por_licitacao(integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.itens_por_licitacao(id_processo integer) RETURNS TABLE(id_item_licitacao bigint, numero_sequencial_item bigint, descricao_item_licitacao text, data_homologacao date, qtd_item_licitacao text, descricao_unidade_medida text, valor_total_cotado_item numeric, nome_vencedor text)
    LANGUAGE sql SECURITY DEFINER
    AS $$
SELECT
    il.id_item_licitacao,
    il.numero_sequencial_item,
    il.descricao_item_licitacao,
    il.data_homologacao,
    il.qtd_item_licitacao,
    il.descricao_unidade_medida,
    co.valor_cotado as valor_total_cotado_item,
    pe.nome as nome_vencedor

FROM item_licitacao il

-- Join para pegar os dados da cotação (valor, id do vencedor, etc)
LEFT JOIN (
    SELECT id_item_licitacao, id_pessoa, valor_cotado, vencedor FROM cotacao) 
	co ON co.id_item_licitacao = il.id_item_licitacao
	
-- Join com a tabela "processo_licitatorio_pessoa" para usar uma chave estrangeira que liga o processo à pessoa
LEFT JOIN processo_licitatorio_pessoa ppl ON ppl.id_pessoa = co.id_pessoa

-- Join com a tabela 'pessoa' para obter o nome do vencedor
LEFT JOIN pessoa pe ON pe.id_pessoa = ppl.id_pessoa

WHERE il.id_processo_licitatorio = id_processo
AND co.vencedor <> FALSE
ORDER BY numero_sequencial_item;
$$;


--
-- Name: licitacao(integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.licitacao(id_processo integer) RETURNS TABLE(id bigint, numero_processo_licitatorio text, objeto text, edital text, processos_sig text, valor_previsto double precision, valor_contratado double precision, diferenca double precision, modalidade text, tipo_licitacao text, situacao text, ente text, unidade_gestora integer, ano_abertura timestamp without time zone, ano_fim timestamp without time zone)
    LANGUAGE sql SECURITY DEFINER ROWS 1
    AS $_$
	select
    pl.id_processo_licitatorio, -- id
    pl.numero_processo_licitatorio, -- processo licitatorio (removido no novo banco)
    pl.descricao_objeto, -- objeto
    pl.numero_edital, -- edital
    null::int as processos_sig, -- processos sig (precisa de análise mais detalhada)
    pl.valor_total_previsto, -- valor previsto
    sum(c.valor_contrato) as valor_contrato, -- soma dos valores de contratado
    (sum(c.valor_contrato) - (pl.valor_total_previsto)::double precision) as diferenca, -- soma diferenca
	ml.descricao AS modalidade,
    tl.descricao as tipo_licitacao, -- tipo
    --sp.descricao as situacao, -- situacao
	pl.situacao as situacao, --situacao
	et.ente, -- ente,
	ug.id_unidade_gestora, -- unidade_gestora
    pl.data_abertura_certame, -- ano abertura
    max(c.data_vencimento) as data_vencimento -- ano fim
	 -- Dados do Órgão Público (para agrupar)
    --est.id_estabelecimento,
    --est.nome_fantasia,

    -- Dados da Pessoa (para a lista interna)
    -- STRING_AGG(pes.id_pessoa::text, ',') AS id_pessoa,
    -- STRING_AGG(pes.nome::text, ',') AS nome_pessoa,    
    -- STRING_AGG(pes_est.cargo::text, ',') AS cargo,
	-- STRING_AGG(pes_fis.data_nascimento::text, ',') AS data_nascimento,
    -- STRING_AGG(pes_fis.cpf::text, ',') AS cpf

	
from processo_licitatorio pl
left join contrato c
    on c.id_processo_licitatorio = pl.id_processo_licitatorio
LEFT JOIN modalidade_licitacao ml ON ml.id_modalidade_licitacao = pl.id_modalidade_licitacao
left join tipo_licitacao tl
    on tl.id_tipo_licitacao = pl.id_tipo_licitacao

--LEFT JOIN processo_licitatorio_pessoa pl_pes ON pl_pes.id_processo_licitatorio = pl.id_processo_licitatorio
--LEFT JOIN pessoa pes ON pes.id_pessoa = pl_pes.id_pessoa 
--LEFT JOIN pessoa_juridica pes_juridic ON pes_juridic.id_pessoa = pl_pes.id_processo_licitatorio 
--LEFT JOIN estabelecimento est ON est.cnpj = pes_juridic.cnpj AND est.eh_orgao_publico = true
--LEFT JOIN pessoa_fisica_estabelecimento pes_est ON pes_est.id_estabelecimento = est.id_estabelecimento
--LEFT JOIN pessoa_fisica pes_fis ON pes_fis.id_pessoa = pl_pes.id_pessoa

--LEFT JOIN processo_licitatorio_pessoa pl_pes ON pl_pes.id_processo_licitatorio = pl.id_proce--sso_licitatorio
--LEFT JOIN pessoa_fisica_estabelecimento pes_est ON pes_est.id_pessoa = pl_pes.id_pessoa
--LEFT JOIN estabelecimento est ON est.id_estabelecimento = pes_est.id_estabelecimento AND est.eh_orgao_publico = true
--LEFT JOIN pessoa pes ON pes.id_pessoa = pl_pes.id_pessoa and pes.eh_pessoa_juridica is false 

JOIN unidade_gestora ug ON ug.id_unidade_gestora = pl.id_unidade_gestora
JOIN ente et ON ug.id_ente = et.id_ente
where pl.id_processo_licitatorio = $1
	--and est.eh_orgao_publico is true 
group by
    pl.id_processo_licitatorio,
    --pl.numero_processo_licitatorio,
    pl.descricao_objeto,
    pl.numero_edital,
    pl.valor_total_previsto,
    tl.descricao,
    pl.situacao,
    -- sp.descricao,
	et.ente,
	ug.id_unidade_gestora,
	ml.descricao,
    pl.data_abertura_certame;
	--est.nome_fantasia,
	--est.eh_orgao_publico,
    --est.id_estabelecimento;

$_$;


--
-- Name: lista_geral_documentos(bigint); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.lista_geral_documentos(p_id_licitacao bigint) RETURNS TABLE(nome_arquivo text, data_emissao timestamp without time zone, tipo_documento text, tamanho text, local_acesso_arquivo text, id_registro bigint)
    LANGUAGE sql SECURITY DEFINER
    AS $$
    SELECT
        d.nome_arquivo,
        d.data_emissao,
        'Documento' AS tipo_documento, 
        d.tamanho,
        d.local_acesso_arquivo,
        d.id_documento::bigint AS id_registro
    FROM
        documento AS d
       -- JOIN tipo_documento td ON td.id_tipo_documento = d.id_tipo_documento
    WHERE
        d.id_processo_licitatorio = p_id_licitacao

    UNION ALL

    SELECT
        'Nota Fiscal' AS nome_arquivo,
        nfe.data_emissao,
        'NFe' AS tipo_documento,
        NULL::text AS tamanho,
        nfe.chave_acesso AS local_acesso_arquivo,
        nfe.id_nfe::bigint AS id_registro
    FROM
        nfe
    WHERE
        nfe.id_processo_licitatorio = p_id_licitacao;
$$;


--
-- Name: mc_busca_itens_gupo(bigint, date, date); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.mc_busca_itens_gupo(produto_query bigint DEFAULT NULL::bigint, data_inicio date DEFAULT NULL::date, data_fim date DEFAULT NULL::date) RETURNS TABLE(id_grupo bigint, descricao_produto text, gtin_produto character varying, nfe_id text, data_emissao_nota date, quantidade_comercial double precision, unidade_comercial character varying, valor_unitario_comercial double precision, chave_acesso text)
    LANGUAGE sql
    AS $$
SELECT
    vf.id_grupo_bp,
    vf.descricao_produto,
    vf.gtin_produto,
    vf.id_nfe,
    nf.data_emissao,
    vf.quantidade_comercial,
    vf.unidade_comercial,
    vf.valor_unitario_comercial,
	nf.chave_acesso
FROM
    public.item_nfe AS vf
JOIN
	public.nfe AS nf on vf.id_nfe = nf.id_nfe
WHERE
    (vf.id_grupo_bp = produto_query OR produto_query IS NULL)
    AND (nf.data_emissao >= data_inicio OR data_inicio IS NULL)
    AND (nf.data_emissao <= data_fim OR data_fim IS NULL);
$$;


--
-- Name: registrar_alerta_ignorado(integer, bigint); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.registrar_alerta_ignorado(p_id_alerta integer, p_id_user bigint) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Verifica se o usuário existe usando o parâmetro
    IF NOT EXISTS (SELECT 1 FROM audit.users WHERE id_pessoa = p_id_user) THEN
        -- Lança uma exceção clara se o usuário não for encontrado
        RAISE EXCEPTION 'Usuário com id % não encontrado.', p_id_user;
    END IF;

INSERT INTO usuario_alerta_ignorado (cpf, id_alerta)
    SELECT
        u.cpf,
        p_id_alerta
    FROM
        audit.users u
    WHERE
        u.id_pessoa = p_id_user
    ON CONFLICT (cpf, id_alerta) DO NOTHING;
END;
$$;


--
-- Name: remover_alerta_ignorado(integer, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.remover_alerta_ignorado(p_id_alerta integer, p_id_user text) RETURNS TABLE(cpf text, id_alerta integer)
    LANGUAGE sql
    AS $$
	DELETE FROM usuario_alerta_ignorado ua
	WHERE ua.id_alerta = p_id_alerta
		AND ua.cpf = p_id_user
	RETURNING ua.cpf, ua.id_alerta;
$$;


--
-- Name: remover_item_bp_novo_ceos(bigint, bigint, integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.remover_item_bp_novo_ceos(p_id_pessoa bigint, p_id_grupo_bp bigint, p_id_banco_preco integer DEFAULT NULL::integer, p_id_nfe integer DEFAULT NULL::integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    /*
     * Verifica se os IDs fornecidos existem nas tabelas de referência antes de permitir a inserção.
     */

    -- Verificação 1: Usuário (p_id_pessoa)
    IF NOT EXISTS (SELECT 1 FROM audit.users WHERE id_pessoa = p_id_pessoa) THEN
        RAISE EXCEPTION 'Usuário (id_pessoa=%) não encontrado em audit.users.', p_id_pessoa
            USING ERRCODE = 'P0001'; -- 'P0001' é um código de erro customizado
    END IF;

    -- Verificação 2: Grupo BP (p_id_grupo_bp)

    IF NOT EXISTS (SELECT 1 FROM grupo_bp WHERE id_grupo_bp = p_id_grupo_bp) THEN
        RAISE EXCEPTION 'Grupo BP (id_grupo_bp=%) não encontrado.', p_id_grupo_bp
            USING ERRCODE = 'P0002';
    END IF;

    -- Verificação 3: Banco de Preço (p_id_banco_preco), se informado
    IF p_id_banco_preco IS NOT NULL THEN
        IF NOT EXISTS (SELECT 1 FROM banco_de_precos WHERE id_banco_precos = p_id_banco_preco) THEN
            RAISE EXCEPTION 'Banco de Preço (id_banco_precos=%) não encontrado.', p_id_banco_preco
                USING ERRCODE = 'P0003';
        END IF;
    END IF;
    
    -- Verificação 4: Item NFe (p_id_nfe), se informado
    IF p_id_nfe IS NOT NULL THEN
        IF NOT EXISTS (SELECT 1 FROM item_nfe WHERE id_nfe = p_id_nfe) THEN
            RAISE EXCEPTION 'Item NFe (id_nfe=%) não encontrado.', p_id_nfe
                USING ERRCODE = 'P0004';
        END IF;
    END IF;

    INSERT INTO teste.items_removidos_bp (
        id_pessoa,
        id_grupo_bp,
        id_banco_de_precos,
        id_nfe,
        data_remocao
    )
    VALUES (
        p_id_pessoa,
        p_id_grupo_bp,
        p_id_banco_preco,
        p_id_nfe,
        NOW() -- Define a data de remoção para o momento atual
    )
    ON CONFLICT DO NOTHING;

END;
$$;


--
-- Name: schema_dinamico(text, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.schema_dinamico(nome_tabela text, nome_schema text DEFAULT 'public'::text) RETURNS TABLE(column_name text, data_type text, is_nullable text, column_default text, is_primary_key boolean)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
    c.column_name::text,
    c.data_type::text,
    c.is_nullable::text,
    c.column_default::text,
    (kcu.column_name IS NOT NULL) AS is_primary_key
	FROM information_schema.columns c
	LEFT JOIN information_schema.key_column_usage kcu
	    ON c.table_name = kcu.table_name
	    AND c.column_name = kcu.column_name
	    AND c.table_schema = kcu.table_schema
	WHERE c.table_name = nome_tabela AND c.table_schema = nome_schema
ORDER BY c.ordinal_position;
END;
$$;


--
-- Name: tabelas_do_schema(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.tabelas_do_schema(p_nome_schema text DEFAULT 'public'::text) RETURNS TABLE(table_name text)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT t.table_name::text
    FROM information_schema.tables AS t
    WHERE t.table_schema = p_nome_schema
      AND t.table_type = 'BASE TABLE'
    ORDER BY t.table_name;
END;
$$;


--
-- Name: teste_permissao(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.teste_permissao() RETURNS integer
    LANGUAGE sql
    AS $$
    SELECT id_processo_licitatorio FROM processo_licitatorio LIMIT 1;
$$;


--
-- Name: todas_licitacoes(integer, text, text, date, date, date, date, text, text, text, text, text, text, text, text, integer, boolean, boolean, boolean, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.todas_licitacoes(p_id_procedimento_licitatorio integer DEFAULT NULL::integer, num_licitacao text DEFAULT NULL::text, num_edital text DEFAULT NULL::text, data_abertura_inicio date DEFAULT NULL::date, data_abertura_fim date DEFAULT NULL::date, data_fechamento_inicio date DEFAULT NULL::date, data_fechamento_fim date DEFAULT NULL::date, ent text DEFAULT NULL::text, uni_gest text DEFAULT NULL::text, obj text DEFAULT NULL::text, situ text DEFAULT NULL::text, modal text DEFAULT NULL::text, empresa text DEFAULT NULL::text, sort_column text DEFAULT 'alertas'::text, sort_dir text DEFAULT 'desc'::text, pag integer DEFAULT 1, p_com_documento boolean DEFAULT NULL::boolean, p_com_nfe boolean DEFAULT NULL::boolean, p_com_proc_sig boolean DEFAULT NULL::boolean, limite integer DEFAULT 10) RETURNS TABLE(processo_licitatorio text, numero_processo_lict text, edital text, objeto text, processos_sig text, valor_previsto double precision, valor_contratado text, diferenca text, modalidade text, tipo_licitacao text, situacao text, ente text, unidade_gestora text, ano_abertura date, ano_fim text, nivel_1 integer, nivel_2 integer, nivel_3 integer, total_documento integer, total_nfe integer)
    LANGUAGE sql SECURITY DEFINER
    AS $$
SELECT 
    pl.id_procedimento_licitatorio,
    pl.numero_processo_licitatorio,
    pl.numero_edital,
    pl.descricao_objeto,
    pl.processos_sig,
    pl.valor_total_previsto,
    pl.valor_contrato,
    pl.diferenca,
    pl.modalidade,
    pl.tipo_documento,
    pl.situacao,
    pl.ente,
    pl.nome_ug,
    pl.data_abertura_certame,
    pl.data_vencimento,
    (
        SELECT COUNT(*) 
        FROM objeto_analise obj
         JOIN execucao_metodo_objeto_analise da ON da.id_objeto_analise = obj.id_objeto_analise
         JOIN execucao_metodo em ON em.id_execucao_metodo = da.id_execucao_metodo
         JOIN alerta al ON em.id_execucao_metodo = al.id_execucao_metodo
         WHERE obj.id_processo_licitatorio = pl.id_procedimento_licitatorio
        AND al.nivel = 1
    ) AS nivel_1,
    (
        SELECT COUNT(*) 
        FROM objeto_analise obj
         JOIN execucao_metodo_objeto_analise da ON da.id_objeto_analise = obj.id_objeto_analise
         JOIN execucao_metodo em ON em.id_execucao_metodo = da.id_execucao_metodo
         JOIN alerta al ON em.id_execucao_metodo = al.id_execucao_metodo
         WHERE obj.id_processo_licitatorio = pl.id_procedimento_licitatorio
        AND al.nivel = 2
    ) AS nivel_2,
    (
        SELECT COUNT(*) 
        FROM objeto_analise obj
         JOIN execucao_metodo_objeto_analise da ON da.id_objeto_analise = obj.id_objeto_analise
         JOIN execucao_metodo em ON em.id_execucao_metodo = da.id_execucao_metodo
         JOIN alerta al ON em.id_execucao_metodo = al.id_execucao_metodo
         WHERE obj.id_processo_licitatorio = pl.id_procedimento_licitatorio
        AND al.nivel = 3
    ) AS nivel_3,
    (
        SELECT COUNT(DISTINCT d.id_tipo_documento)
        FROM documento d
        WHERE d.id_processo_licitatorio = pl.id_procedimento_licitatorio
          AND d.id_tipo_documento IS NOT NULL
    ) AS total_documento,
    (
        SELECT COUNT(DISTINCT pl3.id_nfe)
        FROM view_processo_licitatorio_filtro pl3
        WHERE pl3.id_procedimento_licitatorio = pl.id_procedimento_licitatorio
          AND pl3.id_nfe IS NOT NULL
    ) AS total_nfe
FROM view_processo_licitatorio_filtro pl
WHERE (p_id_procedimento_licitatorio IS NULL OR pl.id_procedimento_licitatorio = p_id_procedimento_licitatorio)
  AND (num_licitacao IS NULL OR pl.numero_processo_licitatorio::TEXT ILIKE '%' || num_licitacao || '%')
  AND (num_edital IS NULL OR LOWER(pl.numero_edital) LIKE '%' || LOWER(num_edital) || '%')
  AND (data_abertura_inicio IS NULL OR pl.data_abertura_certame >= data_abertura_inicio)
  AND (data_abertura_fim IS NULL OR pl.data_abertura_certame <= data_abertura_fim)
  AND (data_fechamento_inicio IS NULL OR pl.data_vencimento >= data_fechamento_inicio)
  AND (data_fechamento_fim IS NULL OR pl.data_vencimento <= data_fechamento_fim)
  AND (obj IS NULL OR LOWER(pl.descricao_objeto) LIKE '%' || LOWER(obj) || '%')
  AND (ent IS NULL OR LOWER(pl.ente) LIKE '%' || LOWER(ent) || '%')
  AND (uni_gest IS NULL OR LOWER(pl.nome_ug) LIKE '%' || LOWER(uni_gest) || '%')
  AND (situ IS NULL OR LOWER(pl.situacao) LIKE '%' || LOWER(situ) || '%')
  AND (modal IS NULL OR LOWER(pl.modalidade) LIKE '%' || LOWER(modal) || '%')
  AND ((p_com_nfe IS NULL OR (p_com_nfe = TRUE AND pl.id_nfe IS NOT NULL))
       AND (p_com_documento IS NULL OR (p_com_documento = TRUE AND EXISTS (
            SELECT 1 FROM documento d 
            WHERE d.id_processo_licitatorio = pl.id_procedimento_licitatorio
       ))))
  AND (p_com_proc_sig IS NULL OR (p_com_proc_sig = TRUE AND pl.processos_sig IS NOT NULL))
GROUP BY
    pl.id_procedimento_licitatorio,
    pl.numero_edital,
    pl.descricao_objeto,
    pl.processos_sig,
    pl.valor_total_previsto,
    pl.valor_contrato,
    pl.diferenca,
    pl.modalidade,
    pl.tipo_licitacao,
    pl.situacao,
	pl.tipo_documento,
    pl.ente,
    pl.nome_ug,
    pl.data_abertura_certame,
    pl.data_vencimento,
    pl.niveis_alerta,
    pl.numero_processo_licitatorio
ORDER BY
    CASE WHEN sort_dir = 'asc' THEN
        CASE sort_column
            WHEN 'alertas' THEN COALESCE(array_length(string_to_array(pl.niveis_alerta, ','), 1), 0)
            WHEN 'valor_contrato' THEN pl.valor_contrato
            WHEN 'data_abertura' THEN EXTRACT(EPOCH FROM pl.data_abertura_certame)
            WHEN 'data_fechamento' THEN EXTRACT(EPOCH FROM pl.data_vencimento)
            WHEN 'diferenca' THEN CASE WHEN pl.valor_total_previsto != 0 THEN (pl.diferenca / pl.valor_total_previsto) ELSE 0 END
        END
    END ASC,
    CASE WHEN sort_dir = 'desc' THEN
        CASE sort_column
            WHEN 'alertas' THEN COALESCE(array_length(string_to_array(pl.niveis_alerta, ','), 1), 0)
            WHEN 'valor_contrato' THEN pl.valor_contrato
            WHEN 'data_abertura' THEN EXTRACT(EPOCH FROM pl.data_abertura_certame)
            WHEN 'data_fechamento' THEN EXTRACT(EPOCH FROM pl.data_vencimento)
            WHEN 'diferenca' THEN CASE WHEN pl.valor_total_previsto != 0 THEN (pl.diferenca / pl.valor_total_previsto) ELSE 0 END
        END
    END DESC
LIMIT limite OFFSET (pag - 1) * limite;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: log_painel; Type: TABLE; Schema: audit; Owner: -
--

CREATE TABLE audit.log_painel (
    acesso timestamp without time zone DEFAULT now(),
    usuario character varying(100) NOT NULL,
    consulta character varying(100) NOT NULL
);


--
-- Name: log_user; Type: TABLE; Schema: audit; Owner: -
--

CREATE TABLE audit.log_user (
    id integer NOT NULL,
    cpf_user text NOT NULL,
    url_backend text NOT NULL,
    data_acesso timestamp without time zone NOT NULL
);


--
-- Name: log_user_id_seq; Type: SEQUENCE; Schema: audit; Owner: -
--

CREATE SEQUENCE audit.log_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: log_user_id_seq; Type: SEQUENCE OWNED BY; Schema: audit; Owner: -
--

ALTER SEQUENCE audit.log_user_id_seq OWNED BY audit.log_user.id;


--
-- Name: users; Type: TABLE; Schema: audit; Owner: -
--

CREATE TABLE audit.users (
    cpf text NOT NULL,
    id_pessoa bigint,
    nome text,
    tipo_acesso text,
    email text,
    cpf_crypt bytea
);


--
-- Name: alerta; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alerta (
    id_alerta integer NOT NULL,
    nome text,
    nivel integer,
    descricao_longa text,
    descricao_curta text,
    id_execucao_metodo integer
);


--
-- Name: alerta_id_alerta_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.alerta_id_alerta_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: alerta_id_alerta_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.alerta_id_alerta_seq OWNED BY public.alerta.id_alerta;


--
-- Name: analise_agente; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.analise_agente (
    id_analise_agente integer NOT NULL,
    id_processo_licitatorio integer,
    data_analise date,
    versao_sistema text
);


--
-- Name: analise_agente_id_analise_agente_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.analise_agente_id_analise_agente_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: analise_agente_id_analise_agente_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.analise_agente_id_analise_agente_seq OWNED BY public.analise_agente.id_analise_agente;


--
-- Name: banco_de_precos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.banco_de_precos (
    id_banco_de_precos integer NOT NULL,
    texto text,
    data_aquisicao date,
    id_alerta integer,
    id_processo_licitatorio integer,
    id_item_nfe integer,
    id_grupo_bp integer
);


--
-- Name: banco_de_precos_id_banco_de_precos_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.banco_de_precos_id_banco_de_precos_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: banco_de_precos_id_banco_de_precos_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.banco_de_precos_id_banco_de_precos_seq OWNED BY public.banco_de_precos.id_banco_de_precos;


--
-- Name: classificacao_produto_servico; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.classificacao_produto_servico (
    id_classificacao_produto_servico integer NOT NULL,
    id_classificacao_produto_servico_pai integer,
    descricao text,
    identificador_para_codigo text
);


--
-- Name: classificacao_produto_servico_id_classificacao_produto_serv_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.classificacao_produto_servico_id_classificacao_produto_serv_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: classificacao_produto_servico_id_classificacao_produto_serv_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.classificacao_produto_servico_id_classificacao_produto_serv_seq OWNED BY public.classificacao_produto_servico.id_classificacao_produto_servico;


--
-- Name: cnae; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cnae (
    id_cnae bigint NOT NULL,
    cnae text NOT NULL,
    descricao text
);


--
-- Name: TABLE cnae; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.cnae IS 'Esta tabela provavelmente tem só uma fonte. Assim, não precisa de surrogate key (id_cnae). Poderia usar o próprio campo cnae como pk.';


--
-- Name: COLUMN cnae.id_cnae; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cnae.id_cnae IS 'pk';


--
-- Name: COLUMN cnae.cnae; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cnae.cnae IS 'aux';


--
-- Name: cnae_id_cnae_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cnae_id_cnae_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cnae_id_cnae_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cnae_id_cnae_seq OWNED BY public.cnae.id_cnae;


--
-- Name: contrato; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.contrato (
    id_contrato integer NOT NULL,
    id_processo_licitatorio bigint,
    numero_contrato text,
    descricao_objetivo text,
    data_assinatura date,
    data_vencimento date,
    valor_contrato double precision,
    valor_garantia double precision,
    id_contrato_superior integer,
    id_pessoa integer
);


--
-- Name: COLUMN contrato.id_contrato; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.contrato.id_contrato IS 'pk';


--
-- Name: COLUMN contrato.id_processo_licitatorio; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.contrato.id_processo_licitatorio IS 'fk';


--
-- Name: COLUMN contrato.numero_contrato; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.contrato.numero_contrato IS 'aux (formato serial/ano)';


--
-- Name: COLUMN contrato.data_assinatura; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.contrato.data_assinatura IS 'aux';


--
-- Name: COLUMN contrato.data_vencimento; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.contrato.data_vencimento IS 'aux';


--
-- Name: COLUMN contrato.valor_contrato; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.contrato.valor_contrato IS 'aux';


--
-- Name: COLUMN contrato.id_contrato_superior; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.contrato.id_contrato_superior IS 'fk';


--
-- Name: contrato_id_contrato_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.contrato_id_contrato_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: contrato_id_contrato_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.contrato_id_contrato_seq OWNED BY public.contrato.id_contrato;


--
-- Name: convenio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.convenio (
    id_convenio integer NOT NULL,
    descricao_objeto text,
    data_assinatura date,
    data_fim_vigencia date,
    valor_convenio text
);


--
-- Name: TABLE convenio; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.convenio IS 'Vários campos data e numéricos estão com tipo text. Deviam ser date ou timestamp e int, respectivamente, não? Em análise exploratória que Buzzi fez dos valores de campos data, muitos deles são na verdade timestamps.';


--
-- Name: COLUMN convenio.id_convenio; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.convenio.id_convenio IS 'pk';


--
-- Name: COLUMN convenio.data_assinatura; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.convenio.data_assinatura IS 'aux';


--
-- Name: COLUMN convenio.valor_convenio; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.convenio.valor_convenio IS 'aux';


--
-- Name: convenio_ente; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.convenio_ente (
    id_convenio integer NOT NULL,
    id_ente integer NOT NULL
);


--
-- Name: COLUMN convenio_ente.id_convenio; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.convenio_ente.id_convenio IS 'pk';


--
-- Name: COLUMN convenio_ente.id_ente; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.convenio_ente.id_ente IS 'fk';


--
-- Name: convenio_id_convenio_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.convenio_id_convenio_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: convenio_id_convenio_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.convenio_id_convenio_seq OWNED BY public.convenio.id_convenio;


--
-- Name: cotacao; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cotacao (
    id_cotacao bigint NOT NULL,
    numero_item integer,
    qt_item_cotado double precision,
    valor_cotado double precision,
    vencedor boolean,
    classificacao integer,
    id_item_licitacao integer NOT NULL,
    id_pessoa bigint
);


--
-- Name: TABLE cotacao; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.cotacao IS 'Pode compensar fazer índices com mais de um atributo:
- (id_pessoa, id_processo_licitatório)';


--
-- Name: COLUMN cotacao.id_cotacao; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cotacao.id_cotacao IS 'pk';


--
-- Name: COLUMN cotacao.id_item_licitacao; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cotacao.id_item_licitacao IS 'fk';


--
-- Name: cotacao_contrato; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cotacao_contrato (
    id_cotacao integer NOT NULL,
    id_contrato integer NOT NULL
);


--
-- Name: COLUMN cotacao_contrato.id_cotacao; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cotacao_contrato.id_cotacao IS 'pk';


--
-- Name: COLUMN cotacao_contrato.id_contrato; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.cotacao_contrato.id_contrato IS 'pk';


--
-- Name: cotacao_id_cotacao_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cotacao_id_cotacao_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cotacao_id_cotacao_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cotacao_id_cotacao_seq OWNED BY public.cotacao.id_cotacao;


--
-- Name: documento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documento (
    id_documento integer NOT NULL,
    nome_arquivo text,
    data_emissao timestamp without time zone,
    tamanho text,
    local_acesso_arquivo text,
    id_processo_licitatorio bigint,
    id_tipo_documento integer
);


--
-- Name: COLUMN documento.id_documento; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.documento.id_documento IS 'pk';


--
-- Name: COLUMN documento.id_processo_licitatorio; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.documento.id_processo_licitatorio IS 'fk';


--
-- Name: documento_id_documento_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.documento_id_documento_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: documento_id_documento_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.documento_id_documento_seq OWNED BY public.documento.id_documento;


--
-- Name: empenho; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.empenho (
    id_empenho bigint NOT NULL,
    num_empenho bigint,
    valor_empenho money,
    descricao text,
    data_empenho date,
    prestacao_contas boolean,
    regularizacao_orcamentaria boolean,
    id_processo_licitatorio bigint,
    id_empenho_superior bigint,
    id_pessoa bigint
);


--
-- Name: TABLE empenho; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.empenho IS 'Pelo que vi  todos os ids desta tabela (campos 12 a 24) dever ser inteiros curtos. 
Para conferir olhem em validacao.rf_empenho_int. A tabela public.empenho continua com erros da carga.

Tipos de ação e de empenho são especificados em https://www.tcesc.tc.br/sites/default/files/2021-07/Tabelas_Basicas_Sistema_Esfinge2019_Versao_15.pdf';


--
-- Name: COLUMN empenho.id_empenho; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.empenho.id_empenho IS 'pk';


--
-- Name: COLUMN empenho.num_empenho; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.empenho.num_empenho IS 'aux';


--
-- Name: COLUMN empenho.valor_empenho; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.empenho.valor_empenho IS 'aux';


--
-- Name: COLUMN empenho.data_empenho; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.empenho.data_empenho IS 'aux';


--
-- Name: COLUMN empenho.id_processo_licitatorio; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.empenho.id_processo_licitatorio IS 'fk';


--
-- Name: COLUMN empenho.id_empenho_superior; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.empenho.id_empenho_superior IS 'fk';


--
-- Name: empenho_id_empenho_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.empenho_id_empenho_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: empenho_id_empenho_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.empenho_id_empenho_seq OWNED BY public.empenho.id_empenho;


--
-- Name: ente; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ente (
    id_ente integer NOT NULL,
    id_municipio bigint,
    ente text
);


--
-- Name: COLUMN ente.id_ente; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ente.id_ente IS 'pk';


--
-- Name: COLUMN ente.id_municipio; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.ente.id_municipio IS 'fk';


--
-- Name: ente_id_ente_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ente_id_ente_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ente_id_ente_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ente_id_ente_seq OWNED BY public.ente.id_ente;


--
-- Name: estabelecimento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.estabelecimento (
    id_estabelecimento integer NOT NULL,
    cnpj text,
    cnpj_ordem text,
    cnpj_dv text,
    nome_fantasia text,
    id_situacao_cadastral integer,
    id_motivo_situacao_cadastral integer,
    cnae_principal text,
    tipo_logradouro text,
    logradouro text,
    numero text,
    complemento text,
    bairro text,
    cep text,
    ddd_1 text,
    telefone_1 text,
    ddd_2 text,
    telefone_2 text,
    ddd_fax text,
    fax text,
    email text,
    situacao_especial text,
    id_municipio integer,
    data_situacao date,
    data_situacao_especial date,
    data_inicio_atividade date
);


--
-- Name: estabelecimento_cnae_secundario; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.estabelecimento_cnae_secundario (
    cnae text NOT NULL,
    id_estabelecimento integer NOT NULL
);


--
-- Name: estabelecimento_id_estabelecimento_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.estabelecimento_id_estabelecimento_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: estabelecimento_id_estabelecimento_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.estabelecimento_id_estabelecimento_seq OWNED BY public.estabelecimento.id_estabelecimento;


--
-- Name: estatistica_item_bp; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.estatistica_item_bp (
    id_estatistica_item integer NOT NULL,
    tipo_estatistica text,
    valor_estatistica double precision,
    id_banco_de_precos integer
);


--
-- Name: estatistica_item_bp_id_estatistica_item_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.estatistica_item_bp_id_estatistica_item_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: estatistica_item_bp_id_estatistica_item_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.estatistica_item_bp_id_estatistica_item_seq OWNED BY public.estatistica_item_bp.id_estatistica_item;


--
-- Name: execucao_metodo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.execucao_metodo (
    id_execucao_metodo integer NOT NULL,
    id_metodo_analise integer NOT NULL,
    data_execucao date NOT NULL
);


--
-- Name: execucao_metodo_id_execucao_metodo_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.execucao_metodo_id_execucao_metodo_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: execucao_metodo_id_execucao_metodo_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.execucao_metodo_id_execucao_metodo_seq OWNED BY public.execucao_metodo.id_execucao_metodo;


--
-- Name: execucao_metodo_objeto_analise; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.execucao_metodo_objeto_analise (
    id_execucao_metodo integer NOT NULL,
    id_objeto_analise integer NOT NULL
);


--
-- Name: grafico_bp; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.grafico_bp (
    id_grafico_bp integer NOT NULL,
    tipo_grafico text,
    conteudo text,
    texto text,
    id_banco_de_precos integer
);


--
-- Name: grafico_bp_id_grafico_bp_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.grafico_bp_id_grafico_bp_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: grafico_bp_id_grafico_bp_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.grafico_bp_id_grafico_bp_seq OWNED BY public.grafico_bp.id_grafico_bp;


--
-- Name: grupo_bp; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.grupo_bp (
    id_grupo_bp integer NOT NULL,
    nome text,
    numero_grupo integer,
    id_metodo_de_agrupamento_bp integer
);


--
-- Name: grupo_bp_id_grupo_bp_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.grupo_bp_id_grupo_bp_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: grupo_bp_id_grupo_bp_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.grupo_bp_id_grupo_bp_seq OWNED BY public.grupo_bp.id_grupo_bp;


--
-- Name: hipertipologia_alerta_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.hipertipologia_alerta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: hipertipologia_alerta; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hipertipologia_alerta (
    id_hipertipologia_alerta integer DEFAULT nextval('public.hipertipologia_alerta_id_seq'::regclass) NOT NULL,
    nome text NOT NULL,
    descricao text,
    id_megatipologia_alerta integer
);


--
-- Name: inidonea; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.inidonea (
    id_inidonea integer NOT NULL,
    data_publicacao date,
    data_validade date,
    id_pessoa integer
);


--
-- Name: inidonea_id_inidonea_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.inidonea_id_inidonea_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: inidonea_id_inidonea_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.inidonea_id_inidonea_seq OWNED BY public.inidonea.id_inidonea;


--
-- Name: item_licitacao; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.item_licitacao (
    id_item_licitacao bigint NOT NULL,
    numero_sequencial_item bigint,
    descricao_item_licitacao text,
    data_homologacao date,
    qtd_item_licitacao text,
    descricao_unidade_medida text,
    id_processo_licitatorio bigint,
    valor_estimado_item text
);


--
-- Name: item_licitacao_id_item_licitacao_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.item_licitacao_id_item_licitacao_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: item_licitacao_id_item_licitacao_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.item_licitacao_id_item_licitacao_seq OWNED BY public.item_licitacao.id_item_licitacao;


--
-- Name: item_nfe; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.item_nfe (
    id_item_nfe integer NOT NULL,
    id_nfe integer NOT NULL,
    id_item integer NOT NULL,
    situacao_nfe text,
    data_emissao date,
    cod_mun_emitente text,
    cod_mun_destinatario text,
    cfop_produto text,
    ncm_produto character varying,
    gtin_produto character varying,
    descricao_produto text,
    quantidade_comercial double precision,
    unidade_comercial character varying,
    valor_unitario_comercial double precision,
    id_item_licitacao bigint,
    valor_desconto double precision,
    valor_frete double precision,
    valor_seguro double precision,
    valor_outras_despesas double precision,
    valor_total_comercial double precision,
    valor_total_liquido double precision,
    valor_unitario_liquido double precision,
    tipo_item_nfe text
);


--
-- Name: item_nfe_classificacao_produto_servico; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.item_nfe_classificacao_produto_servico (
    id_classificacao_produto_servico integer NOT NULL,
    id_item_nfe integer NOT NULL,
    id_item_nfe_classificacao_produto_servico integer NOT NULL
);


--
-- Name: item_nfe_classificacao_produt_id_item_nfe_classificacao_pro_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.item_nfe_classificacao_produt_id_item_nfe_classificacao_pro_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: item_nfe_classificacao_produt_id_item_nfe_classificacao_pro_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.item_nfe_classificacao_produt_id_item_nfe_classificacao_pro_seq OWNED BY public.item_nfe_classificacao_produto_servico.id_item_nfe_classificacao_produto_servico;


--
-- Name: item_nfe_grupo_bp; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.item_nfe_grupo_bp (
    id_grupo_bp integer NOT NULL,
    id_item_nfe integer NOT NULL,
    id_item_nfe_grupo_bp integer
);


--
-- Name: item_nfe_id_item_nfe_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.item_nfe_id_item_nfe_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: item_nfe_id_item_nfe_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.item_nfe_id_item_nfe_seq OWNED BY public.item_nfe.id_item_nfe;


--
-- Name: items_removidos_bp; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.items_removidos_bp (
    id_items_removidos_bp integer NOT NULL,
    id_banco_de_precos integer,
    id_nfe integer,
    id_grupo_bp integer NOT NULL,
    id_pessoa bigint NOT NULL,
    data_remocao timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: items_removidos_bp_id_items_removidos_bp_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.items_removidos_bp_id_items_removidos_bp_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: items_removidos_bp_id_items_removidos_bp_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.items_removidos_bp_id_items_removidos_bp_seq OWNED BY public.items_removidos_bp.id_items_removidos_bp;


--
-- Name: liquidacao; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.liquidacao (
    id_liquidacao integer NOT NULL,
    data_liquidacao date,
    valor_liquidacao double precision,
    id_empenho bigint,
    nota_liquidacao text,
    id_pessoa integer
);


--
-- Name: liquidacao_id_liquidacao_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.liquidacao_id_liquidacao_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: liquidacao_id_liquidacao_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.liquidacao_id_liquidacao_seq OWNED BY public.liquidacao.id_liquidacao;


--
-- Name: megatipologia_alerta_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.megatipologia_alerta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: megatipologia_alerta; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.megatipologia_alerta (
    id_megatipologia_alerta integer DEFAULT nextval('public.megatipologia_alerta_id_seq'::regclass) NOT NULL,
    nome text NOT NULL,
    descricao text
);


--
-- Name: metodo_analise; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.metodo_analise (
    id_metodo_analise integer NOT NULL,
    nome text,
    versao real,
    template_longo text,
    template_curto text,
    instrucoes_execucao text,
    metodologia text,
    tipo_instrucao text,
    id_tipologia_alerta integer
);


--
-- Name: metodo_analise_id_metodo_analise_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.metodo_analise_id_metodo_analise_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: metodo_analise_id_metodo_analise_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.metodo_analise_id_metodo_analise_seq OWNED BY public.metodo_analise.id_metodo_analise;


--
-- Name: metodo_de_agrupamento_bp; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.metodo_de_agrupamento_bp (
    id_metodo_de_agrupamento_bp integer NOT NULL,
    nome text,
    data_criacao date,
    id_classificacao_produto_servico integer
);


--
-- Name: metodo_de_agrupamento_bp_id_metodo_de_agrupamento_bp_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.metodo_de_agrupamento_bp_id_metodo_de_agrupamento_bp_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: metodo_de_agrupamento_bp_id_metodo_de_agrupamento_bp_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.metodo_de_agrupamento_bp_id_metodo_de_agrupamento_bp_seq OWNED BY public.metodo_de_agrupamento_bp.id_metodo_de_agrupamento_bp;


--
-- Name: modalidade_licitacao; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.modalidade_licitacao (
    id_modalidade_licitacao integer NOT NULL,
    descricao text NOT NULL
);


--
-- Name: motivo_situacao_cadastral; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.motivo_situacao_cadastral (
    id_motivo_situacao_cadastral integer NOT NULL,
    descricao text
);


--
-- Name: movimentacao_empenho; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.movimentacao_empenho (
    id_movimentacao_empenho integer NOT NULL,
    id_empenho integer NOT NULL
);


--
-- Name: movimentacao_empenho_id_movimentacao_empenho_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.movimentacao_empenho_id_movimentacao_empenho_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: movimentacao_empenho_id_movimentacao_empenho_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.movimentacao_empenho_id_movimentacao_empenho_seq OWNED BY public.movimentacao_empenho.id_movimentacao_empenho;


--
-- Name: municipio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.municipio (
    id_municipio integer NOT NULL,
    nome_municipio text,
    sigla_uf character(2),
    nome_uf text
);


--
-- Name: municipio_id_municipio_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.municipio_id_municipio_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: municipio_id_municipio_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.municipio_id_municipio_seq OWNED BY public.municipio.id_municipio;


--
-- Name: natureza_juridica; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.natureza_juridica (
    id_natureza_juridica integer NOT NULL,
    descricao text,
    orgao_publico boolean
);


--
-- Name: nfe_id_nfe_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nfe_id_nfe_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nfe; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nfe (
    id_nfe integer DEFAULT nextval('public.nfe_id_nfe_seq'::regclass) NOT NULL,
    situacao_nfe integer,
    forma_pgto integer,
    num_serie_nfe integer,
    num_doc_nfe integer,
    data_emissao date,
    data_saida date,
    tipo_operacao text,
    cnpj_emitente text,
    cpf_emitente text,
    ie_emitente character varying(255),
    ie_st_emitente character varying(255),
    im_emitente character varying(40),
    cnae_emitente text,
    crt_emitente integer,
    nome_emitente character varying(255),
    nome_fant_emitente character varying(255),
    fone_emitente character varying(255),
    logradouro_emitente character varying(255),
    numero_emitente integer,
    cpl_emitente character varying(100),
    bairro_emitente character varying(255),
    cod_mun_emitente text,
    nome_mun_emitente character varying(255),
    uf_emitente character varying(3),
    cod_pais_emitente text,
    nome_pais_emitente character varying(55),
    cep_emitente text,
    cnpj_destinatario text,
    nome_destinatario character varying(255),
    ie_destinatario character varying(255),
    insc_suframa_destinatario character varying(30),
    logradouro_destinatario character varying(255),
    numero_destinatario character varying(255),
    cpl_destinatario character varying(100),
    bairro_destinatario character varying(255),
    cod_mun_destinatario text,
    nome_mun_destinatario character varying(255),
    uf_destinatario character varying(3),
    cod_pais_destinatario text,
    nome_pais_destinatario character varying(100),
    cep_destinatario text,
    cpf_destinatario text,
    chave_acesso text,
    id_pagamento_empenho integer,
    id_estabelecimento integer,
    id_processo_licitatorio bigint
);


--
-- Name: noticia; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.noticia (
    id_noticia integer NOT NULL,
    titulo text,
    link text,
    numero_edital text,
    id_modalidade_licitacao integer,
    objeto text,
    data_publicacao date,
    nome_portal text,
    texto text,
    chamada text,
    id_processo_licitatorio integer
);


--
-- Name: noticia_id_noticia_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.noticia_id_noticia_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: noticia_id_noticia_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.noticia_id_noticia_seq OWNED BY public.noticia.id_noticia;


--
-- Name: noticia_municipio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.noticia_municipio (
    id_noticia integer NOT NULL,
    id_municipio integer NOT NULL,
    id_noticia_municipio integer NOT NULL
);


--
-- Name: noticia_municipio_id_noticia_municipio_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.noticia_municipio_id_noticia_municipio_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: noticia_municipio_id_noticia_municipio_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.noticia_municipio_id_noticia_municipio_seq OWNED BY public.noticia_municipio.id_noticia_municipio;


--
-- Name: objeto_analise; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.objeto_analise (
    id_objeto_analise integer NOT NULL,
    nome_objeto text,
    id_unidade_gestora integer,
    id_ente integer,
    id_item_nfe integer,
    id_documento integer,
    id_item_licitacao integer,
    id_pessoa integer,
    id_processo_licitatorio integer
);


--
-- Name: objeto_analise_id_objeto_analise_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.objeto_analise_id_objeto_analise_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: objeto_analise_id_objeto_analise_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.objeto_analise_id_objeto_analise_seq OWNED BY public.objeto_analise.id_objeto_analise;


--
-- Name: pagamento_empenho; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pagamento_empenho (
    id_pagamento_empenho integer NOT NULL,
    data_pagamento date,
    valor_pagamento double precision,
    nro_ordem_bancaria integer,
    data_exigibilidade date,
    data_publicacao_justificativa date,
    data_validade date,
    cod_banco integer,
    cod_agencia integer,
    numero_conta_bancaria_pagadora text,
    id_liquidacao bigint,
    id_empenho bigint
);


--
-- Name: pagamento_empenho_id_pagamento_empenho_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pagamento_empenho_id_pagamento_empenho_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pagamento_empenho_id_pagamento_empenho_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pagamento_empenho_id_pagamento_empenho_seq OWNED BY public.pagamento_empenho.id_pagamento_empenho;


--
-- Name: participante_convenio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.participante_convenio (
    id_convenio integer NOT NULL,
    id_pessoa integer NOT NULL
);


--
-- Name: pessoa; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pessoa (
    id_pessoa integer NOT NULL,
    nome text NOT NULL,
    estrangeiro boolean
);


--
-- Name: pessoa_fisica; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pessoa_fisica (
    cpf character varying(20) NOT NULL,
    id_situacao_cadastral integer,
    faixa_etaria character(5),
    data_nascimento date,
    id_pessoa integer NOT NULL
);


--
-- Name: pessoa_fisica_estabelecimento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pessoa_fisica_estabelecimento (
    id_estabelecimento integer NOT NULL,
    cargo text NOT NULL,
    cpf character varying(20)
);


--
-- Name: pessoa_fisica_nfe; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pessoa_fisica_nfe (
    id_nfe integer NOT NULL,
    cpf character varying(20)
);


--
-- Name: pessoa_id_pessoa_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pessoa_id_pessoa_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pessoa_id_pessoa_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pessoa_id_pessoa_seq OWNED BY public.pessoa.id_pessoa;


--
-- Name: pessoa_juridica; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pessoa_juridica (
    cnpj character varying(20) NOT NULL,
    razao_social text,
    id_natureza_juridica integer,
    capital_social double precision,
    porte_empresa integer,
    id_pessoa bigint NOT NULL,
    orgao_publico boolean DEFAULT false
);


--
-- Name: pessoa_juridica_id_pessoa_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.pessoa_juridica_id_pessoa_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: pessoa_juridica_id_pessoa_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.pessoa_juridica_id_pessoa_seq OWNED BY public.pessoa_juridica.id_pessoa;


--
-- Name: pessoa_municipio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pessoa_municipio (
    id_pessoa integer NOT NULL,
    id_municipio integer NOT NULL
);


--
-- Name: pessoa_pessoa_juridica; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pessoa_pessoa_juridica (
    participacao integer,
    tipo_sociedade integer,
    responsavel integer,
    classificacao integer,
    cnpj character varying(20) NOT NULL,
    id_pessoa integer NOT NULL
);


--
-- Name: processo_licitatorio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.processo_licitatorio (
    id_processo_licitatorio bigint NOT NULL,
    numero_edital text,
    data_limite date,
    descricao_objeto text,
    valor_total_previsto double precision,
    data_abertura_certame date,
    id_tipo_objeto_licitacao integer,
    id_tipo_cotacao integer,
    id_modalidade_licitacao integer,
    id_tipo_licitacao integer DEFAULT 20,
    id_unidade_gestora integer,
    id_unidade_orcamentaria integer,
    situacao text,
    numero_processo_licitatorio text
);


--
-- Name: processo_licitatorio_id_processo_licitatorio_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.processo_licitatorio_id_processo_licitatorio_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: processo_licitatorio_id_processo_licitatorio_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.processo_licitatorio_id_processo_licitatorio_seq OWNED BY public.processo_licitatorio.id_processo_licitatorio;


--
-- Name: processo_licitatorio_pessoa; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.processo_licitatorio_pessoa (
    id_processo_licitatorio integer NOT NULL,
    id_pessoa integer NOT NULL,
    cnpj_consorcio character varying(20),
    data_validade_proposta date,
    participante_cotacao text
);


--
-- Name: sig; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sig (
    id_sig bigint NOT NULL,
    numero_processo_sig bigint,
    data_abertura date,
    data_fechamento date,
    promotor character varying(100),
    fraude_investigada text,
    status text
);


--
-- Name: sig_documento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sig_documento (
    id_documento bigint NOT NULL,
    id_sig bigint NOT NULL
);


--
-- Name: sig_processo_licitatorio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sig_processo_licitatorio (
    id_sig bigint NOT NULL,
    id_processo_licitatorio bigint NOT NULL
);


--
-- Name: situacao_cadastral; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.situacao_cadastral (
    id_situacao_cadastral integer NOT NULL,
    descricao text
);


--
-- Name: situacao_cadastral_id_situacao_cadastral_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.situacao_cadastral_id_situacao_cadastral_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: situacao_cadastral_id_situacao_cadastral_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.situacao_cadastral_id_situacao_cadastral_seq OWNED BY public.situacao_cadastral.id_situacao_cadastral;


--
-- Name: tipo_cotacao; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tipo_cotacao (
    id_tipo_cotacao integer NOT NULL,
    descricao text
);


--
-- Name: tipo_documento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tipo_documento (
    id_tipo_documento integer NOT NULL,
    descricao text NOT NULL
);


--
-- Name: tipo_documento_id_tipo_documento_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tipo_documento_id_tipo_documento_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tipo_documento_id_tipo_documento_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tipo_documento_id_tipo_documento_seq OWNED BY public.tipo_documento.id_tipo_documento;


--
-- Name: tipo_especificacao_ug; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tipo_especificacao_ug (
    id_tipo_especificacao_ug integer NOT NULL,
    descricao text
);


--
-- Name: tipo_especificacao_ug_id_tipo_especificacao_ug_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tipo_especificacao_ug_id_tipo_especificacao_ug_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tipo_especificacao_ug_id_tipo_especificacao_ug_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tipo_especificacao_ug_id_tipo_especificacao_ug_seq OWNED BY public.tipo_especificacao_ug.id_tipo_especificacao_ug;


--
-- Name: tipo_licitacao; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tipo_licitacao (
    id_tipo_licitacao integer NOT NULL,
    descricao text
);


--
-- Name: tipo_licitacao_id_tipo_licitacao_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tipo_licitacao_id_tipo_licitacao_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tipo_licitacao_id_tipo_licitacao_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tipo_licitacao_id_tipo_licitacao_seq OWNED BY public.tipo_licitacao.id_tipo_licitacao;


--
-- Name: tipo_objeto_licitacao; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tipo_objeto_licitacao (
    id_tipo_objeto_licitacao integer NOT NULL,
    descricao text
);


--
-- Name: tipo_ug; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tipo_ug (
    id_tipo_ug integer NOT NULL,
    descricao text
);


--
-- Name: tipo_ug_id_tipo_ug_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tipo_ug_id_tipo_ug_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tipo_ug_id_tipo_ug_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tipo_ug_id_tipo_ug_seq OWNED BY public.tipo_ug.id_tipo_ug;


--
-- Name: tipologia_alerta_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tipologia_alerta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tipologia_alerta; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tipologia_alerta (
    id_tipologia_alerta integer DEFAULT nextval('public.tipologia_alerta_id_seq'::regclass) NOT NULL,
    id_hipertipologia_alerta integer NOT NULL,
    nome text NOT NULL,
    descricao text
);


--
-- Name: unidade_gestora; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.unidade_gestora (
    id_unidade_gestora integer NOT NULL,
    nome_ug text,
    cep character varying(20),
    cnpj character varying(20),
    id_ente integer,
    id_tipo_ug integer,
    id_tipo_especificacao_ug integer
);


--
-- Name: unidade_gestora_id_unidade_gestora_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.unidade_gestora_id_unidade_gestora_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: unidade_gestora_id_unidade_gestora_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.unidade_gestora_id_unidade_gestora_seq OWNED BY public.unidade_gestora.id_unidade_gestora;


--
-- Name: unidade_orcamentaria; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.unidade_orcamentaria (
    id_unidade_orcamentaria integer NOT NULL,
    nome_unidade_orcamentaria text
);


--
-- Name: unidade_orcamentaria_id_unidade_orcamentaria_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.unidade_orcamentaria_id_unidade_orcamentaria_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: unidade_orcamentaria_id_unidade_orcamentaria_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.unidade_orcamentaria_id_unidade_orcamentaria_seq OWNED BY public.unidade_orcamentaria.id_unidade_orcamentaria;


--
-- Name: usuario_alerta_ignorado; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usuario_alerta_ignorado (
    cpf text NOT NULL,
    id_alerta integer NOT NULL
);


--
-- Name: usuario_processo_licitatorio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usuario_processo_licitatorio (
    cpf text NOT NULL,
    id_processo_licitatorio bigint NOT NULL
);


--
-- Name: log_user id; Type: DEFAULT; Schema: audit; Owner: -
--

ALTER TABLE ONLY audit.log_user ALTER COLUMN id SET DEFAULT nextval('audit.log_user_id_seq'::regclass);


--
-- Name: alerta id_alerta; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerta ALTER COLUMN id_alerta SET DEFAULT nextval('public.alerta_id_alerta_seq'::regclass);


--
-- Name: analise_agente id_analise_agente; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analise_agente ALTER COLUMN id_analise_agente SET DEFAULT nextval('public.analise_agente_id_analise_agente_seq'::regclass);


--
-- Name: banco_de_precos id_banco_de_precos; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.banco_de_precos ALTER COLUMN id_banco_de_precos SET DEFAULT nextval('public.banco_de_precos_id_banco_de_precos_seq'::regclass);


--
-- Name: classificacao_produto_servico id_classificacao_produto_servico; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classificacao_produto_servico ALTER COLUMN id_classificacao_produto_servico SET DEFAULT nextval('public.classificacao_produto_servico_id_classificacao_produto_serv_seq'::regclass);


--
-- Name: cnae id_cnae; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cnae ALTER COLUMN id_cnae SET DEFAULT nextval('public.cnae_id_cnae_seq'::regclass);


--
-- Name: contrato id_contrato; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato ALTER COLUMN id_contrato SET DEFAULT nextval('public.contrato_id_contrato_seq'::regclass);


--
-- Name: convenio id_convenio; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.convenio ALTER COLUMN id_convenio SET DEFAULT nextval('public.convenio_id_convenio_seq'::regclass);


--
-- Name: cotacao id_cotacao; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cotacao ALTER COLUMN id_cotacao SET DEFAULT nextval('public.cotacao_id_cotacao_seq'::regclass);


--
-- Name: documento id_documento; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento ALTER COLUMN id_documento SET DEFAULT nextval('public.documento_id_documento_seq'::regclass);


--
-- Name: empenho id_empenho; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empenho ALTER COLUMN id_empenho SET DEFAULT nextval('public.empenho_id_empenho_seq'::regclass);


--
-- Name: ente id_ente; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ente ALTER COLUMN id_ente SET DEFAULT nextval('public.ente_id_ente_seq'::regclass);


--
-- Name: estabelecimento id_estabelecimento; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estabelecimento ALTER COLUMN id_estabelecimento SET DEFAULT nextval('public.estabelecimento_id_estabelecimento_seq'::regclass);


--
-- Name: estatistica_item_bp id_estatistica_item; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estatistica_item_bp ALTER COLUMN id_estatistica_item SET DEFAULT nextval('public.estatistica_item_bp_id_estatistica_item_seq'::regclass);


--
-- Name: execucao_metodo id_execucao_metodo; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.execucao_metodo ALTER COLUMN id_execucao_metodo SET DEFAULT nextval('public.execucao_metodo_id_execucao_metodo_seq'::regclass);


--
-- Name: grafico_bp id_grafico_bp; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.grafico_bp ALTER COLUMN id_grafico_bp SET DEFAULT nextval('public.grafico_bp_id_grafico_bp_seq'::regclass);


--
-- Name: grupo_bp id_grupo_bp; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.grupo_bp ALTER COLUMN id_grupo_bp SET DEFAULT nextval('public.grupo_bp_id_grupo_bp_seq'::regclass);


--
-- Name: inidonea id_inidonea; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inidonea ALTER COLUMN id_inidonea SET DEFAULT nextval('public.inidonea_id_inidonea_seq'::regclass);


--
-- Name: item_licitacao id_item_licitacao; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_licitacao ALTER COLUMN id_item_licitacao SET DEFAULT nextval('public.item_licitacao_id_item_licitacao_seq'::regclass);


--
-- Name: item_nfe id_item_nfe; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_nfe ALTER COLUMN id_item_nfe SET DEFAULT nextval('public.item_nfe_id_item_nfe_seq'::regclass);


--
-- Name: item_nfe_classificacao_produto_servico id_item_nfe_classificacao_produto_servico; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_nfe_classificacao_produto_servico ALTER COLUMN id_item_nfe_classificacao_produto_servico SET DEFAULT nextval('public.item_nfe_classificacao_produt_id_item_nfe_classificacao_pro_seq'::regclass);


--
-- Name: items_removidos_bp id_items_removidos_bp; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.items_removidos_bp ALTER COLUMN id_items_removidos_bp SET DEFAULT nextval('public.items_removidos_bp_id_items_removidos_bp_seq'::regclass);


--
-- Name: liquidacao id_liquidacao; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidacao ALTER COLUMN id_liquidacao SET DEFAULT nextval('public.liquidacao_id_liquidacao_seq'::regclass);


--
-- Name: metodo_analise id_metodo_analise; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metodo_analise ALTER COLUMN id_metodo_analise SET DEFAULT nextval('public.metodo_analise_id_metodo_analise_seq'::regclass);


--
-- Name: metodo_de_agrupamento_bp id_metodo_de_agrupamento_bp; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metodo_de_agrupamento_bp ALTER COLUMN id_metodo_de_agrupamento_bp SET DEFAULT nextval('public.metodo_de_agrupamento_bp_id_metodo_de_agrupamento_bp_seq'::regclass);


--
-- Name: movimentacao_empenho id_movimentacao_empenho; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimentacao_empenho ALTER COLUMN id_movimentacao_empenho SET DEFAULT nextval('public.movimentacao_empenho_id_movimentacao_empenho_seq'::regclass);


--
-- Name: municipio id_municipio; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.municipio ALTER COLUMN id_municipio SET DEFAULT nextval('public.municipio_id_municipio_seq'::regclass);


--
-- Name: noticia id_noticia; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.noticia ALTER COLUMN id_noticia SET DEFAULT nextval('public.noticia_id_noticia_seq'::regclass);


--
-- Name: noticia_municipio id_noticia_municipio; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.noticia_municipio ALTER COLUMN id_noticia_municipio SET DEFAULT nextval('public.noticia_municipio_id_noticia_municipio_seq'::regclass);


--
-- Name: objeto_analise id_objeto_analise; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.objeto_analise ALTER COLUMN id_objeto_analise SET DEFAULT nextval('public.objeto_analise_id_objeto_analise_seq'::regclass);


--
-- Name: pagamento_empenho id_pagamento_empenho; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pagamento_empenho ALTER COLUMN id_pagamento_empenho SET DEFAULT nextval('public.pagamento_empenho_id_pagamento_empenho_seq'::regclass);


--
-- Name: pessoa id_pessoa; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pessoa ALTER COLUMN id_pessoa SET DEFAULT nextval('public.pessoa_id_pessoa_seq'::regclass);


--
-- Name: pessoa_juridica id_pessoa; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pessoa_juridica ALTER COLUMN id_pessoa SET DEFAULT nextval('public.pessoa_juridica_id_pessoa_seq'::regclass);


--
-- Name: processo_licitatorio id_processo_licitatorio; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processo_licitatorio ALTER COLUMN id_processo_licitatorio SET DEFAULT nextval('public.processo_licitatorio_id_processo_licitatorio_seq'::regclass);


--
-- Name: situacao_cadastral id_situacao_cadastral; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.situacao_cadastral ALTER COLUMN id_situacao_cadastral SET DEFAULT nextval('public.situacao_cadastral_id_situacao_cadastral_seq'::regclass);


--
-- Name: tipo_documento id_tipo_documento; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_documento ALTER COLUMN id_tipo_documento SET DEFAULT nextval('public.tipo_documento_id_tipo_documento_seq'::regclass);


--
-- Name: tipo_especificacao_ug id_tipo_especificacao_ug; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_especificacao_ug ALTER COLUMN id_tipo_especificacao_ug SET DEFAULT nextval('public.tipo_especificacao_ug_id_tipo_especificacao_ug_seq'::regclass);


--
-- Name: tipo_licitacao id_tipo_licitacao; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_licitacao ALTER COLUMN id_tipo_licitacao SET DEFAULT nextval('public.tipo_licitacao_id_tipo_licitacao_seq'::regclass);


--
-- Name: tipo_ug id_tipo_ug; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_ug ALTER COLUMN id_tipo_ug SET DEFAULT nextval('public.tipo_ug_id_tipo_ug_seq'::regclass);


--
-- Name: unidade_gestora id_unidade_gestora; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.unidade_gestora ALTER COLUMN id_unidade_gestora SET DEFAULT nextval('public.unidade_gestora_id_unidade_gestora_seq'::regclass);


--
-- Name: unidade_orcamentaria id_unidade_orcamentaria; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.unidade_orcamentaria ALTER COLUMN id_unidade_orcamentaria SET DEFAULT nextval('public.unidade_orcamentaria_id_unidade_orcamentaria_seq'::regclass);


--
-- Data for Name: log_painel; Type: TABLE DATA; Schema: audit; Owner: -
--

COPY audit.log_painel (acesso, usuario, consulta) FROM stdin;
2024-10-29 00:47:44.029844	Cleber	login
2024-10-29 00:47:44.078005	Cleber	login
2024-10-23 19:42:22.524766	Luis	login
2024-10-29 00:47:44.512256	Cleber	login
2024-10-29 00:47:44.982915	Cleber	login
2024-10-29 00:47:45.627922	Cleber	login
2024-10-29 00:47:45.673544	Cleber	login
2024-10-29 00:47:46.581877	Cleber	login
2024-10-29 00:47:47.260114	Cleber	login
2024-11-04 20:12:17.388174	Matheus Machado dos Santos	login
2024-10-29 00:47:47.708275	Cleber	login
2024-11-04 20:12:18.539106	Matheus Machado dos Santos	login
2024-10-29 00:48:01.633269	Cleber	login
2024-11-04 20:12:19.711262	Matheus Machado dos Santos	login
2024-10-29 00:48:02.114628	Cleber	login
2024-10-23 20:01:55.189573	Luis	consulta_licitacao
2024-11-04 20:12:20.911142	Matheus Machado dos Santos	login
2024-10-29 00:48:14.289993	Cleber	login
2024-11-04 20:12:22.177164	Matheus Machado dos Santos	login
2024-10-29 00:48:23.224329	Cleber	login
2024-11-04 20:12:23.447622	Matheus Machado dos Santos	login
2024-10-29 00:48:23.525287	Cleber	login
2024-11-04 20:12:24.894071	Matheus Machado dos Santos	login
2024-10-29 00:48:47.537948	Cleber	login
2024-11-04 20:12:26.257122	Matheus Machado dos Santos	login
2024-10-29 00:48:47.917925	Cleber	login
2024-11-04 20:12:27.683046	Matheus Machado dos Santos	login
2024-10-25 21:54:56.115545	Felipe	login
2024-10-29 00:48:54.521465	Cleber	login
2024-10-25 21:54:56.682048	Felipe	login
2024-11-04 20:12:29.124872	Matheus Machado dos Santos	login
2024-10-29 00:48:54.980771	Cleber	login
2024-10-27 17:57:17.791628	Felipe	login
2024-11-04 20:12:30.591138	Matheus Machado dos Santos	login
2024-10-27 17:57:18.349543	Felipe	login
2024-10-29 00:49:42.777353	Cleber	login
2024-10-27 17:57:20.237537	Felipe	login
2024-10-27 17:57:20.237537	Felipe	login
2024-10-27 17:57:21.039052	Felipe	login
2024-10-27 17:57:21.477858	Felipe	login
2024-10-27 17:57:23.817292	Felipe	login
2024-10-27 17:57:27.425463	Felipe	login
2024-10-27 17:57:27.543697	Felipe	login
2024-10-27 17:57:27.968746	Felipe	login
2024-10-27 17:57:28.918074	Felipe	login
2024-10-27 17:57:31.921795	Felipe	login
2024-10-27 17:57:31.921795	Felipe	login
2024-10-27 17:57:33.238046	Felipe	login
2024-10-27 17:57:35.918624	Felipe	login
2024-10-27 17:57:35.918624	Felipe	login
2024-10-27 17:57:37.138044	Felipe	login
2024-11-04 20:12:32.173356	Matheus Machado dos Santos	login
2024-10-27 17:57:37.688216	Felipe	login
2024-10-29 00:49:43.192909	Cleber	login
2024-10-27 17:59:33.328336	Felipe	login
2024-10-27 17:59:33.347056	Felipe	login
2024-10-27 17:59:33.745264	Felipe	login
2024-10-27 17:59:34.131018	Felipe	login
2024-11-04 20:12:33.796666	Matheus Machado dos Santos	login
2024-10-28 11:42:28.979835	Matheus Machado dos Santos	login
2024-10-29 00:50:50.314867	Cleber	login
2024-10-28 11:42:29.784517	Matheus Machado dos Santos	login
2024-11-04 20:12:35.58561	Matheus Machado dos Santos	login
2024-10-29 00:50:50.903661	Cleber	login
2024-10-29 00:45:49.921683	Cleber	login
2024-11-04 20:12:37.530609	Matheus Machado dos Santos	login
2024-10-29 00:45:50.50388	Cleber	login
2024-10-29 00:54:09.776062	Cleber	login
2024-10-29 00:46:30.293008	Cleber	login
2024-10-29 00:46:30.293008	Cleber	login
2024-10-29 00:46:30.349758	Cleber	login
2024-10-29 00:46:30.81031	Cleber	login
2024-10-29 00:46:35.817262	Cleber	login
2024-10-29 00:46:35.861893	Cleber	login
2024-10-29 00:46:40.973138	Cleber	login
2024-11-04 20:12:39.339027	Matheus Machado dos Santos	login
2024-10-29 00:46:41.489917	Cleber	login
2024-10-29 00:54:10.386715	Cleber	login
2024-10-29 00:46:48.066148	Cleber	login
2024-11-04 20:12:41.221987	Matheus Machado dos Santos	login
2024-10-29 00:46:48.601782	Cleber	login
2024-10-29 00:54:11.580202	Cleber	login
2024-10-29 00:46:51.193842	Cleber	login
2024-11-04 20:12:43.281836	Matheus Machado dos Santos	login
2024-10-29 00:46:51.769146	Cleber	login
2024-10-29 00:54:12.168406	Cleber	login
2024-10-29 00:47:03.531009	Cleber	login
2024-11-04 20:12:45.125239	Matheus Machado dos Santos	login
2024-10-29 00:47:03.966902	Cleber	login
2024-10-29 00:54:23.540084	Cleber	login
2024-10-29 00:47:07.574678	Cleber	login
2024-11-04 20:12:47.019606	Matheus Machado dos Santos	login
2024-10-29 00:47:08.000802	Cleber	login
2024-10-29 00:54:23.995051	Cleber	login
2024-10-29 00:47:11.717892	Cleber	login
2024-11-04 20:12:48.931657	Matheus Machado dos Santos	login
2024-10-29 00:47:12.214775	Cleber	login
2024-10-29 00:54:32.047457	Cleber	login
2024-10-29 00:47:13.106076	Cleber	login
2024-11-04 20:12:50.919393	Matheus Machado dos Santos	login
2024-10-29 00:47:13.598281	Cleber	login
2024-10-29 00:54:32.455601	Cleber	login
2024-10-29 00:47:15.038247	Cleber	login
2024-11-04 20:12:52.976922	Matheus Machado dos Santos	login
2024-10-29 00:47:15.613793	Cleber	login
2024-10-29 00:55:37.071981	Cleber	login
2024-10-29 00:47:16.577409	Cleber	login
2024-10-29 00:55:37.121833	Cleber	login
2024-10-29 00:47:17.13108	Cleber	login
2024-10-29 00:55:37.530795	Cleber	login
2024-10-29 00:47:24.98242	Cleber	login
2024-10-29 00:55:38.030742	Cleber	login
2024-10-29 00:47:25.486817	Cleber	login
2024-10-29 00:55:44.127981	Cleber	login
2024-10-29 00:47:30.034924	Cleber	login
2024-11-04 20:12:55.100163	Matheus Machado dos Santos	login
2024-10-29 00:47:30.426638	Cleber	login
2024-10-29 00:55:44.575526	Cleber	login
2024-11-04 20:12:57.67147	Matheus Machado dos Santos	login
2024-10-29 00:56:12.527575	Cleber	login
2024-11-04 20:12:59.940611	Matheus Machado dos Santos	login
2024-10-29 00:56:13.059548	Cleber	login
2024-11-04 20:13:02.134331	Matheus Machado dos Santos	login
2024-10-29 00:56:38.499201	Cleber	login
2024-11-04 20:13:04.773289	Matheus Machado dos Santos	login
2024-10-29 00:56:38.991469	Cleber	login
2024-11-04 20:13:06.906897	Matheus Machado dos Santos	login
2024-10-29 00:58:14.216272	Cleber	login
2024-10-29 00:58:14.266148	Cleber	login
2024-10-29 00:58:14.674934	Cleber	login
2024-10-29 00:58:15.099205	Cleber	login
2024-10-29 00:58:18.987124	Cleber	login
2024-10-29 00:58:20.151661	Cleber	login
2024-10-29 00:58:20.191189	Cleber	login
2024-10-29 00:58:20.687124	Cleber	login
2024-10-29 00:58:20.763296	Cleber	login
2024-11-04 20:13:09.153212	Matheus Machado dos Santos	login
2024-10-29 00:58:21.223648	Cleber	login
2024-10-29 00:58:22.239881	Cleber	login
2024-10-29 00:58:22.691236	Cleber	login
2024-10-29 00:58:23.131593	Cleber	login
2024-10-29 00:58:23.984166	Cleber	login
2024-10-29 00:58:24.489627	Cleber	login
2024-10-29 00:58:27.128706	Cleber	login
2024-10-29 00:58:27.643735	Cleber	login
2024-10-29 00:58:28.14094	Cleber	login
2024-10-29 00:58:29.183668	Cleber	login
2024-10-29 00:58:29.183668	Cleber	login
2024-10-29 00:58:29.633821	Cleber	login
2024-10-29 00:58:30.058387	Cleber	login
2024-10-29 00:58:33.210572	Cleber	login
2024-10-29 00:58:34.092087	Cleber	login
2024-10-29 00:58:34.131091	Cleber	login
2024-10-29 00:58:34.591346	Cleber	login
2024-10-29 00:58:35.32378	Cleber	login
2024-10-29 00:58:35.32378	Cleber	login
2024-10-29 00:58:35.424338	Cleber	login
2024-11-08 17:11:48.676489	Felipe	login
2024-11-08 17:11:50.38406	Felipe	login
2024-11-22 22:03:55.28641	Felipe	login
2025-02-21 23:56:15.970004	Jos├® Eduardo Medeiros Jochem	login
2024-11-25 19:26:26.440485	Andr├® Teixeira Milioli	login
2025-02-21 23:56:16.6322	Jos├® Eduardo Medeiros Jochem	login
2024-11-25 19:26:49.885787	Andr├® Teixeira Milioli	login
2025-02-21 23:56:17.737203	Jos├® Eduardo Medeiros Jochem	login
2024-11-25 19:27:56.685721	Andr├® Teixeira Milioli	login
2024-11-08 19:42:39.395348	Felipe	login
2024-11-25 19:29:13.122649	Andr├® Teixeira Milioli	login
2024-11-08 19:42:47.883621	Felipe	login
2025-02-21 23:56:25.767278	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:43:05.555148	Felipe	login
2024-11-25 19:29:47.918084	Andr├® Teixeira Milioli	login
2024-11-08 19:43:08.326096	Felipe	login
2025-02-21 23:56:25.833814	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:43:12.601492	Felipe	login
2024-11-26 14:30:36.165734	Felipe	login
2024-11-08 19:43:14.514364	Felipe	login
2024-11-26 14:30:36.165734	Felipe	login
2024-11-08 19:43:36.727884	Felipe	login
2024-11-26 14:30:36.165734	Felipe	login
2024-11-08 19:44:09.469283	Felipe	login
2024-11-08 19:44:55.573145	Felipe	login
2024-11-26 14:30:36.165734	Felipe	login
2024-11-08 19:45:59.665427	Felipe	login
2024-11-26 14:30:36.165734	Felipe	login
2024-11-08 19:46:02.629797	Felipe	login
2024-11-26 14:30:36.165734	Felipe	login
2024-11-08 19:46:11.60669	Felipe	login
2024-11-26 14:33:18.768992	Felipe	login
2024-11-08 19:46:30.654025	Felipe	login
2024-11-04 20:13:24.267505	Matheus Machado dos Santos	login
2024-11-04 20:13:24.755947	Matheus Machado dos Santos	login
2024-11-04 20:17:21.469683	Matheus Machado dos Santos	login
2024-11-04 20:17:29.505869	Matheus Machado dos Santos	login
2024-11-04 20:17:30.199942	Matheus Machado dos Santos	login
2024-11-04 20:17:37.716778	Matheus Machado dos Santos	login
2024-11-04 20:17:37.834183	Matheus Machado dos Santos	login
2024-11-05 13:29:48.089008	Breno	login
2024-11-05 13:29:49.794377	Breno	login
2024-11-05 13:30:15.722052	Breno	login
2024-11-05 13:30:15.920928	Breno	login
2024-11-05 13:30:23.528889	Breno	login
2024-11-05 13:30:23.528889	Breno	login
2024-11-05 13:30:23.547513	Breno	login
2024-11-05 13:33:31.617735	Breno	login
2024-11-05 13:33:31.960617	Breno	login
2024-11-05 13:33:38.949968	Breno	login
2024-11-05 13:34:38.762943	Breno	login
2024-11-05 13:34:39.467486	Breno	login
2024-11-05 13:34:39.467486	Breno	login
2024-11-05 13:35:48.288057	Breno	login
2024-11-05 13:36:44.793498	Breno	login
2024-11-05 13:36:45.29857	Breno	login
2024-11-05 13:37:07.760421	Breno	login
2024-11-05 13:37:07.997393	Breno	login
2024-11-05 13:37:10.360668	Breno	login
2024-11-05 13:37:10.360668	Breno	login
2024-11-05 13:37:10.369704	Breno	login
2024-11-05 13:37:11.183457	Breno	login
2024-11-08 19:46:44.392467	Felipe	login
2024-11-08 19:47:26.863389	Felipe	login
2024-11-05 14:21:49.792619	Breno	login
2024-11-05 14:23:03.388485	Breno	login
2024-11-05 14:23:07.510759	Breno	login
2024-11-08 19:48:01.586443	Felipe	login
2024-11-08 19:48:01.663936	Felipe	login
2024-11-05 17:02:24.4858	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:49:46.245654	Felipe	login
2024-11-05 17:07:33.37626	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:55:44.878438	Felipe	login
2024-11-05 17:07:38.338097	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:38.338097	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:38.338097	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:39.449864	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:40.390239	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:42.144318	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:43.143156	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:43.157815	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:44.003836	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:44.36983	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:08.533065	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:15.372974	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:18.498758	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:18.498758	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:25.848106	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:15:38.421316	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:16:22.741573	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:16:22.741573	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:16:22.799297	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:21:32.306893	Felipe	login
2024-11-05 17:21:38.570573	Felipe	login
2024-11-05 17:21:38.570573	Felipe	login
2024-11-05 17:21:39.455662	Felipe	login
2024-11-05 17:21:45.68713	Felipe	login
2024-11-05 17:21:45.68713	Felipe	login
2024-11-05 17:22:16.854559	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:22:16.854559	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:22:16.926034	Jos├® Eduardo Medeiros Jochem	login
2024-11-26 14:34:37.033701	Felipe	login
2024-11-08 19:56:10.449869	Felipe	login
2024-11-08 19:56:54.318318	Felipe	login
2024-11-08 19:57:46.975964	Felipe	login
2024-11-26 14:34:37.033701	Felipe	login
2024-11-11 11:20:45.498526	Cleber	login
2024-11-11 11:20:45.498526	Cleber	login
2024-11-11 11:21:01.489098	Cleber	login
2024-11-11 11:21:07.860767	Cleber	login
2024-11-26 14:34:37.033701	Felipe	login
2024-11-11 11:21:16.049837	Cleber	login
2024-11-11 11:21:16.049837	Cleber	login
2024-11-11 11:21:19.937925	Cleber	login
2024-11-26 14:34:37.033701	Felipe	login
2024-11-11 11:21:28.088783	Cleber	login
2024-11-26 14:34:37.033701	Felipe	login
2024-11-11 11:21:40.689732	Cleber	login
2024-11-26 14:34:37.033701	Felipe	login
2024-11-26 14:35:52.615339	Felipe	login
2024-11-26 14:37:06.95997	Felipe	login
2024-11-04 20:13:11.876283	Matheus Machado dos Santos	login
2024-11-04 20:13:14.481513	Matheus Machado dos Santos	login
2024-11-04 20:13:16.741088	Matheus Machado dos Santos	login
2024-11-04 20:13:20.441263	Matheus Machado dos Santos	login
2024-10-29 00:58:35.376751	Cleber	login
2024-10-29 00:58:35.803262	Cleber	login
2024-10-29 00:58:35.803262	Cleber	login
2024-10-29 00:58:35.839323	Cleber	login
2024-10-29 00:58:36.311478	Cleber	login
2024-10-29 00:58:36.443495	Cleber	login
2024-10-29 00:58:36.839295	Cleber	login
2024-10-29 00:58:44.296776	Cleber	login
2024-11-22 22:03:56.807555	Felipe	login
2024-10-29 00:58:44.756559	Cleber	login
2024-11-08 17:25:16.284595	Felipe	login
2024-10-29 00:58:48.099759	Cleber	login
2024-11-08 17:25:17.216058	Felipe	login
2024-10-29 00:58:48.576394	Cleber	login
2024-11-08 17:25:28.289184	Felipe	login
2024-10-29 00:58:49.636636	Cleber	login
2024-11-08 17:25:28.511435	Felipe	login
2024-10-29 00:58:50.1358	Cleber	login
2024-11-08 17:25:42.862516	Felipe	login
2024-10-29 01:01:07.347577	Cleber	login
2024-10-29 01:01:07.401661	Cleber	login
2024-10-29 01:01:07.791115	Cleber	login
2024-10-29 01:01:08.198244	Cleber	login
2024-10-29 01:01:09.138573	Cleber	login
2024-11-08 17:25:43.536595	Felipe	login
2024-10-29 01:01:09.542699	Cleber	login
2024-11-08 17:25:45.104878	Felipe	login
2024-10-29 01:01:11.76943	Cleber	login
2024-10-29 01:01:11.828252	Cleber	login
2024-10-29 01:01:12.209537	Cleber	login
2024-10-29 01:01:12.712967	Cleber	login
2024-10-29 01:01:13.533044	Cleber	login
2024-11-08 17:25:59.721365	Felipe	login
2024-10-29 01:01:13.976248	Cleber	login
2024-11-05 14:20:25.606025	Breno	login
2024-10-29 01:01:40.102665	Cleber	login
2024-11-05 14:20:44.072008	Breno	login
2024-10-29 01:01:40.588397	Cleber	login
2024-11-05 14:20:45.569113	Breno	login
2024-11-05 14:23:04.160136	Breno	login
2024-11-04 02:10:09.947089	Matheus Machado dos Santos	login
2024-11-08 17:26:01.362437	Felipe	login
2024-11-04 02:10:11.796291	Matheus Machado dos Santos	login
2024-11-05 14:23:18.195431	Breno	login
2024-11-05 17:07:42.209332	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 15:26:51.660851	Felipe	login
2024-11-08 17:26:06.186011	Felipe	login
2024-11-04 15:26:53.565035	Felipe	login
2024-11-08 17:26:09.114766	Felipe	login
2024-11-04 15:38:15.19246	Felipe	login
2024-11-08 17:26:50.000031	Felipe	login
2024-11-04 15:38:15.568775	Felipe	login
2024-11-05 17:13:25.840802	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:25.840802	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 17:58:42.852073	Breno	login
2024-11-04 17:58:42.852073	Breno	login
2024-11-04 17:58:52.769728	Breno	login
2024-11-04 17:58:52.769728	Breno	login
2024-11-04 17:58:57.401039	Breno	login
2024-11-04 17:58:57.401039	Breno	login
2024-11-04 17:59:25.431168	Breno	login
2024-11-04 17:59:25.431168	Breno	login
2024-11-04 17:59:27.760606	Breno	login
2024-11-04 17:59:41.207967	Breno	login
2024-11-05 17:13:25.853274	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 17:59:43.521388	Breno	login
2024-11-05 17:13:25.853274	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 18:00:35.478505	Breno	login
2024-11-05 17:13:25.853274	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 18:00:36.235015	Breno	login
2024-11-05 17:15:38.410745	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 18:00:44.240241	Breno	login
2024-11-04 18:00:44.240241	Breno	login
2024-11-04 18:00:44.313654	Breno	login
2024-11-04 18:00:45.801406	Breno	login
2024-11-04 18:05:59.397035	Breno	login
2024-11-04 18:06:03.422681	Breno	login
2024-11-04 18:06:09.348788	Breno	login
2024-11-04 18:06:09.348788	Breno	login
2024-11-04 18:06:42.972466	Breno	login
2024-11-04 18:06:45.704404	Breno	login
2024-11-04 18:06:45.71298	Breno	login
2024-11-04 18:06:54.204365	Breno	login
2024-11-04 18:07:44.690057	Breno	login
2024-11-04 18:07:49.928736	Breno	login
2024-11-05 17:15:38.410745	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:51.399132	Matheus Machado dos Santos	login
2024-11-05 17:15:38.431869	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:53.485275	Matheus Machado dos Santos	login
2024-11-05 17:16:22.750782	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:53.989119	Matheus Machado dos Santos	login
2024-11-05 17:16:22.750782	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:54.452885	Matheus Machado dos Santos	login
2024-11-08 17:27:04.489356	Felipe	login
2024-11-04 20:11:54.989036	Matheus Machado dos Santos	login
2024-11-05 17:23:31.46305	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:55.536623	Matheus Machado dos Santos	login
2024-11-08 17:27:05.58796	Felipe	login
2024-11-04 20:11:56.071778	Matheus Machado dos Santos	login
2024-11-05 17:24:43.945974	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:56.63974	Matheus Machado dos Santos	login
2024-11-05 17:25:34.740783	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:57.540483	Matheus Machado dos Santos	login
2024-11-05 17:25:46.80312	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:58.356597	Matheus Machado dos Santos	login
2024-11-05 17:25:59.60598	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:58.967366	Matheus Machado dos Santos	login
2024-11-05 17:28:55.734287	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:59.621338	Matheus Machado dos Santos	login
2024-11-05 17:28:57.685569	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:12:00.445257	Matheus Machado dos Santos	login
2024-11-05 17:28:57.685569	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:12:01.39075	Matheus Machado dos Santos	login
2024-11-05 17:28:57.69337	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:12:02.151996	Matheus Machado dos Santos	login
2024-11-05 17:28:57.700302	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:12:02.864073	Matheus Machado dos Santos	login
2024-11-08 19:48:02.602936	Felipe	login
2024-11-04 20:12:03.704643	Matheus Machado dos Santos	login
2024-11-05 17:29:19.971602	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:12:04.429206	Matheus Machado dos Santos	login
2024-11-04 20:12:05.163285	Matheus Machado dos Santos	login
2024-11-08 19:49:30.577759	Felipe	login
2024-11-08 19:49:47.250779	Felipe	login
2024-11-08 19:55:46.742996	Felipe	login
2024-11-26 15:56:37.535693	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:56:34.13202	Felipe	login
2024-11-08 19:56:55.286909	Felipe	login
2024-11-11 11:21:42.724715	Cleber	login
2024-11-08 17:27:11.234858	Felipe	login
2024-11-05 14:18:27.763762	Breno	login
2024-11-05 14:18:28.151476	Breno	login
2024-11-05 14:18:49.859802	Breno	login
2024-11-05 14:18:49.859802	Breno	login
2024-11-05 14:18:49.859802	Breno	login
2024-11-05 14:19:56.653312	Breno	login
2024-11-05 14:19:59.724029	Breno	login
2024-11-05 14:19:59.724029	Breno	login
2024-11-05 14:20:00.828735	Breno	login
2024-11-05 14:20:00.828735	Breno	login
2024-11-05 14:20:03.310367	Breno	login
2024-11-05 14:20:04.00975	Breno	login
2024-11-26 15:56:33.728271	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 14:20:16.349787	Breno	login
2024-11-05 14:20:16.807276	Breno	login
2024-11-05 14:20:24.497076	Breno	login
2024-11-05 14:20:24.497076	Breno	login
2024-11-05 14:20:24.520944	Breno	login
2024-11-08 17:27:13.081152	Felipe	login
2024-11-05 17:02:00.090242	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:02:24.063445	Jos├® Eduardo Medeiros Jochem	login
2024-11-26 15:56:40.626538	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:02:36.529432	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:48:02.66648	Felipe	login
2024-11-05 17:07:38.32608	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:39.467088	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:49:45.134196	Felipe	login
2024-11-05 17:15:38.439561	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:21:32.888031	Felipe	login
2024-11-05 17:21:38.589227	Felipe	login
2024-11-05 17:21:42.377397	Felipe	login
2024-11-05 17:21:42.377397	Felipe	login
2024-11-05 17:21:47.620474	Felipe	login
2024-11-05 17:21:47.620474	Felipe	login
2024-11-05 17:21:47.620474	Felipe	login
2024-11-05 17:22:16.863065	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:22:16.863065	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:22:38.183513	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:22:38.183513	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:22:38.183513	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:23:31.444436	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:23:31.444436	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:23:31.62228	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:23:55.362331	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:24:42.912851	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:24:43.179366	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:24:43.179366	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:24:43.179366	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:24:43.96432	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:25:37.831041	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:25:59.58817	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:25:59.58817	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:26:00.490083	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:47.768402	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:47.768402	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:47.768402	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:48.982685	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:48.982685	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:56:10.165787	Felipe	login
2024-11-05 17:28:56.208824	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:57.68875	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:58.872682	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:58.872682	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:00.849	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:01.216016	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:02.51878	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:19.949741	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:19.949741	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:20.936234	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:20.936234	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:54.446718	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:54.446718	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:54.446718	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:54.446718	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:25.54759	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:26.104379	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:29.159851	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:32.959456	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:36.42581	Felipe	login
2024-11-05 17:30:51.169186	Felipe	login
2024-11-05 17:30:58.696086	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:58.696086	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:01.137937	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:01.137937	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:01.137937	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:03.684658	Felipe	login
2024-11-05 17:31:03.684658	Felipe	login
2024-11-05 17:31:04.644801	Felipe	login
2024-11-05 17:31:04.669746	Felipe	login
2024-11-05 17:31:11.104275	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:11.104275	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:56:53.426477	Felipe	login
2024-11-05 17:31:11.13129	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:11.13129	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:11.13129	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:35:41.457365	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:38:03.547316	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:38:03.586609	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:38:52.17428	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:42:39.30519	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:42:39.338303	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:45:07.391002	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:46:22.298482	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:46:22.333778	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:46:47.201349	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:46:47.201349	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:48:02.675575	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:54:52.594322	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:55:39.011488	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:55:55.91066	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:00:12.023197	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:01:31.796793	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:22.253314	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:42.393484	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:57:46.026695	Felipe	login
2024-11-11 11:21:44.245113	Cleber	login
2024-11-11 11:21:44.245113	Cleber	login
2024-11-13 20:31:22.47321	Jerusa Marchi	login
2024-11-04 20:12:05.892652	Matheus Machado dos Santos	login
2024-11-04 20:12:06.831994	Matheus Machado dos Santos	login
2024-11-04 20:12:07.751314	Matheus Machado dos Santos	login
2024-11-04 20:12:08.616757	Matheus Machado dos Santos	login
2024-11-04 20:12:09.456478	Matheus Machado dos Santos	login
2024-11-04 20:12:10.490957	Matheus Machado dos Santos	login
2024-11-04 20:12:11.444042	Matheus Machado dos Santos	login
2024-11-04 20:12:12.367974	Matheus Machado dos Santos	login
2024-11-04 20:12:13.3023	Matheus Machado dos Santos	login
2024-11-04 20:12:14.250897	Matheus Machado dos Santos	login
2024-11-04 20:12:15.228923	Matheus Machado dos Santos	login
2024-11-04 20:12:16.296055	Matheus Machado dos Santos	login
2024-11-08 17:27:40.262377	Felipe	login
2024-11-26 15:56:34.727787	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 17:27:49.297331	Felipe	login
2024-11-26 15:56:40.626538	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 17:29:27.95783	Felipe	login
2024-11-05 13:30:29.949669	Breno	login
2024-11-05 13:31:14.507699	Breno	login
2024-11-05 13:31:17.797468	Breno	login
2025-02-21 23:56:27.84425	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 20:29:21.790825	Felipe	login
2024-11-08 20:30:26.211641	Felipe	login
2025-02-23 18:04:15.230246	Andr├® W├╝st Zibetti	login
2024-11-13 20:29:18.354991	Jerusa Marchi	login
2024-11-13 20:31:12.998155	Jerusa Marchi	login
2024-11-05 14:20:29.942872	Breno	login
2024-11-05 14:20:32.366505	Breno	login
2024-11-05 14:20:35.720622	Breno	login
2024-11-05 14:20:36.404602	Breno	login
2024-11-05 14:20:44.000161	Breno	login
2024-11-05 14:20:44.011125	Breno	login
2024-11-05 14:21:46.406818	Breno	login
2024-11-05 14:22:50.049345	Breno	login
2024-11-05 14:22:50.049345	Breno	login
2024-11-05 14:23:06.88976	Breno	login
2025-02-23 18:04:17.706012	Andr├® W├╝st Zibetti	login
2024-11-05 14:23:18.204417	Breno	login
2024-11-05 14:23:18.204417	Breno	login
2024-11-05 17:01:59.435491	Jos├® Eduardo Medeiros Jochem	login
2024-11-13 20:31:22.487836	Jerusa Marchi	login
2024-11-13 20:31:27.268385	Jerusa Marchi	login
2024-11-05 17:02:36.155377	Jos├® Eduardo Medeiros Jochem	login
2024-11-13 20:31:36.088391	Jerusa Marchi	login
2024-11-05 17:07:33.738388	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:40.37617	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:08.883225	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:15.383864	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:15.383864	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:15.383864	Jos├® Eduardo Medeiros Jochem	login
2024-11-13 20:31:37.792003	Jerusa Marchi	login
2024-11-05 17:22:38.199231	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:23:55.768981	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:24:42.922809	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:26:00.518086	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:47.982237	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:47.982237	Jos├® Eduardo Medeiros Jochem	login
2024-11-13 20:31:58.084834	Jerusa Marchi	login
2024-11-05 17:29:02.527872	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:02.527872	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:02.527872	Jos├® Eduardo Medeiros Jochem	login
2024-11-13 20:32:57.282005	Jerusa Marchi	login
2024-11-13 20:33:19.578606	Jerusa Marchi	login
2024-11-05 17:30:29.171205	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:29.171205	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:29.171205	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:32.979826	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:32.979826	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:50.422421	Felipe	login
2024-11-05 17:30:58.684225	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:58.684225	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:58.763648	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:01.127298	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:01.127298	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:01.291495	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:03.699306	Felipe	login
2024-11-05 17:35:41.523432	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:38:52.221349	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:45:07.424689	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:48:02.653688	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:51:03.02767	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:51:03.050653	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:54:52.57005	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:54:59.160391	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:54:59.182363	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:55:38.991914	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:55:55.89219	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:00:12.009069	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:00:46.520807	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:00:46.530989	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:01:31.784996	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:01:51.679427	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:01:51.693384	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:22.237649	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:22.916687	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:22.916687	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:22.916687	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:22.916687	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:57.684754	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:57.696621	Jos├® Eduardo Medeiros Jochem	login
2024-11-14 13:49:18.699494	Jonata Tyska	login
2024-12-02 03:40:09.323989	Cleber	login
2024-11-05 18:02:57.711773	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:58.669004	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:03:48.39565	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:03:48.39565	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:03:48.403949	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:03:48.403949	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:03:48.413984	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:03:49.179582	Jos├® Eduardo Medeiros Jochem	login
2024-11-14 13:49:56.507308	Jonata Tyska	login
2024-11-14 13:51:20.429322	Jonata Tyska	login
2024-12-02 03:40:10.155875	Cleber	login
2024-11-14 13:51:56.244254	Jonata Tyska	login
2024-11-14 13:53:16.775897	Jonata Tyska	login
2024-11-19 12:36:58.593268	Jonata Tyska	login
2024-12-02 03:41:14.309308	Cleber	login
2024-11-26 11:15:33.42788	Andr├® W├╝st Zibetti	login
2024-11-05 18:03:51.9583	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:11:50.897189	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:16:04.293443	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:19:03.062123	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:20:52.610191	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:23:09.938685	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:32:49.314394	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:32:52.746154	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:32:52.847835	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:32:52.847835	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:32:52.847835	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:40.117724	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:40.117724	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:43.692501	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:43.692501	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:55.638158	Jos├® Eduardo Medeiros Jochem	login
2024-11-26 15:56:37.549428	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 17:27:48.540822	Felipe	login
2024-11-26 15:56:37.549428	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 17:27:57.879316	Felipe	login
2024-11-26 15:56:37.549428	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 17:30:07.31424	Felipe	login
2024-11-08 20:29:54.017937	Felipe	login
2024-11-13 20:28:55.273779	Jerusa Marchi	login
2024-11-13 20:31:14.352162	Jerusa Marchi	login
2024-11-26 16:34:16.516295	Jos├® Eduardo Medeiros Jochem	login
2024-11-13 20:31:24.06527	Jerusa Marchi	login
2024-11-13 20:31:29.848139	Jerusa Marchi	login
2024-11-13 20:31:40.245125	Jerusa Marchi	login
2024-11-26 16:34:31.042529	Jos├® Eduardo Medeiros Jochem	login
2024-11-13 20:32:57.299486	Jerusa Marchi	login
2024-11-13 20:33:18.837369	Jerusa Marchi	login
2024-11-26 11:15:51.940515	Andr├® W├╝st Zibetti	login
2024-11-26 11:16:28.188263	Andr├® W├╝st Zibetti	login
2024-11-14 13:49:41.103283	Jonata Tyska	login
2024-11-14 13:49:50.470391	Jonata Tyska	login
2024-11-26 11:16:28.827654	Andr├® W├╝st Zibetti	login
2024-11-26 16:34:33.17895	Jos├® Eduardo Medeiros Jochem	login
2024-11-14 13:49:57.209255	Jonata Tyska	login
2024-11-14 13:50:17.674116	Jonata Tyska	login
2024-11-14 13:51:26.347012	Jonata Tyska	login
2024-11-14 13:51:51.232624	Jonata Tyska	login
2024-11-26 11:17:26.723072	Andr├® W├╝st Zibetti	login
2024-11-14 13:51:57.381927	Jonata Tyska	login
2024-11-14 13:52:11.964525	Jonata Tyska	login
2024-11-26 16:34:33.17895	Jos├® Eduardo Medeiros Jochem	login
2024-11-26 11:17:54.568941	Andr├® W├╝st Zibetti	login
2024-11-18 17:20:20.854311	Felipe	login
2024-11-26 16:34:36.057437	Jos├® Eduardo Medeiros Jochem	login
2024-11-26 14:33:58.013083	Felipe	login
2024-11-19 12:37:31.649623	Jonata Tyska	login
2024-11-26 14:37:06.95997	Felipe	login
2024-11-19 12:38:09.57812	Jonata Tyska	login
2024-11-26 14:37:07.99073	Felipe	login
2024-11-19 12:38:17.925302	Jonata Tyska	login
2024-11-26 14:37:08.004741	Felipe	login
2024-11-19 12:38:30.496092	Jonata Tyska	login
2024-11-26 14:37:12.983453	Felipe	login
2024-11-19 12:38:40.266294	Jonata Tyska	login
2024-11-26 14:37:12.983453	Felipe	login
2024-11-19 12:39:40.935093	Jonata Tyska	login
2024-11-26 14:37:13.022141	Felipe	login
2024-11-19 12:39:47.598509	Jonata Tyska	login
2024-11-26 14:37:13.022141	Felipe	login
2024-11-19 12:39:52.142952	Jonata Tyska	login
2024-11-26 16:34:45.104706	Jos├® Eduardo Medeiros Jochem	login
2024-11-19 12:40:40.372587	Jonata Tyska	login
2024-11-26 16:34:45.104706	Jos├® Eduardo Medeiros Jochem	login
2024-11-19 12:40:41.298341	Jonata Tyska	login
2025-02-21 23:56:27.920766	Jos├® Eduardo Medeiros Jochem	login
2024-11-19 12:40:55.433045	Jonata Tyska	login
2025-02-21 23:56:41.943009	Jos├® Eduardo Medeiros Jochem	login
2024-11-19 12:41:19.850667	Jonata Tyska	login
2024-11-19 12:41:21.136433	Jonata Tyska	login
2024-11-19 12:42:37.282425	Jonata Tyska	login
2024-11-19 12:42:46.124628	Jonata Tyska	login
2025-02-21 23:56:41.943009	Jos├® Eduardo Medeiros Jochem	login
2024-11-19 13:42:08.297404	Jonata Tyska	login
2024-11-19 13:47:04.221418	Jonata Tyska	login
2024-11-19 13:47:51.83717	Jonata Tyska	login
2024-11-19 13:47:56.033974	Jonata Tyska	login
2024-11-19 13:48:14.851061	Jonata Tyska	login
2024-11-19 13:48:34.884227	Jonata Tyska	login
2024-11-19 14:18:11.498781	Luis	login
2024-11-19 14:18:19.118862	Luis	login
2024-11-19 14:56:13.549836	Luis	login
2024-11-19 14:56:20.596382	Luis	login
2024-11-19 14:56:44.277639	Luis	login
2025-02-21 23:56:44.429671	Jos├® Eduardo Medeiros Jochem	login
2025-02-21 23:56:44.458411	Jos├® Eduardo Medeiros Jochem	login
2025-02-21 23:56:44.528522	Jos├® Eduardo Medeiros Jochem	login
2024-11-19 14:56:54.215173	Luis	login
2024-11-19 14:56:54.329152	Luis	login
2024-11-19 14:57:10.501953	Luis	login
2024-11-19 14:57:19.30824	Luis	login
2025-02-23 18:04:18.271823	Andr├® W├╝st Zibetti	login
2025-02-23 18:04:18.841474	Andr├® W├╝st Zibetti	login
2024-11-19 14:58:48.523049	Luis	login
2024-11-19 14:58:50.29352	Luis	login
2024-11-19 14:58:50.29352	Luis	login
2024-11-19 14:59:05.759379	Luis	login
2024-11-19 14:59:12.886651	Luis	login
2024-11-19 14:59:12.886651	Luis	login
2024-11-19 14:59:18.469757	Luis	login
2024-11-19 14:59:20.163506	Luis	login
2024-11-19 14:59:20.163506	Luis	login
2025-02-23 18:04:19.439347	Andr├® W├╝st Zibetti	login
2025-02-23 18:05:31.657516	Andr├® W├╝st Zibetti	login
2025-02-23 18:05:32.00392	Andr├® W├╝st Zibetti	login
2024-11-19 20:45:53.429711	Andr├® Teixeira Milioli	login
2024-11-19 20:45:54.756691	Andr├® Teixeira Milioli	login
2024-11-19 20:46:06.904033	Andr├® Teixeira Milioli	login
2025-02-23 18:05:47.800114	Andr├® W├╝st Zibetti	login
2025-02-23 18:05:47.870338	Andr├® W├╝st Zibetti	login
2025-02-23 18:05:47.904483	Andr├® W├╝st Zibetti	login
2024-11-19 20:46:16.315665	Andr├® Teixeira Milioli	login
2024-11-19 20:46:20.095656	Andr├® Teixeira Milioli	login
2024-11-19 20:46:21.12998	Andr├® Teixeira Milioli	login
2025-02-23 18:05:52.130893	Andr├® W├╝st Zibetti	login
2024-12-02 03:40:09.371952	Cleber	login
2024-12-02 03:40:13.275977	Cleber	login
2024-11-19 20:46:43.093283	Andr├® Teixeira Milioli	login
2024-11-19 20:46:43.856821	Andr├® Teixeira Milioli	login
2024-11-19 20:47:30.606641	Andr├® Teixeira Milioli	login
2024-12-02 03:40:53.916032	Cleber	login
2024-12-02 03:41:14.917007	Cleber	login
2024-12-02 03:41:18.013707	Cleber	login
2025-02-23 18:05:52.808396	Andr├® W├╝st Zibetti	login
2025-02-23 18:05:57.167364	Andr├® W├╝st Zibetti	login
2024-11-05 18:03:51.987311	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:04:04.024756	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:04:54.112754	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:05:57.669669	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:06:08.239515	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:07:16.060849	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:08:43.881853	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:09:27.94421	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:10:32.582086	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:12:59.538963	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:17:52.382711	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:20:52.643305	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:23:09.970068	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:32:52.758093	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:35:16.127094	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:35:16.127094	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:35:16.127094	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:26.7694	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:38.975311	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:43.677386	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:43.677386	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:43.677386	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:43.677386	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:54.37819	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:54.37819	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:54.37819	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:54.37819	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:54.395845	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 17:27:42.039376	Felipe	login
2024-11-26 16:34:19.033859	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 17:27:57.50324	Felipe	login
2024-11-26 16:34:40.679772	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 17:30:06.922149	Felipe	login
2024-11-26 16:34:45.11454	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 20:29:57.646987	Felipe	login
2024-11-26 16:34:45.11454	Jos├® Eduardo Medeiros Jochem	login
2024-11-13 20:29:18.387644	Jerusa Marchi	login
2024-11-13 20:30:03.595756	Jerusa Marchi	login
2024-11-13 20:31:18.694492	Jerusa Marchi	login
2024-11-13 20:31:32.896586	Jerusa Marchi	login
2024-11-13 20:31:57.060708	Jerusa Marchi	login
2024-11-26 16:34:45.11454	Jos├® Eduardo Medeiros Jochem	login
2024-11-14 13:49:15.885375	Jonata Tyska	login
2024-11-14 13:49:51.147438	Jonata Tyska	login
2024-11-14 13:50:18.934194	Jonata Tyska	login
2025-02-23 18:05:57.996143	Andr├® W├╝st Zibetti	login
2024-11-14 13:51:51.801619	Jonata Tyska	login
2024-11-14 13:53:15.912375	Jonata Tyska	login
2024-11-18 17:20:18.672552	Felipe	login
2025-02-23 18:05:58.029559	Andr├® W├╝st Zibetti	login
2024-11-18 17:20:43.829954	Felipe	login
2024-11-18 17:20:43.829954	Felipe	login
2024-11-19 12:36:51.371086	Jonata Tyska	login
2025-02-23 18:06:36.750276	Andr├® W├╝st Zibetti	login
2024-11-19 12:38:17.250275	Jonata Tyska	login
2025-02-23 18:06:36.772391	Andr├® W├╝st Zibetti	login
2024-11-19 12:39:11.888506	Jonata Tyska	login
2024-11-19 12:39:52.984534	Jonata Tyska	login
2024-11-19 12:41:04.324523	Jonata Tyska	login
2024-11-19 12:42:44.770173	Jonata Tyska	login
2024-11-19 12:42:47.311623	Jonata Tyska	login
2024-11-26 11:15:35.43582	Andr├® W├╝st Zibetti	login
2024-11-19 13:41:42.646094	Jonata Tyska	login
2024-11-19 13:41:57.855042	Jonata Tyska	login
2024-11-26 11:16:24.93285	Andr├® W├╝st Zibetti	login
2024-11-26 11:16:29.839017	Andr├® W├╝st Zibetti	login
2024-11-19 13:47:20.83571	Jonata Tyska	login
2024-11-19 13:47:44.56233	Jonata Tyska	login
2024-11-26 11:17:53.725729	Andr├® W├╝st Zibetti	login
2024-11-19 13:47:54.543523	Jonata Tyska	login
2024-11-26 14:34:05.98248	Felipe	login
2024-11-19 13:48:13.884467	Jonata Tyska	login
2024-11-26 14:34:05.98248	Felipe	login
2024-11-19 13:48:33.628755	Jonata Tyska	login
2024-11-19 13:48:36.110979	Jonata Tyska	login
2024-11-26 14:34:05.98248	Felipe	login
2024-11-26 14:34:05.98248	Felipe	login
2024-11-26 14:34:05.98248	Felipe	login
2024-11-19 14:18:26.965603	Luis	login
2024-11-19 14:18:27.025585	Luis	login
2024-11-19 14:18:44.612587	Luis	login
2024-11-26 14:34:05.98248	Felipe	login
2024-11-26 14:37:06.999604	Felipe	login
2024-11-19 14:56:45.618426	Luis	login
2024-11-19 14:56:47.05963	Luis	login
2024-11-19 14:57:43.75062	Luis	login
2024-11-19 14:57:43.75062	Luis	login
2024-11-19 14:58:47.18858	Luis	login
2024-11-26 14:37:14.1834	Felipe	login
2024-11-19 14:59:05.714773	Luis	login
2024-11-19 14:59:18.445736	Luis	login
2024-11-19 19:58:34.2014	Andr├® Teixeira Milioli	login
2024-11-19 19:58:41.105482	Andr├® Teixeira Milioli	login
2024-11-26 14:37:14.1834	Felipe	login
2024-11-27 14:38:59.441339	Cleber	login
2024-11-19 20:46:07.918663	Andr├® Teixeira Milioli	login
2024-11-19 20:46:15.227663	Andr├® Teixeira Milioli	login
2024-11-27 14:39:02.048564	Cleber	login
2024-11-27 14:39:02.921513	Cleber	login
2024-11-19 20:46:28.02134	Andr├® Teixeira Milioli	login
2024-11-19 20:46:29.025396	Andr├® Teixeira Milioli	login
2024-11-27 14:39:03.560631	Cleber	login
2024-11-27 14:39:04.873308	Cleber	login
2024-11-19 20:47:31.430959	Andr├® Teixeira Milioli	login
2024-11-19 20:47:39.304607	Andr├® Teixeira Milioli	login
2024-11-27 14:39:06.368732	Cleber	login
2024-11-19 20:47:40.12187	Andr├® Teixeira Milioli	login
2024-11-27 14:39:10.261845	Cleber	login
2024-11-19 20:47:54.968592	Andr├® Teixeira Milioli	login
2024-11-27 14:39:11.417895	Cleber	login
2024-11-19 20:47:55.475391	Andr├® Teixeira Milioli	login
2024-11-27 14:39:12.375531	Cleber	login
2024-11-19 20:48:35.751725	Andr├® Teixeira Milioli	login
2024-11-27 14:39:14.117662	Cleber	login
2024-11-19 20:48:36.249584	Andr├® Teixeira Milioli	login
2024-11-26 17:57:24.587628	Cleber	login
2024-11-19 20:49:17.964921	Andr├® Teixeira Milioli	login
2024-11-27 14:39:15.833424	Cleber	login
2024-11-27 14:39:17.215258	Cleber	login
2024-11-27 14:39:18.74499	Cleber	login
2024-11-27 14:39:20.078382	Cleber	login
2024-11-27 14:39:20.688537	Cleber	login
2024-11-27 14:39:22.200658	Cleber	login
2024-11-27 14:39:23.403598	Cleber	login
2024-11-27 14:39:25.024515	Cleber	login
2024-11-27 14:39:26.396955	Cleber	login
2024-11-27 14:39:27.677475	Cleber	login
2024-11-27 14:39:29.511922	Cleber	login
2024-11-05 18:04:54.094712	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:05:57.650334	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:06:08.220023	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:07:16.042111	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:08:43.826118	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:09:27.886619	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:10:32.530669	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:11:50.849176	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:12:59.490506	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:16:04.244292	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:17:52.339416	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:18:23.249068	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:18:23.249068	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:19:03.101154	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:32:49.340662	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:26.741845	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:38.961636	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:39.34337	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:39.34337	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:38:01.780253	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:38:02.029629	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:46:04.213116	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:46:04.395729	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:48:53.722818	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:48:53.838069	Jos├® Eduardo Medeiros Jochem	login
2024-11-26 16:34:20.685189	Jos├® Eduardo Medeiros Jochem	login
2024-11-06 13:36:15.195268	Matheus Machado dos Santos	login
2024-11-08 19:42:29.523499	Felipe	login
2024-11-06 13:36:17.277634	Matheus Machado dos Santos	login
2024-11-26 16:34:36.071084	Jos├® Eduardo Medeiros Jochem	login
2024-11-06 13:36:59.005051	Matheus Machado dos Santos	login
2024-11-08 19:42:47.428893	Felipe	login
2024-11-06 13:36:59.191794	Matheus Machado dos Santos	login
2024-11-26 16:34:41.353996	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:42:56.352482	Felipe	login
2024-11-07 21:38:57.036959	Matheus Machado dos Santos	login
2025-02-23 18:06:36.842931	Andr├® W├╝st Zibetti	login
2024-11-07 21:39:01.349912	Matheus Machado dos Santos	login
2024-11-08 19:43:07.95519	Felipe	login
2024-11-07 21:39:24.37747	Matheus Machado dos Santos	login
2024-11-27 14:39:31.879294	Cleber	login
2024-11-07 21:39:24.648373	Matheus Machado dos Santos	login
2024-11-08 19:43:09.93226	Felipe	login
2024-11-27 14:39:39.556997	Cleber	login
2024-11-07 23:38:46.047297	Matheus Machado dos Santos	login
2024-11-08 19:43:14.095976	Felipe	login
2024-11-07 23:38:46.602757	Matheus Machado dos Santos	login
2024-11-27 14:39:44.972616	Cleber	login
2024-11-07 23:39:01.307777	Matheus Machado dos Santos	login
2024-11-08 19:43:19.425418	Felipe	login
2024-11-07 23:39:01.661424	Matheus Machado dos Santos	login
2024-11-27 14:39:52.693655	Cleber	login
2024-11-08 19:44:08.901682	Felipe	login
2024-11-08 02:35:50.651766	Felipe	login
2024-11-26 17:57:25.369026	Cleber	login
2024-11-08 02:35:51.051697	Felipe	login
2024-11-08 19:44:53.884663	Felipe	login
2024-11-08 02:36:01.017504	Felipe	login
2024-11-08 19:45:31.08748	Felipe	login
2024-11-08 02:36:01.241844	Felipe	login
2024-11-27 14:40:05.888374	Cleber	login
2024-11-08 02:36:06.723002	Felipe	login
2024-11-08 19:46:02.174523	Felipe	login
2024-11-08 02:36:06.969591	Felipe	login
2024-11-27 14:40:13.699132	Cleber	login
2024-11-08 02:36:10.559802	Felipe	login
2024-11-08 19:46:06.708494	Felipe	login
2024-11-08 02:36:10.796771	Felipe	login
2024-11-27 14:40:19.692818	Cleber	login
2024-11-08 02:36:11.893808	Felipe	login
2024-11-08 19:46:29.574222	Felipe	login
2024-11-08 02:45:42.992506	Felipe	login
2024-11-08 02:45:42.992506	Felipe	login
2024-11-08 02:45:55.712383	Felipe	login
2024-11-08 02:45:56.652823	Felipe	login
2024-11-08 02:46:05.103909	Felipe	login
2024-11-08 02:46:06.522653	Felipe	login
2024-11-08 02:46:06.522653	Felipe	login
2024-11-08 02:46:32.34798	Felipe	login
2024-11-08 02:46:32.417023	Felipe	login
2024-11-08 02:46:33.202876	Felipe	login
2024-11-08 02:46:34.128642	Felipe	login
2024-11-08 02:46:40.780026	Felipe	login
2024-11-08 02:46:40.807336	Felipe	login
2024-11-08 02:46:41.586998	Felipe	login
2024-11-08 02:46:42.424729	Felipe	login
2024-11-08 02:47:13.030642	Felipe	login
2024-11-08 02:47:37.273938	Felipe	login
2024-11-08 02:47:37.355205	Felipe	login
2024-11-08 19:46:43.43977	Felipe	login
2024-11-08 12:55:04.547609	Matheus Machado dos Santos	login
2024-11-08 19:47:25.825924	Felipe	login
2024-11-08 12:55:06.930656	Matheus Machado dos Santos	login
2024-11-08 19:47:36.497314	Felipe	login
2024-11-08 12:55:18.241181	Matheus Machado dos Santos	login
2024-11-08 19:49:16.08787	Felipe	login
2024-11-08 12:55:18.689603	Matheus Machado dos Santos	login
2024-11-08 19:49:41.689006	Felipe	login
2024-11-08 12:55:23.238421	Matheus Machado dos Santos	login
2024-11-27 14:40:28.008253	Cleber	login
2024-11-08 12:55:23.848865	Matheus Machado dos Santos	login
2024-11-08 19:55:58.901222	Felipe	login
2024-11-27 14:40:38.76604	Cleber	login
2024-11-08 13:07:20.698132	Matheus Machado dos Santos	login
2024-11-08 19:56:35.570458	Felipe	login
2024-11-08 13:07:21.192924	Matheus Machado dos Santos	login
2024-11-08 19:57:17.984407	Felipe	login
2024-11-08 13:07:39.823175	Matheus Machado dos Santos	login
2024-11-08 19:57:17.984407	Felipe	login
2024-11-08 13:07:40.216024	Matheus Machado dos Santos	login
2024-11-27 14:40:45.398942	Cleber	login
2024-11-11 11:20:44.028224	Cleber	login
2024-11-08 14:28:22.379405	Jonata Tyska	login
2024-11-11 11:21:04.933667	Cleber	login
2024-11-08 14:28:24.59354	Jonata Tyska	login
2024-11-27 14:40:56.698864	Cleber	login
2024-11-11 11:21:13.943801	Cleber	login
2024-11-27 14:41:04.917983	Cleber	login
2024-11-11 11:21:16.112374	Cleber	login
2024-11-11 11:21:20.278018	Cleber	login
2024-11-27 14:41:11.771083	Cleber	login
2024-11-11 11:21:37.266227	Cleber	login
2024-11-27 14:41:21.270322	Cleber	login
2024-11-11 11:21:40.746312	Cleber	login
2024-11-11 11:21:41.542961	Cleber	login
2024-11-11 11:21:42.769931	Cleber	login
2024-11-11 11:21:45.109599	Cleber	login
2024-11-13 20:28:59.03916	Jerusa Marchi	login
2024-11-13 20:31:09.965797	Jerusa Marchi	login
2024-11-27 14:41:30.794027	Cleber	login
2024-11-25 06:44:37.670167	Cleber	login
2024-11-25 06:44:55.609972	Cleber	login
2024-11-25 06:44:56.762282	Cleber	login
2024-11-08 19:42:28.933988	Felipe	login
2024-11-08 14:28:39.154355	Jonata Tyska	login
2024-11-26 16:34:21.636588	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 14:28:41.479696	Jonata Tyska	login
2024-11-08 19:42:39.961667	Felipe	login
2024-11-08 14:28:59.000936	Jonata Tyska	login
2024-11-26 16:34:21.636588	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 14:29:01.153613	Jonata Tyska	login
2024-11-08 19:42:55.961279	Felipe	login
2024-11-08 14:29:19.473254	Jonata Tyska	login
2024-11-26 16:34:31.654336	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 14:29:22.200278	Jonata Tyska	login
2024-11-08 19:43:06.239821	Felipe	login
2024-11-08 14:29:27.298924	Jonata Tyska	login
2024-11-26 16:34:33.193641	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 14:29:29.117752	Jonata Tyska	login
2024-11-08 19:43:09.473617	Felipe	login
2024-11-08 14:29:34.145088	Jonata Tyska	login
2024-11-25 06:43:43.322948	Cleber	login
2024-11-08 14:29:35.928198	Jonata Tyska	login
2024-11-08 19:43:12.930619	Felipe	login
2024-11-08 14:29:37.85071	Jonata Tyska	login
2024-11-25 06:44:54.878606	Cleber	login
2024-11-08 14:29:39.048386	Jonata Tyska	login
2024-11-08 19:43:19.031497	Felipe	login
2024-11-08 14:29:41.608295	Jonata Tyska	login
2024-11-25 06:44:56.202328	Cleber	login
2024-11-08 14:29:42.775618	Jonata Tyska	login
2024-11-08 19:43:37.185301	Felipe	login
2024-11-08 14:29:49.740187	Jonata Tyska	login
2024-11-26 16:34:33.193641	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 14:29:51.858488	Jonata Tyska	login
2024-11-08 19:44:38.547185	Felipe	login
2024-11-08 14:29:56.241106	Jonata Tyska	login
2024-11-08 19:45:30.44618	Felipe	login
2024-11-08 14:29:57.847616	Jonata Tyska	login
2024-11-25 06:45:00.782286	Cleber	login
2024-11-08 14:30:00.909433	Jonata Tyska	login
2024-11-08 19:45:59.981658	Felipe	login
2024-11-08 14:30:01.857947	Jonata Tyska	login
2024-11-26 16:34:33.193641	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 14:30:03.09061	Jonata Tyska	login
2024-11-08 19:46:06.236353	Felipe	login
2024-11-08 14:30:06.158863	Jonata Tyska	login
2024-11-25 06:45:12.114175	Cleber	login
2024-11-08 14:30:07.082395	Jonata Tyska	login
2024-11-08 19:46:11.905189	Felipe	login
2024-11-08 14:30:10.437078	Jonata Tyska	login
2024-11-08 19:46:31.714484	Felipe	login
2024-11-08 14:30:11.491627	Jonata Tyska	login
2024-11-08 19:46:45.530456	Felipe	login
2024-11-08 14:30:16.015106	Jonata Tyska	login
2024-11-08 19:47:27.851943	Felipe	login
2024-11-08 14:30:17.08621	Jonata Tyska	login
2024-11-08 19:48:13.775248	Felipe	login
2024-11-08 14:30:21.44223	Jonata Tyska	login
2024-11-08 19:48:17.422696	Felipe	login
2024-11-08 14:30:22.525174	Jonata Tyska	login
2024-11-08 19:48:28.944258	Felipe	login
2024-11-08 19:49:44.07881	Felipe	login
2024-11-08 15:20:24.980378	Felipe	login
2024-11-25 06:45:52.514833	Cleber	login
2024-11-08 15:20:25.384134	Felipe	login
2024-11-08 19:55:59.206699	Felipe	login
2024-11-08 15:23:22.134687	Felipe	login
2024-11-08 15:23:22.214555	Felipe	login
2024-11-08 15:23:37.793195	Felipe	login
2024-11-08 15:25:24.135939	Felipe	login
2024-11-26 16:34:33.193641	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 15:25:24.7271	Felipe	login
2024-11-08 19:56:36.572976	Felipe	login
2024-11-08 15:25:31.966722	Felipe	login
2024-11-08 19:57:45.21069	Felipe	login
2024-11-08 17:09:47.825954	Felipe	login
2024-11-11 11:20:41.553643	Cleber	login
2024-11-08 17:09:50.015124	Felipe	login
2024-11-25 06:47:42.281745	Cleber	login
2024-11-08 17:10:28.715761	Felipe	login
2024-11-08 17:10:37.953301	Felipe	login
2024-11-11 11:20:45.542528	Cleber	login
2024-11-08 17:10:38.400606	Felipe	login
2024-11-11 11:20:47.054324	Cleber	login
2024-11-08 17:10:43.388773	Felipe	login
2024-11-08 17:10:45.595637	Felipe	login
2024-11-08 17:10:51.695814	Felipe	login
2024-11-08 17:10:54.905934	Felipe	login
2024-11-11 11:20:47.097681	Cleber	login
2024-11-11 11:20:50.249961	Cleber	login
2024-11-11 11:20:55.38	Cleber	login
2024-11-11 11:20:55.423448	Cleber	login
2024-11-11 11:20:56.736776	Cleber	login
2024-11-11 11:20:59.249354	Cleber	login
2024-11-11 11:21:00.672525	Cleber	login
2024-11-11 11:21:07.425397	Cleber	login
2024-11-27 14:39:33.794471	Cleber	login
2024-11-11 11:21:14.364944	Cleber	login
2024-11-11 11:21:17.304071	Cleber	login
2024-11-27 14:39:35.668292	Cleber	login
2024-11-11 11:21:27.762331	Cleber	login
2024-11-26 11:15:52.794886	Andr├® W├╝st Zibetti	login
2024-11-11 11:21:37.588806	Cleber	login
2024-11-11 11:21:42.406478	Cleber	login
2024-11-11 11:21:43.711476	Cleber	login
2024-11-27 14:39:36.761084	Cleber	login
2024-11-13 20:29:41.0108	Jerusa Marchi	login
2024-11-13 20:31:17.483711	Jerusa Marchi	login
2024-11-13 20:31:30.825029	Jerusa Marchi	login
2024-11-13 20:31:40.905493	Jerusa Marchi	login
2024-11-26 11:17:25.842681	Andr├® W├╝st Zibetti	login
2024-11-13 20:32:59.049348	Jerusa Marchi	login
2024-11-26 11:17:27.618483	Andr├® W├╝st Zibetti	login
2024-11-27 14:39:38.248108	Cleber	login
2024-11-14 13:49:41.944021	Jonata Tyska	login
2024-11-26 11:17:55.423988	Andr├® W├╝st Zibetti	login
2024-11-14 13:50:02.174516	Jonata Tyska	login
2024-11-14 13:51:27.17372	Jonata Tyska	login
2024-11-27 14:39:40.223057	Cleber	login
2024-11-14 13:51:58.619826	Jonata Tyska	login
2024-11-27 14:39:41.179621	Cleber	login
2024-11-27 14:39:42.472768	Cleber	login
2024-11-18 17:20:41.757758	Felipe	login
2024-11-18 17:20:41.757758	Felipe	login
2024-11-27 14:39:43.581651	Cleber	login
2024-11-19 12:37:46.708413	Jonata Tyska	login
2024-11-27 14:39:46.483688	Cleber	login
2024-11-19 12:38:31.199422	Jonata Tyska	login
2024-11-27 14:39:48.598313	Cleber	login
2024-11-19 12:39:48.32016	Jonata Tyska	login
2024-11-27 14:39:50.888199	Cleber	login
2024-11-19 12:40:54.743975	Jonata Tyska	login
2024-11-19 12:42:34.565805	Jonata Tyska	login
2024-11-19 13:41:35.302434	Jonata Tyska	login
2024-11-27 14:39:52.017704	Cleber	login
2024-11-19 13:42:09.795696	Jonata Tyska	login
2024-11-19 13:47:17.678691	Jonata Tyska	login
2024-11-19 13:47:18.895142	Jonata Tyska	login
2024-11-27 14:39:55.779626	Cleber	login
2024-11-27 14:39:59.023717	Cleber	login
2024-11-27 14:39:59.737244	Cleber	login
2024-11-27 14:40:04.064684	Cleber	login
2024-11-27 14:40:07.851347	Cleber	login
2024-11-27 14:40:09.293188	Cleber	login
2024-11-27 14:40:10.396025	Cleber	login
2024-11-27 14:40:11.562671	Cleber	login
2024-11-27 14:40:14.745664	Cleber	login
2024-11-27 14:40:15.963962	Cleber	login
2024-11-19 20:49:51.995331	Andr├® Teixeira Milioli	login
2024-11-27 14:40:22.498659	Cleber	login
2024-11-27 14:40:30.97341	Cleber	login
2024-11-19 20:52:35.553602	Andr├® Teixeira Milioli	login
2024-11-19 20:53:49.408813	Andr├® Teixeira Milioli	login
2024-11-19 20:54:18.716383	Andr├® Teixeira Milioli	login
2024-11-27 14:40:41.411685	Cleber	login
2024-11-27 14:40:51.26729	Cleber	login
2024-11-27 14:40:59.216355	Cleber	login
2024-11-25 06:44:51.614879	Cleber	login
2024-11-25 06:44:52.710087	Cleber	login
2024-11-25 06:44:57.422701	Cleber	login
2024-11-25 06:44:59.890686	Cleber	login
2024-11-25 06:45:11.282254	Cleber	login
2024-11-25 06:45:51.602276	Cleber	login
2024-11-27 14:41:07.698874	Cleber	login
2024-11-25 06:47:41.430397	Cleber	login
2024-11-26 11:15:37.845634	Andr├® W├╝st Zibetti	login
2024-11-26 11:15:37.845634	Andr├® W├╝st Zibetti	login
2024-11-26 11:16:27.248836	Andr├® W├╝st Zibetti	login
2024-11-26 11:16:28.209362	Andr├® W├╝st Zibetti	login
2024-11-26 11:16:29.274981	Andr├® W├╝st Zibetti	login
2024-11-26 11:17:25.832692	Andr├® W├╝st Zibetti	login
2024-11-26 11:17:46.634948	Andr├® W├╝st Zibetti	login
2024-11-26 11:17:58.917949	Andr├® W├╝st Zibetti	login
2024-11-27 14:41:16.377971	Cleber	login
2024-11-27 14:41:25.497271	Cleber	login
2024-11-27 14:41:33.884768	Cleber	login
2024-11-27 14:41:41.891862	Cleber	login
2024-11-27 14:41:51.542489	Cleber	login
2024-11-27 14:42:05.048783	Cleber	login
2024-11-27 14:42:11.827353	Cleber	login
2024-11-27 14:42:19.070324	Cleber	login
2024-11-27 14:42:26.854764	Cleber	login
2024-11-27 14:42:34.863912	Cleber	login
2024-11-27 14:42:44.091685	Cleber	login
2024-11-27 14:42:53.481996	Cleber	login
2024-11-27 14:43:08.131662	Cleber	login
2024-11-27 14:43:20.091796	Cleber	login
2024-11-27 14:43:31.060824	Cleber	login
2024-11-27 14:43:41.668874	Cleber	login
2024-11-27 14:43:52.061501	Cleber	login
2024-11-27 14:44:04.025446	Cleber	login
2024-11-27 14:44:13.613477	Cleber	login
2024-11-27 14:44:23.388804	Cleber	login
2024-12-02 03:40:10.075844	Cleber	login
2024-12-02 03:41:11.757649	Cleber	login
2024-12-02 03:41:16.757269	Cleber	login
2024-11-04 18:06:45.71298	Breno	login
2024-11-04 18:06:54.204365	Breno	login
2024-11-04 18:07:44.690057	Breno	login
2024-11-04 18:07:49.928736	Breno	login
2024-11-05 17:15:38.410745	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:51.399132	Matheus Machado dos Santos	login
2024-11-05 17:15:38.431869	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:53.485275	Matheus Machado dos Santos	login
2024-11-05 17:16:22.750782	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:53.989119	Matheus Machado dos Santos	login
2024-11-05 17:16:22.750782	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:54.452885	Matheus Machado dos Santos	login
2024-11-08 17:27:04.489356	Felipe	login
2024-11-04 20:11:54.989036	Matheus Machado dos Santos	login
2024-12-04 02:58:54.138038	Cleber	login
2024-12-04 02:59:02.558678	Cleber	login
2024-12-04 02:59:15.716493	Cleber	login
2024-12-04 02:59:23.59915	Cleber	login
2024-12-04 02:59:32.778235	Cleber	login
2024-12-04 03:00:19.555771	Cleber	login
2024-12-04 03:02:30.024939	Cleber	login
2024-11-05 17:23:31.46305	Jos├® Eduardo Medeiros Jochem	login
2024-12-10 13:07:55.649477	M├írcio Castro	login
2024-12-10 13:08:51.19196	M├írcio Castro	login
2024-12-10 13:08:58.903618	M├írcio Castro	login
2024-12-10 13:09:54.859068	Jonata Tyska	login
2024-11-04 20:11:55.536623	Matheus Machado dos Santos	login
2024-11-08 17:27:05.58796	Felipe	login
2024-11-04 20:11:56.071778	Matheus Machado dos Santos	login
2024-11-05 17:24:43.945974	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:56.63974	Matheus Machado dos Santos	login
2024-11-05 17:25:34.740783	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:57.540483	Matheus Machado dos Santos	login
2024-11-05 17:25:46.80312	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:58.356597	Matheus Machado dos Santos	login
2025-04-04 18:03:36.437605	Matheus Machado dos Santos	login
2024-11-05 17:25:59.60598	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:58.967366	Matheus Machado dos Santos	login
2024-11-05 17:28:55.734287	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:11:59.621338	Matheus Machado dos Santos	login
2024-11-05 17:28:57.685569	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:12:00.445257	Matheus Machado dos Santos	login
2024-11-05 17:28:57.685569	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:12:01.39075	Matheus Machado dos Santos	login
2024-11-05 17:28:57.69337	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:12:02.151996	Matheus Machado dos Santos	login
2024-11-05 17:28:57.700302	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:12:02.864073	Matheus Machado dos Santos	login
2024-11-08 19:48:02.602936	Felipe	login
2024-11-04 20:12:03.704643	Matheus Machado dos Santos	login
2024-11-05 17:29:19.971602	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 20:12:04.429206	Matheus Machado dos Santos	login
2024-11-04 20:12:05.163285	Matheus Machado dos Santos	login
2024-11-08 19:49:30.577759	Felipe	login
2024-11-08 19:49:47.250779	Felipe	login
2024-11-08 19:55:46.742996	Felipe	login
2024-11-26 15:56:37.535693	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:56:34.13202	Felipe	login
2024-11-08 19:56:55.286909	Felipe	login
2024-11-11 11:21:42.724715	Cleber	login
2024-11-08 17:27:11.234858	Felipe	login
2024-11-05 14:18:27.763762	Breno	login
2024-11-05 14:18:28.151476	Breno	login
2024-11-05 14:18:49.859802	Breno	login
2024-11-05 14:18:49.859802	Breno	login
2024-11-05 14:18:49.859802	Breno	login
2024-11-05 14:19:56.653312	Breno	login
2024-11-05 14:19:59.724029	Breno	login
2024-11-05 14:19:59.724029	Breno	login
2024-11-05 14:20:00.828735	Breno	login
2024-11-05 14:20:00.828735	Breno	login
2024-11-05 14:20:03.310367	Breno	login
2024-11-05 14:20:04.00975	Breno	login
2024-11-26 15:56:33.728271	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 14:20:16.349787	Breno	login
2024-11-05 14:20:16.807276	Breno	login
2024-11-05 14:20:24.497076	Breno	login
2024-11-05 14:20:24.497076	Breno	login
2024-11-05 14:20:24.520944	Breno	login
2024-11-08 17:27:13.081152	Felipe	login
2024-11-05 17:02:00.090242	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:02:24.063445	Jos├® Eduardo Medeiros Jochem	login
2024-11-26 15:56:40.626538	Jos├® Eduardo Medeiros Jochem	login
2024-11-19 20:49:30.431201	Andr├® Teixeira Milioli	login
2024-11-19 20:52:14.757591	Andr├® Teixeira Milioli	login
2024-11-19 20:52:58.269166	Andr├® Teixeira Milioli	login
2024-11-27 14:40:16.741233	Cleber	login
2024-11-27 14:40:17.579435	Cleber	login
2024-11-27 14:40:20.817361	Cleber	login
2024-11-27 14:40:24.037819	Cleber	login
2024-11-27 14:40:25.839506	Cleber	login
2024-11-27 14:40:29.606062	Cleber	login
2024-11-27 14:40:33.787139	Cleber	login
2024-11-25 06:43:45.726472	Cleber	login
2024-11-25 06:44:57.857806	Cleber	login
2024-11-25 06:45:08.918625	Cleber	login
2024-11-25 06:45:50.802749	Cleber	login
2024-11-25 06:47:35.481647	Cleber	login
2024-11-25 06:51:33.834399	Cleber	login
2024-11-26 11:16:23.236297	Andr├® W├╝st Zibetti	login
2024-11-26 11:17:46.250932	Andr├® W├╝st Zibetti	login
2024-11-26 11:17:58.553438	Andr├® W├╝st Zibetti	login
2024-11-27 14:40:36.035296	Cleber	login
2024-11-27 14:40:40.600318	Cleber	login
2024-11-27 14:40:43.445877	Cleber	login
2024-11-27 14:40:44.381832	Cleber	login
2024-11-27 14:40:49.696943	Cleber	login
2024-11-27 14:40:53.045069	Cleber	login
2024-11-27 14:40:55.294892	Cleber	login
2024-11-27 14:40:58.390974	Cleber	login
2024-11-27 14:41:00.399607	Cleber	login
2024-11-27 14:41:02.658984	Cleber	login
2024-11-27 14:41:06.827075	Cleber	login
2024-11-27 14:41:08.72666	Cleber	login
2024-11-27 14:41:10.4505	Cleber	login
2024-11-27 14:41:13.691147	Cleber	login
2024-11-27 14:41:18.252122	Cleber	login
2024-11-27 14:41:19.568422	Cleber	login
2024-11-27 14:41:23.24354	Cleber	login
2024-11-27 14:41:28.140076	Cleber	login
2024-11-27 14:41:29.776686	Cleber	login
2024-11-27 14:41:32.731262	Cleber	login
2024-11-27 14:41:35.499817	Cleber	login
2024-11-27 14:41:37.093526	Cleber	login
2024-11-27 14:41:39.26381	Cleber	login
2024-11-27 14:41:40.567744	Cleber	login
2024-11-27 14:41:43.973334	Cleber	login
2024-11-27 14:41:45.602172	Cleber	login
2024-11-27 14:41:47.485346	Cleber	login
2024-11-27 14:41:49.195184	Cleber	login
2024-11-27 14:41:58.640614	Cleber	login
2024-11-27 14:41:59.91696	Cleber	login
2024-11-27 14:42:01.663872	Cleber	login
2024-11-27 14:42:03.342837	Cleber	login
2024-11-27 14:42:06.289539	Cleber	login
2024-11-27 14:42:07.471667	Cleber	login
2024-11-27 14:42:09.673642	Cleber	login
2024-11-27 14:42:10.808059	Cleber	login
2024-11-27 14:42:14.191114	Cleber	login
2024-11-27 14:42:15.587276	Cleber	login
2024-11-27 14:42:16.6825	Cleber	login
2024-11-27 14:42:18.071777	Cleber	login
2024-11-27 14:42:20.180338	Cleber	login
2024-11-27 14:42:22.38604	Cleber	login
2024-11-27 14:42:24.330468	Cleber	login
2024-11-27 14:42:25.853139	Cleber	login
2024-11-27 14:42:28.161083	Cleber	login
2024-11-27 14:42:29.80033	Cleber	login
2024-11-27 14:42:31.212656	Cleber	login
2024-11-27 14:42:33.531716	Cleber	login
2024-11-27 14:42:35.953343	Cleber	login
2024-11-27 14:42:38.056878	Cleber	login
2024-11-27 14:42:39.922771	Cleber	login
2024-11-27 14:42:41.95743	Cleber	login
2024-11-27 14:42:45.226133	Cleber	login
2024-11-27 14:42:46.705084	Cleber	login
2024-11-27 14:42:48.456903	Cleber	login
2024-11-27 14:42:51.54009	Cleber	login
2024-11-27 14:42:54.653042	Cleber	login
2024-11-27 14:42:56.439709	Cleber	login
2024-11-27 14:42:59.653768	Cleber	login
2024-11-27 14:43:00.784472	Cleber	login
2024-11-27 14:43:09.589808	Cleber	login
2024-11-27 14:43:11.812527	Cleber	login
2024-11-27 14:43:13.962906	Cleber	login
2024-11-27 14:43:16.469423	Cleber	login
2024-11-27 14:43:21.638908	Cleber	login
2024-11-27 14:43:24.48939	Cleber	login
2024-11-27 14:43:26.872357	Cleber	login
2024-11-27 14:43:29.506525	Cleber	login
2024-11-27 14:43:33.797724	Cleber	login
2024-11-27 14:43:35.141764	Cleber	login
2024-11-27 14:43:37.954306	Cleber	login
2024-11-27 14:43:39.752412	Cleber	login
2024-11-27 14:43:44.545805	Cleber	login
2024-11-27 14:43:46.436018	Cleber	login
2024-11-27 14:43:48.364253	Cleber	login
2024-11-27 14:43:50.694267	Cleber	login
2024-11-27 14:43:57.047372	Cleber	login
2024-11-27 14:43:58.259768	Cleber	login
2024-11-27 14:44:00.930882	Cleber	login
2024-11-27 14:44:02.23881	Cleber	login
2024-11-27 14:44:06.034	Cleber	login
2024-11-27 14:44:09.057375	Cleber	login
2024-11-27 14:44:10.535056	Cleber	login
2024-11-27 14:44:11.983101	Cleber	login
2024-11-27 14:44:15.450066	Cleber	login
2024-11-27 14:44:18.108624	Cleber	login
2024-11-27 14:44:19.620169	Cleber	login
2024-11-27 14:44:21.209373	Cleber	login
2024-11-27 14:44:26.218024	Cleber	login
2024-12-02 03:41:17.35373	Cleber	login
2025-02-24 17:35:26.641503	Myllena	login
2025-02-24 17:35:26.686986	Myllena	login
2025-02-24 17:35:26.748228	Myllena	login
2025-02-24 17:35:35.610522	Myllena	login
2025-02-24 17:35:36.281763	Myllena	login
2025-02-24 17:35:38.021622	Myllena	login
2025-02-24 17:35:38.049361	Myllena	login
2025-02-24 17:35:38.105759	Myllena	login
2024-12-04 03:00:09.969015	Cleber	login
2024-12-04 03:00:23.182451	Cleber	login
2024-11-05 17:02:36.529432	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:48:02.66648	Felipe	login
2024-11-05 17:07:38.32608	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:39.467088	Jos├® Eduardo Medeiros Jochem	login
2024-12-10 13:08:00.828504	M├írcio Castro	login
2024-12-10 13:08:52.368379	M├írcio Castro	login
2024-11-08 19:49:45.134196	Felipe	login
2024-12-10 13:11:14.57491	Jonata Tyska	login
2024-11-05 17:15:38.439561	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:21:32.888031	Felipe	login
2024-11-05 17:21:38.589227	Felipe	login
2024-11-05 17:21:42.377397	Felipe	login
2024-11-05 17:21:42.377397	Felipe	login
2024-11-05 17:21:47.620474	Felipe	login
2024-11-05 17:21:47.620474	Felipe	login
2024-11-05 17:21:47.620474	Felipe	login
2024-11-05 17:22:16.863065	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:22:16.863065	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:22:38.183513	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:22:38.183513	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:22:38.183513	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:23:31.444436	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:23:31.444436	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:23:31.62228	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:23:55.362331	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:24:42.912851	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:44:28.306072	Cleber	login
2024-11-19 20:50:04.570588	Andr├® Teixeira Milioli	login
2024-11-19 20:50:47.840224	Andr├® Teixeira Milioli	login
2024-11-27 14:44:29.724848	Cleber	login
2024-11-19 20:52:36.57159	Andr├® Teixeira Milioli	login
2024-11-19 20:53:50.462228	Andr├® Teixeira Milioli	login
2024-11-19 20:54:20.092801	Andr├® Teixeira Milioli	login
2024-11-27 14:44:31.391038	Cleber	login
2024-11-27 14:44:33.45701	Cleber	login
2024-11-27 14:44:36.26454	Cleber	login
2024-11-27 14:44:38.158869	Cleber	login
2024-11-27 14:44:39.780797	Cleber	login
2024-11-25 06:44:51.825821	Cleber	login
2024-11-25 06:45:08.491096	Cleber	login
2024-11-25 06:45:50.022525	Cleber	login
2024-11-25 06:47:35.045643	Cleber	login
2024-11-25 06:51:33.350363	Cleber	login
2024-11-27 14:44:41.975833	Cleber	login
2024-11-26 13:26:05.406624	Jonata Tyska	login
2024-11-26 13:26:50.442323	Jonata Tyska	login
2024-11-27 14:44:43.68032	Cleber	login
2024-11-27 14:44:45.620619	Cleber	login
2024-11-27 14:44:50.684069	Cleber	login
2024-11-27 14:44:52.202081	Cleber	login
2024-11-27 14:44:54.347695	Cleber	login
2024-11-27 14:44:56.759891	Cleber	login
2024-11-27 14:44:58.857911	Cleber	login
2024-11-27 14:45:00.795205	Cleber	login
2024-11-27 14:45:03.335698	Cleber	login
2024-11-27 14:45:05.430399	Cleber	login
2024-11-27 14:45:08.452889	Cleber	login
2024-11-27 14:45:11.7377	Cleber	login
2024-11-27 14:45:14.949856	Cleber	login
2024-11-27 14:45:17.757009	Cleber	login
2024-11-27 14:45:21.555863	Cleber	login
2024-11-27 14:45:23.365013	Cleber	login
2024-11-27 14:45:26.177614	Cleber	login
2024-11-27 14:45:30.670085	Cleber	login
2024-11-27 14:45:33.058331	Cleber	login
2024-11-27 14:45:35.66944	Cleber	login
2024-11-27 14:45:38.86493	Cleber	login
2024-11-27 14:45:41.303541	Cleber	login
2024-11-27 14:45:44.702259	Cleber	login
2024-11-27 14:45:47.500444	Cleber	login
2024-11-27 14:45:50.265353	Cleber	login
2024-11-27 14:45:53.064017	Cleber	login
2024-11-27 14:45:55.67286	Cleber	login
2024-11-27 14:45:58.312436	Cleber	login
2024-11-27 14:46:01.5422	Cleber	login
2024-11-27 14:46:04.678188	Cleber	login
2024-11-27 14:46:06.905244	Cleber	login
2024-11-27 14:46:10.200709	Cleber	login
2024-11-27 14:46:14.298744	Cleber	login
2024-11-27 14:46:18.083695	Cleber	login
2024-11-27 14:46:20.690824	Cleber	login
2024-11-27 14:46:23.76314	Cleber	login
2024-11-27 14:46:26.65961	Cleber	login
2024-11-27 14:46:30.175682	Cleber	login
2024-11-27 14:46:53.57348	Cleber	login
2024-11-27 14:46:55.811148	Cleber	login
2024-11-27 14:46:57.893631	Cleber	login
2024-11-27 14:47:00.512156	Cleber	login
2024-11-27 14:47:03.427633	Cleber	login
2024-11-27 14:47:05.802908	Cleber	login
2024-11-27 14:47:09.519818	Cleber	login
2024-11-27 14:47:30.88692	Cleber	login
2024-11-27 14:47:35.515825	Cleber	login
2024-11-27 14:47:37.59022	Cleber	login
2024-11-27 14:47:40.976956	Cleber	login
2024-11-27 14:48:07.489273	Cleber	login
2024-11-27 14:48:10.760665	Cleber	login
2024-11-27 14:48:13.843649	Cleber	login
2024-11-27 14:48:16.792033	Cleber	login
2024-11-27 14:48:20.222341	Cleber	login
2024-11-27 14:48:24.283623	Cleber	login
2024-11-27 14:48:27.282448	Cleber	login
2024-11-27 14:48:30.011713	Cleber	login
2024-11-27 14:48:32.721384	Cleber	login
2024-11-27 14:48:35.413386	Cleber	login
2024-11-27 14:48:41.269773	Cleber	login
2024-11-27 14:48:44.130696	Cleber	login
2024-11-27 14:48:49.030127	Cleber	login
2024-11-27 14:48:51.387292	Cleber	login
2024-11-27 14:48:54.237523	Cleber	login
2024-11-27 14:48:57.485829	Cleber	login
2024-11-27 14:49:00.151153	Cleber	login
2024-11-27 14:49:04.163293	Cleber	login
2024-11-27 14:49:07.736753	Cleber	login
2024-11-27 14:49:10.318	Cleber	login
2024-11-27 14:49:12.701845	Cleber	login
2024-11-27 14:49:15.973031	Cleber	login
2024-11-27 14:49:18.782051	Cleber	login
2024-11-27 14:49:21.786182	Cleber	login
2024-11-27 14:49:24.762486	Cleber	login
2024-11-27 14:49:28.333424	Cleber	login
2024-11-27 14:49:31.232739	Cleber	login
2024-11-27 14:49:34.779607	Cleber	login
2024-11-27 14:49:39.550773	Cleber	login
2024-11-27 14:49:41.769146	Cleber	login
2024-11-27 14:49:44.476231	Cleber	login
2024-11-27 14:49:47.489934	Cleber	login
2024-11-27 14:49:50.647274	Cleber	login
2024-11-27 14:49:53.717275	Cleber	login
2024-11-27 14:49:56.676115	Cleber	login
2024-11-27 14:49:59.718088	Cleber	login
2024-11-27 14:50:02.841386	Cleber	login
2024-11-27 14:50:05.793612	Cleber	login
2024-11-27 14:50:08.911884	Cleber	login
2024-11-27 14:50:12.714514	Cleber	login
2024-11-27 14:50:16.182958	Cleber	login
2024-11-27 14:50:19.941503	Cleber	login
2024-11-27 14:50:22.729209	Cleber	login
2024-11-27 14:50:26.333869	Cleber	login
2024-11-27 14:50:29.575613	Cleber	login
2024-11-27 14:50:32.653785	Cleber	login
2024-11-27 14:50:35.826756	Cleber	login
2024-11-27 14:50:39.498429	Cleber	login
2024-11-27 14:50:43.119197	Cleber	login
2024-11-27 14:50:45.844448	Cleber	login
2024-11-27 14:50:49.319396	Cleber	login
2024-11-27 14:50:52.977726	Cleber	login
2024-11-27 14:50:56.281623	Cleber	login
2024-11-27 14:50:59.548083	Cleber	login
2024-11-27 14:51:02.831645	Cleber	login
2024-11-27 14:51:06.082348	Cleber	login
2024-11-27 14:51:11.544127	Cleber	login
2024-11-27 14:51:14.018956	Cleber	login
2024-11-27 14:51:17.617359	Cleber	login
2024-11-27 14:51:21.091668	Cleber	login
2024-11-27 14:51:23.95817	Cleber	login
2024-11-27 14:51:27.342904	Cleber	login
2024-11-27 14:51:31.11162	Cleber	login
2024-11-27 14:51:34.839225	Cleber	login
2024-11-27 14:51:38.698996	Cleber	login
2024-11-27 14:51:41.282703	Cleber	login
2024-11-27 14:51:44.699334	Cleber	login
2024-11-27 14:51:48.060685	Cleber	login
2024-11-27 14:51:51.991408	Cleber	login
2024-11-27 14:51:55.492424	Cleber	login
2024-11-27 14:51:58.907532	Cleber	login
2024-11-27 14:52:02.503675	Cleber	login
2024-11-27 14:52:06.145097	Cleber	login
2024-11-27 14:52:09.682043	Cleber	login
2024-11-27 14:52:13.81954	Cleber	login
2024-11-27 14:52:17.041479	Cleber	login
2024-11-27 14:52:25.8478	Cleber	login
2024-11-27 14:52:29.659744	Cleber	login
2024-11-27 14:52:33.480317	Cleber	login
2024-11-27 14:52:37.180354	Cleber	login
2024-11-27 14:52:40.608376	Cleber	login
2024-11-27 14:52:44.935303	Cleber	login
2024-11-27 14:52:47.967651	Cleber	login
2024-11-27 14:52:51.315661	Cleber	login
2024-11-27 14:52:54.932704	Cleber	login
2024-11-27 14:52:58.794025	Cleber	login
2024-11-19 20:49:31.087224	Andr├® Teixeira Milioli	login
2024-11-27 14:53:02.234713	Cleber	login
2024-11-25 06:45:01.729814	Cleber	login
2024-11-19 20:52:15.266721	Andr├® Teixeira Milioli	login
2024-11-19 20:53:04.099649	Andr├® Teixeira Milioli	login
2024-11-27 14:53:21.627351	Cleber	login
2024-11-25 06:45:13.022385	Cleber	login
2024-11-27 14:53:45.575732	Cleber	login
2024-11-25 06:47:43.254341	Cleber	login
2024-11-27 14:54:19.461919	Cleber	login
2024-11-26 13:25:29.913751	Jonata Tyska	login
2024-11-27 14:54:53.419706	Cleber	login
2024-11-26 13:26:24.841955	Jonata Tyska	login
2024-11-27 14:55:44.471436	Cleber	login
2024-11-26 13:33:03.770057	Jonata Tyska	login
2024-11-27 14:56:19.889313	Cleber	login
2024-11-27 14:56:49.821224	Cleber	login
2024-11-27 14:57:20.222456	Cleber	login
2024-11-27 14:57:57.08849	Cleber	login
2024-11-26 14:11:36.895884	Felipe	login
2024-11-27 14:58:28.736755	Cleber	login
2024-11-27 14:59:01.280973	Cleber	login
2024-11-27 14:59:33.733062	Cleber	login
2024-11-27 15:00:07.04224	Cleber	login
2024-11-27 15:00:36.232681	Cleber	login
2024-11-26 15:44:34.464165	Felipe	login
2024-11-27 15:01:07.44754	Cleber	login
2025-02-23 18:32:07.53848	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:08.444644	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:15.35706	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:25.728387	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:26.050633	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:29.776146	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:30.098036	Andr├® W├╝st Zibetti	login
2024-12-03 02:13:04.521038	Cleber	login
2024-12-03 02:13:46.876611	Cleber	login
2024-12-03 02:14:04.040348	Cleber	login
2024-12-03 02:14:20.75727	Cleber	login
2024-12-03 02:14:27.012364	Cleber	login
2024-12-03 02:15:22.64131	Cleber	login
2024-12-03 02:15:46.076516	Cleber	login
2024-12-03 02:15:58.165949	Cleber	login
2024-12-03 02:16:17.341646	Cleber	login
2024-12-03 02:16:31.392314	Cleber	login
2025-02-23 18:32:42.63676	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:46.387712	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:51.997679	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:52.314497	Andr├® W├╝st Zibetti	login
2025-02-23 18:33:19.456111	Andr├® W├╝st Zibetti	login
2025-02-23 18:33:19.787955	Andr├® W├╝st Zibetti	login
2025-02-23 18:42:37.126874	Andr├® W├╝st Zibetti	login
2024-12-03 12:22:10.836835	Jonata Tyska	login
2024-12-03 12:23:35.41525	Jonata Tyska	login
2025-02-23 18:42:39.050715	Andr├® W├╝st Zibetti	login
2025-02-23 18:50:11.888983	Andr├® W├╝st Zibetti	login
2025-02-23 18:50:11.948957	Andr├® W├╝st Zibetti	login
2025-02-23 18:50:11.984871	Andr├® W├╝st Zibetti	login
2024-11-05 17:24:43.179366	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:24:43.179366	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:24:43.179366	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:24:43.96432	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:25:37.831041	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:25:59.58817	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:25:59.58817	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:26:00.490083	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:47.768402	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:47.768402	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:47.768402	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:48.982685	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:48.982685	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:56:10.165787	Felipe	login
2024-11-05 17:28:56.208824	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:57.68875	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:58.872682	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:58.872682	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:00.849	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:01.216016	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:02.51878	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:19.949741	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:19.949741	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:20.936234	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:20.936234	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:54.446718	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:54.446718	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:54.446718	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:54.446718	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:25.54759	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:26.104379	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:29.159851	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:32.959456	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:36.42581	Felipe	login
2024-11-05 17:30:51.169186	Felipe	login
2024-11-05 17:30:58.696086	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:58.696086	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:01.137937	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:01.137937	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:01.137937	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:03.684658	Felipe	login
2024-11-05 17:31:03.684658	Felipe	login
2024-11-05 17:31:04.644801	Felipe	login
2024-11-05 17:31:04.669746	Felipe	login
2024-11-05 17:31:11.104275	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:11.104275	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:56:53.426477	Felipe	login
2024-11-05 17:31:11.13129	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:11.13129	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:11.13129	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:35:41.457365	Jos├® Eduardo Medeiros Jochem	login
2024-12-18 13:42:12.20479	Matheus Machado dos Santos	login
2024-11-05 17:38:03.547316	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:38:03.586609	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:38:52.17428	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:42:39.30519	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:42:39.338303	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:45:07.391002	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:46:22.298482	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:46:22.333778	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:46:47.201349	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:46:47.201349	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:48:02.675575	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:54:52.594322	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:53:06.199784	Cleber	login
2024-11-19 20:50:05.834	Andr├® Teixeira Milioli	login
2024-11-19 20:50:48.347934	Andr├® Teixeira Milioli	login
2024-11-27 14:53:09.94799	Cleber	login
2024-11-19 20:52:37.636426	Andr├® Teixeira Milioli	login
2024-11-27 14:53:13.972082	Cleber	login
2024-11-20 22:44:51.460303	Matheus Machado dos Santos	login
2024-11-27 14:53:17.671082	Cleber	login
2024-11-27 14:53:25.538975	Cleber	login
2024-11-21 14:19:27.438069	Andr├® W├╝st Zibetti	login
2024-11-27 14:53:30.040693	Cleber	login
2024-11-21 14:19:31.094297	Andr├® W├╝st Zibetti	login
2024-11-27 14:53:35.967442	Cleber	login
2024-11-27 14:53:42.237118	Cleber	login
2024-11-21 15:13:00.750424	Felipe	login
2024-11-27 14:53:54.754967	Cleber	login
2024-11-21 15:13:04.358008	Felipe	login
2024-11-27 14:54:00.776165	Cleber	login
2024-11-21 15:13:21.850655	Felipe	login
2024-11-21 15:13:21.850655	Felipe	login
2024-11-21 15:13:21.850655	Felipe	login
2024-11-21 15:14:04.102798	Felipe	login
2024-11-21 15:14:04.102798	Felipe	login
2024-11-21 15:14:48.185255	Felipe	login
2024-11-21 15:14:48.257858	Felipe	login
2024-11-21 15:14:49.728223	Felipe	login
2024-11-21 15:16:51.244319	Felipe	login
2024-11-21 15:16:51.244319	Felipe	login
2024-11-25 18:36:18.281868	Andr├® Teixeira Milioli	login
2024-11-21 17:40:14.625317	Andr├® W├╝st Zibetti	login
2024-11-25 18:37:29.657235	Andr├® Teixeira Milioli	login
2024-11-21 17:40:18.335498	Andr├® W├╝st Zibetti	login
2024-11-27 14:54:06.902778	Cleber	login
2024-11-21 17:40:20.207138	Andr├® W├╝st Zibetti	login
2024-11-21 17:40:35.7488	Andr├® W├╝st Zibetti	login
2024-11-21 17:40:37.028479	Andr├® W├╝st Zibetti	login
2024-11-21 17:40:41.726394	Andr├® W├╝st Zibetti	login
2024-11-21 17:40:43.532911	Andr├® W├╝st Zibetti	login
2024-11-25 18:38:07.705627	Andr├® Teixeira Milioli	login
2024-11-21 17:40:52.693579	Luis	login
2024-11-25 18:38:45.530133	Andr├® Teixeira Milioli	login
2024-11-21 17:40:53.615271	Luis	login
2024-11-27 14:54:13.72198	Cleber	login
2024-11-21 17:40:55.824291	Luis	login
2024-11-21 17:40:55.824291	Luis	login
2024-11-21 17:40:55.87183	Luis	login
2024-11-21 17:40:57.585336	Luis	login
2024-11-21 17:41:01.962188	Luis	login
2024-11-21 17:41:01.969278	Luis	login
2024-11-21 17:55:53.651583	Luis	login
2024-11-27 14:54:25.783612	Cleber	login
2024-11-21 17:55:57.19946	Luis	login
2024-11-26 13:26:06.600181	Jonata Tyska	login
2024-11-21 17:56:00.211308	Luis	login
2024-11-21 17:56:00.211308	Luis	login
2024-11-21 17:56:09.22413	Luis	login
2024-11-26 13:26:51.498998	Jonata Tyska	login
2024-11-21 18:26:30.707655	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:54:34.025508	Cleber	login
2024-11-21 18:26:32.357884	Jos├® Eduardo Medeiros Jochem	login
2024-11-26 14:12:33.955583	Felipe	login
2024-11-21 18:26:35.338574	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:54:40.436154	Cleber	login
2024-11-21 18:26:38.752219	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:26:38.752219	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:26:38.752219	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:14.713068	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:18.512834	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:18.512834	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:34.363715	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:34.384235	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:37.279443	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:37.300891	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:51.117725	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:51.132733	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:28:05.68621	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:54:46.347149	Cleber	login
2024-11-21 18:28:06.543079	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:55:17.84806	Cleber	login
2024-11-21 18:30:21.201765	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:55:26.546293	Cleber	login
2024-11-21 18:30:22.098084	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:55:33.678113	Cleber	login
2024-11-21 18:31:28.956642	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:31:28.976293	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:31:48.267719	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:55:38.940997	Cleber	login
2024-11-21 18:31:49.139139	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:55:50.412636	Cleber	login
2024-11-21 18:31:50.995057	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:31:51.007291	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:31:51.007291	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:31:51.007291	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:38:52.652981	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:55:57.123161	Cleber	login
2024-11-21 18:38:56.280844	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:56:06.031926	Cleber	login
2024-11-21 18:38:58.737068	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:38:58.747633	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:38:58.757853	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:43:38.008903	Luis	login
2024-11-27 14:56:12.274745	Cleber	login
2024-11-21 18:43:38.799284	Luis	login
2024-11-27 14:56:25.940352	Cleber	login
2024-11-21 18:43:40.200608	Luis	login
2024-11-21 18:43:40.200608	Luis	login
2024-11-21 18:43:40.200608	Luis	login
2024-11-21 18:47:46.294189	Luis	login
2024-11-21 18:47:47.719072	Luis	login
2024-11-21 18:47:59.203047	Luis	login
2024-11-27 14:56:31.628669	Cleber	login
2024-11-21 18:47:59.850314	Luis	login
2024-11-27 14:56:37.76601	Cleber	login
2024-11-21 18:48:01.828186	Luis	login
2024-11-21 18:48:01.828186	Luis	login
2024-11-21 18:48:01.842947	Luis	login
2024-11-21 18:48:03.023719	Luis	login
2024-11-21 18:48:07.997623	Luis	login
2024-11-27 14:56:43.808638	Cleber	login
2024-11-21 18:48:08.526411	Luis	login
2024-11-27 14:56:55.5433	Cleber	login
2024-11-21 18:48:09.893063	Luis	login
2024-11-27 14:57:01.172865	Cleber	login
2024-11-27 14:57:06.945777	Cleber	login
2024-11-27 14:57:14.538474	Cleber	login
2024-11-27 14:57:25.85996	Cleber	login
2024-11-27 14:57:33.980471	Cleber	login
2024-11-27 14:57:40.232807	Cleber	login
2024-11-27 14:57:46.701524	Cleber	login
2024-11-27 14:58:03.187842	Cleber	login
2024-11-27 14:58:09.985889	Cleber	login
2024-11-27 14:58:15.982098	Cleber	login
2024-11-27 14:58:22.575963	Cleber	login
2024-11-27 14:58:35.03617	Cleber	login
2024-11-27 14:58:44.130898	Cleber	login
2024-11-27 14:58:49.760739	Cleber	login
2024-11-21 18:48:09.893063	Luis	login
2024-11-21 18:49:29.578875	Luis	login
2024-11-27 14:58:55.57012	Cleber	login
2024-11-21 18:49:53.622139	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:50:07.08271	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:57:56.996604	Luis	login
2024-11-21 18:57:56.996604	Luis	login
2024-11-21 18:58:18.669884	Luis	login
2024-11-27 14:59:27.308605	Cleber	login
2024-11-21 18:58:33.566416	Luis	login
2024-11-21 18:58:37.050972	Luis	login
2024-11-21 18:58:40.567498	Luis	login
2024-11-27 14:59:59.039388	Cleber	login
2024-11-27 15:00:29.822527	Cleber	login
2024-11-25 17:26:55.308439	Felipe	login
2024-11-27 15:01:01.431018	Cleber	login
2024-11-25 17:27:45.025607	Felipe	login
2024-11-25 18:36:07.191369	Andr├® Teixeira Milioli	login
2024-11-25 18:37:11.214704	Andr├® Teixeira Milioli	login
2024-11-25 18:37:47.518814	Andr├® Teixeira Milioli	login
2024-11-05 17:55:39.011488	Jos├® Eduardo Medeiros Jochem	login
2024-11-25 18:38:27.462326	Andr├® Teixeira Milioli	login
2024-11-26 13:25:34.266703	Jonata Tyska	login
2024-11-05 17:55:55.91066	Jos├® Eduardo Medeiros Jochem	login
2024-11-26 13:26:26.042603	Jonata Tyska	login
2024-11-05 18:00:12.023197	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:01:31.796793	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:22.253314	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:42.393484	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:57:46.026695	Felipe	login
2024-12-03 02:12:57.135351	Cleber	login
2024-12-03 02:13:59.080307	Cleber	login
2024-11-26 15:44:36.91679	Felipe	login
2024-12-03 02:13:59.080307	Cleber	login
2024-12-03 02:14:09.896633	Cleber	login
2024-12-03 02:14:34.281437	Cleber	login
2024-12-03 02:15:26.917281	Cleber	login
2024-12-03 02:15:50.57347	Cleber	login
2024-12-03 02:16:07.260762	Cleber	login
2024-12-03 02:16:20.948409	Cleber	login
2024-12-03 02:16:34.829465	Cleber	login
2024-11-11 11:21:44.245113	Cleber	login
2024-11-11 11:21:44.245113	Cleber	login
2024-11-13 20:31:22.47321	Jerusa Marchi	login
2024-12-03 12:21:56.5568	Jonata Tyska	login
2024-12-03 12:22:30.081426	Jonata Tyska	login
2024-11-04 20:12:05.892652	Matheus Machado dos Santos	login
2024-11-04 20:12:06.831994	Matheus Machado dos Santos	login
2024-12-05 20:35:28.355255	Andr├® Teixeira Milioli	login
2024-12-05 20:36:46.949611	Andr├® Teixeira Milioli	login
2024-12-05 20:37:28.570018	Andr├® Teixeira Milioli	login
2024-11-04 20:12:07.751314	Matheus Machado dos Santos	login
2024-11-04 20:12:08.616757	Matheus Machado dos Santos	login
2024-11-04 20:12:09.456478	Matheus Machado dos Santos	login
2024-11-04 20:12:10.490957	Matheus Machado dos Santos	login
2024-11-04 20:12:11.444042	Matheus Machado dos Santos	login
2024-12-04 02:58:39.965355	Cleber	login
2024-12-04 02:59:00.766145	Cleber	login
2024-12-04 02:59:13.92265	Cleber	login
2024-12-04 02:59:21.758541	Cleber	login
2024-12-04 02:59:31.038025	Cleber	login
2024-12-04 03:00:17.692209	Cleber	login
2024-11-04 20:12:12.367974	Matheus Machado dos Santos	login
2024-12-04 03:02:28.10475	Cleber	login
2024-11-04 20:12:13.3023	Matheus Machado dos Santos	login
2024-11-04 20:12:14.250897	Matheus Machado dos Santos	login
2024-11-04 20:12:15.228923	Matheus Machado dos Santos	login
2024-11-04 20:12:16.296055	Matheus Machado dos Santos	login
2024-11-08 17:27:40.262377	Felipe	login
2024-11-26 15:56:34.727787	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 17:27:49.297331	Felipe	login
2024-11-26 15:56:40.626538	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 17:29:27.95783	Felipe	login
2024-11-05 13:30:29.949669	Breno	login
2024-11-05 13:31:14.507699	Breno	login
2024-11-05 13:31:17.797468	Breno	login
2025-02-21 23:56:27.84425	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 20:29:21.790825	Felipe	login
2024-11-08 20:30:26.211641	Felipe	login
2025-02-23 18:04:15.230246	Andr├® W├╝st Zibetti	login
2024-11-13 20:29:18.354991	Jerusa Marchi	login
2024-11-13 20:31:12.998155	Jerusa Marchi	login
2024-11-05 14:20:29.942872	Breno	login
2024-11-05 14:20:32.366505	Breno	login
2024-11-05 14:20:35.720622	Breno	login
2024-11-05 14:20:36.404602	Breno	login
2024-11-05 14:20:44.000161	Breno	login
2024-11-05 14:20:44.011125	Breno	login
2024-11-05 14:21:46.406818	Breno	login
2024-11-05 14:22:50.049345	Breno	login
2024-11-05 14:22:50.049345	Breno	login
2024-11-05 14:23:06.88976	Breno	login
2025-02-23 18:04:17.706012	Andr├® W├╝st Zibetti	login
2024-11-05 14:23:18.204417	Breno	login
2024-11-05 14:23:18.204417	Breno	login
2024-11-05 17:01:59.435491	Jos├® Eduardo Medeiros Jochem	login
2024-11-13 20:31:22.487836	Jerusa Marchi	login
2024-11-13 20:31:27.268385	Jerusa Marchi	login
2024-11-05 17:02:36.155377	Jos├® Eduardo Medeiros Jochem	login
2024-11-13 20:31:36.088391	Jerusa Marchi	login
2024-11-05 17:07:33.738388	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:40.37617	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:08.883225	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:15.383864	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:15.383864	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:15.383864	Jos├® Eduardo Medeiros Jochem	login
2024-11-13 20:31:37.792003	Jerusa Marchi	login
2024-11-05 17:22:38.199231	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:23:55.768981	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:24:42.922809	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:26:00.518086	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:47.982237	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:28:47.982237	Jos├® Eduardo Medeiros Jochem	login
2024-11-13 20:31:58.084834	Jerusa Marchi	login
2024-11-05 17:29:02.527872	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:02.527872	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:29:02.527872	Jos├® Eduardo Medeiros Jochem	login
2024-11-13 20:32:57.282005	Jerusa Marchi	login
2024-11-13 20:33:19.578606	Jerusa Marchi	login
2024-11-05 17:30:29.171205	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:29.171205	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:29.171205	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:32.979826	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:32.979826	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:50.422421	Felipe	login
2024-11-05 17:30:58.684225	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:58.684225	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:30:58.763648	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:48:09.911811	Luis	login
2024-11-21 18:48:11.20379	Luis	login
2024-11-21 18:48:33.335446	Luis	login
2024-11-21 18:48:33.335446	Luis	login
2024-11-21 18:48:33.335446	Luis	login
2024-11-21 18:49:30.154643	Luis	login
2024-11-27 14:59:08.850625	Cleber	login
2024-11-21 18:49:59.479879	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:49:59.479879	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:49:59.479879	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:49:59.479879	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:58:32.324406	Luis	login
2024-11-21 18:58:37.86409	Luis	login
2024-11-21 18:58:48.656066	Luis	login
2024-11-27 14:59:15.916657	Cleber	login
2024-11-27 14:59:21.48614	Cleber	login
2024-11-27 14:59:39.340984	Cleber	login
2024-11-25 17:27:02.124659	Felipe	login
2024-11-27 14:59:45.638366	Cleber	login
2024-11-25 18:36:18.681322	Andr├® Teixeira Milioli	login
2024-11-25 18:37:37.073963	Andr├® Teixeira Milioli	login
2024-11-27 14:59:53.158602	Cleber	login
2024-11-25 18:38:08.089662	Andr├® Teixeira Milioli	login
2024-11-25 18:38:50.621107	Andr├® Teixeira Milioli	login
2024-11-27 15:00:12.36179	Cleber	login
2024-11-26 13:26:09.654374	Jonata Tyska	login
2024-11-26 13:33:02.695508	Jonata Tyska	login
2024-11-27 15:00:19.367615	Cleber	login
2024-11-27 15:00:24.187956	Cleber	login
2024-11-27 15:00:42.847856	Cleber	login
2024-11-27 15:00:48.742099	Cleber	login
2024-11-27 15:00:54.022149	Cleber	login
2024-11-27 15:01:13.184461	Cleber	login
2024-11-27 15:01:20.235319	Cleber	login
2024-11-27 15:01:26.133993	Cleber	login
2024-11-27 15:01:32.209802	Cleber	login
2024-11-27 15:01:38.163997	Cleber	login
2024-11-27 15:01:44.77633	Cleber	login
2024-11-27 15:01:51.738927	Cleber	login
2024-11-27 15:01:58.584853	Cleber	login
2024-11-27 15:02:06.735742	Cleber	login
2024-11-27 15:02:13.201639	Cleber	login
2024-11-27 15:02:18.906674	Cleber	login
2024-11-27 15:02:27.078206	Cleber	login
2024-11-27 15:02:34.148427	Cleber	login
2024-11-27 15:02:37.367616	Cleber	login
2024-11-27 15:02:42.808709	Cleber	login
2024-11-27 15:02:48.472073	Cleber	login
2024-11-27 15:02:54.071881	Cleber	login
2024-11-27 15:02:59.709164	Cleber	login
2024-11-27 15:03:05.129745	Cleber	login
2024-11-27 15:03:10.73092	Cleber	login
2024-11-27 15:03:17.087388	Cleber	login
2024-11-27 15:03:23.522356	Cleber	login
2024-11-27 15:03:28.058259	Cleber	login
2024-11-27 15:03:35.459519	Cleber	login
2024-11-27 15:03:41.598942	Cleber	login
2024-11-27 15:03:48.846089	Cleber	login
2024-11-27 15:03:54.724135	Cleber	login
2024-11-27 15:04:00.587151	Cleber	login
2024-11-27 15:04:05.007446	Cleber	login
2024-11-27 15:04:10.860812	Cleber	login
2024-11-27 15:04:17.135846	Cleber	login
2024-11-27 15:04:21.4147	Cleber	login
2024-11-27 15:04:27.356148	Cleber	login
2024-11-27 15:04:34.148662	Cleber	login
2024-11-27 15:04:40.732287	Cleber	login
2024-11-27 15:04:44.826723	Cleber	login
2024-11-27 15:04:51.147961	Cleber	login
2024-11-27 15:04:55.555042	Cleber	login
2024-11-27 15:05:01.32128	Cleber	login
2024-11-27 15:05:08.872996	Cleber	login
2024-11-27 15:05:14.79708	Cleber	login
2024-11-27 15:05:22.190371	Cleber	login
2024-11-27 15:05:29.449786	Cleber	login
2024-11-27 15:05:33.99554	Cleber	login
2024-11-27 15:05:40.096504	Cleber	login
2024-11-27 15:05:46.37041	Cleber	login
2024-11-27 15:05:54.87964	Cleber	login
2024-11-27 15:06:02.231346	Cleber	login
2024-11-27 15:06:08.623831	Cleber	login
2024-11-27 15:06:14.440614	Cleber	login
2024-11-27 15:06:20.736037	Cleber	login
2024-11-27 15:06:27.593787	Cleber	login
2024-11-27 15:06:34.306619	Cleber	login
2024-11-27 15:06:40.044663	Cleber	login
2024-11-27 15:06:46.803454	Cleber	login
2024-11-27 15:06:52.774764	Cleber	login
2024-11-27 15:06:59.330717	Cleber	login
2024-11-27 15:07:06.747299	Cleber	login
2024-11-27 15:07:18.550299	Cleber	login
2024-11-27 15:07:26.386875	Cleber	login
2024-11-27 15:07:32.368608	Cleber	login
2024-11-27 15:07:38.224459	Cleber	login
2024-11-27 15:07:42.787638	Cleber	login
2024-11-27 15:07:48.661476	Cleber	login
2024-11-27 15:07:54.51319	Cleber	login
2024-11-27 15:08:02.438785	Cleber	login
2024-11-27 15:08:08.693368	Cleber	login
2024-11-27 15:08:14.908366	Cleber	login
2024-11-27 15:08:21.017809	Cleber	login
2024-11-27 15:08:26.881852	Cleber	login
2024-11-27 15:08:33.40261	Cleber	login
2024-11-27 15:08:40.277716	Cleber	login
2024-11-27 15:08:46.5661	Cleber	login
2024-11-27 15:08:53.529118	Cleber	login
2024-11-27 15:08:59.730996	Cleber	login
2024-11-27 15:09:04.212156	Cleber	login
2024-11-27 15:09:11.905307	Cleber	login
2024-11-27 15:09:17.905794	Cleber	login
2024-11-27 15:09:24.280088	Cleber	login
2024-11-27 15:09:35.653101	Cleber	login
2024-11-27 15:09:41.725794	Cleber	login
2024-11-27 15:09:48.087394	Cleber	login
2024-11-27 15:09:53.899819	Cleber	login
2024-11-27 15:09:59.688481	Cleber	login
2024-11-27 15:10:11.548078	Cleber	login
2024-11-27 15:10:17.963	Cleber	login
2024-11-27 15:10:24.194705	Cleber	login
2024-11-27 15:10:30.459802	Cleber	login
2024-11-27 15:10:37.562644	Cleber	login
2024-11-27 15:10:44.293743	Cleber	login
2024-11-27 15:10:50.258631	Cleber	login
2024-11-27 15:10:56.620338	Cleber	login
2024-11-27 15:11:02.721958	Cleber	login
2024-11-27 15:11:08.920229	Cleber	login
2024-11-27 15:11:14.943501	Cleber	login
2024-11-27 15:11:20.947359	Cleber	login
2024-11-27 15:11:26.852829	Cleber	login
2024-11-27 15:11:33.572956	Cleber	login
2024-11-27 15:11:40.682709	Cleber	login
2024-11-27 15:11:47.625656	Cleber	login
2024-11-27 15:11:53.579352	Cleber	login
2024-11-27 15:12:00.615198	Cleber	login
2024-11-27 15:12:06.734731	Cleber	login
2024-11-27 15:12:11.416667	Cleber	login
2024-11-27 15:12:18.131493	Cleber	login
2024-11-27 15:12:24.505137	Cleber	login
2024-11-27 15:12:30.46828	Cleber	login
2024-11-27 15:12:36.609055	Cleber	login
2024-11-27 15:12:42.894402	Cleber	login
2024-11-27 15:12:49.132999	Cleber	login
2024-11-27 15:12:53.810825	Cleber	login
2024-11-27 15:13:00.796998	Cleber	login
2024-11-27 15:13:07.827641	Cleber	login
2024-11-27 15:13:13.778815	Cleber	login
2024-11-27 15:13:19.687711	Cleber	login
2024-11-27 15:13:25.601218	Cleber	login
2024-11-27 15:13:31.89385	Cleber	login
2024-11-27 15:13:38.864221	Cleber	login
2024-11-27 15:13:44.887752	Cleber	login
2024-11-27 15:13:53.045134	Cleber	login
2024-11-27 15:13:59.606221	Cleber	login
2024-11-21 18:49:15.15967	Luis	login
2024-11-27 15:14:05.663693	Cleber	login
2024-11-21 18:49:53.05819	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 15:14:40.74424	Cleber	login
2024-11-21 18:50:07.06904	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:57:57.006416	Luis	login
2024-11-21 18:58:01.123756	Luis	login
2024-11-21 18:58:01.123756	Luis	login
2024-11-21 18:58:01.123756	Luis	login
2024-11-21 18:58:03.172836	Luis	login
2024-11-21 18:58:03.172836	Luis	login
2024-11-21 18:58:09.4774	Luis	login
2024-11-27 15:15:13.973994	Cleber	login
2024-11-21 18:58:12.510919	Luis	login
2024-11-27 15:15:45.007422	Cleber	login
2024-11-21 18:58:14.479436	Luis	login
2024-11-21 18:58:14.479436	Luis	login
2024-11-21 18:58:14.554694	Luis	login
2024-11-21 18:58:19.136865	Luis	login
2024-11-21 18:58:19.136865	Luis	login
2024-11-21 18:58:31.789445	Luis	login
2024-11-27 15:16:24.322457	Cleber	login
2024-11-21 18:58:33.524274	Luis	login
2024-11-21 18:58:33.524274	Luis	login
2024-11-21 18:58:35.014497	Luis	login
2024-11-21 18:58:40.550748	Luis	login
2024-11-21 18:58:40.550748	Luis	login
2024-11-21 18:58:40.59103	Luis	login
2024-11-21 18:58:48.744199	Luis	login
2024-11-21 18:58:50.377621	Luis	login
2024-11-21 18:58:54.316063	Luis	login
2024-11-27 15:17:01.473651	Cleber	login
2024-11-21 18:59:42.209868	Luis	login
2024-11-27 15:17:54.445991	Cleber	login
2024-11-21 18:59:42.809314	Luis	login
2024-11-25 17:26:57.538719	Felipe	login
2024-11-21 18:59:44.81954	Luis	login
2024-11-21 18:59:44.903987	Luis	login
2024-11-21 18:59:45.995898	Luis	login
2024-11-21 18:59:48.739285	Luis	login
2024-11-21 19:00:40.98951	Luis	login
2024-11-27 15:18:30.482863	Cleber	login
2024-11-21 19:00:41.517306	Luis	login
2024-11-25 17:28:13.869608	Felipe	login
2024-11-21 19:00:42.733034	Luis	login
2024-11-21 19:00:42.733034	Luis	login
2024-11-21 19:00:42.764144	Luis	login
2024-11-21 19:00:44.321798	Luis	login
2024-11-21 19:00:46.705369	Luis	login
2024-11-21 19:00:53.093133	Luis	login
2024-11-21 19:01:12.510607	Luis	login
2024-11-25 18:36:09.495953	Andr├® Teixeira Milioli	login
2024-11-21 19:01:13.037738	Luis	login
2024-11-27 15:19:04.751356	Cleber	login
2024-11-21 19:01:30.830269	Luis	login
2024-11-25 18:37:12.103952	Andr├® Teixeira Milioli	login
2024-11-21 19:01:31.363154	Luis	login
2024-11-27 15:19:39.89121	Cleber	login
2024-11-21 19:12:12.914805	Luis	login
2024-11-25 18:37:48.099541	Andr├® Teixeira Milioli	login
2024-11-21 19:12:15.888444	Luis	login
2024-11-27 15:20:12.824537	Cleber	login
2024-11-21 19:12:17.30589	Luis	login
2024-11-21 19:12:17.30589	Luis	login
2024-11-21 19:12:17.30589	Luis	login
2024-11-21 19:12:17.715149	Jos├® Eduardo Medeiros Jochem	login
2024-11-25 18:38:28.333435	Andr├® Teixeira Milioli	login
2024-11-21 19:12:18.278292	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 15:20:47.306016	Cleber	login
2024-11-21 19:12:20.145984	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:20.15715	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:20.166463	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:27.215122	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:27.215122	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:31.206007	Luis	login
2024-11-21 19:12:31.266985	Luis	login
2024-11-21 19:12:35.320127	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:35.320127	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:56.38966	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:56.404276	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:57.725316	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:57.738943	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:07.477929	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:07.490812	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:13.608963	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:13.620269	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:16.234817	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:16.246033	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:47.215194	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:47.226065	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:51.084502	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:51.095116	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:14:55.502638	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:14:55.520731	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:15:03.058698	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:15:03.069338	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:15:06.714262	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:15:06.726801	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:15:27.244913	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:15:27.257655	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:15:29.264883	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:15:29.276802	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:21:28.701129	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:21:28.701129	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:21:57.259658	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:21:57.278853	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:22:12.380836	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:22:12.405215	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:22:39.373397	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:22:39.40562	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:24:15.847515	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:24:15.881474	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:24:23.333664	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:24:23.366225	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 15:21:19.783745	Cleber	login
2024-11-22 16:30:27.919015	Felipe	login
2024-11-27 15:21:51.523902	Cleber	login
2024-11-22 16:30:30.153358	Felipe	login
2024-11-27 15:22:32.989773	Cleber	login
2024-11-22 16:30:34.132692	Felipe	login
2024-11-27 15:23:06.079335	Cleber	login
2024-11-22 16:30:34.747071	Felipe	login
2024-11-27 15:23:39.994053	Cleber	login
2024-11-22 16:30:41.814326	Felipe	login
2024-11-27 15:24:13.0471	Cleber	login
2024-11-22 16:30:42.555764	Felipe	login
2024-11-27 15:24:47.59602	Cleber	login
2024-11-22 16:32:36.332344	Felipe	login
2024-11-22 16:32:42.398487	Felipe	login
2024-11-27 15:25:23.354878	Cleber	login
2024-11-27 15:25:58.328266	Cleber	login
2024-11-27 15:26:32.925619	Cleber	login
2024-11-27 15:27:07.062487	Cleber	login
2024-11-27 15:27:42.444921	Cleber	login
2024-11-27 15:14:12.889279	Cleber	login
2024-11-22 16:38:24.387599	Felipe	login
2024-11-22 16:38:24.387599	Felipe	login
2024-11-27 15:14:20.57223	Cleber	login
2024-11-27 15:14:26.800988	Cleber	login
2024-11-27 15:14:32.929441	Cleber	login
2024-11-27 15:14:48.36246	Cleber	login
2024-11-27 15:14:54.965948	Cleber	login
2024-11-27 15:15:01.189778	Cleber	login
2024-11-27 15:15:07.682885	Cleber	login
2024-11-25 17:27:26.281332	Felipe	login
2024-11-25 17:27:26.281332	Felipe	login
2024-11-27 15:15:20.0893	Cleber	login
2024-11-25 18:36:57.043435	Andr├® Teixeira Milioli	login
2024-11-25 18:37:37.495653	Andr├® Teixeira Milioli	login
2024-11-27 15:15:26.070916	Cleber	login
2024-11-25 18:38:26.627673	Andr├® Teixeira Milioli	login
2024-11-25 18:38:51.057923	Andr├® Teixeira Milioli	login
2024-11-27 15:15:32.684789	Cleber	login
2024-11-27 15:15:38.99298	Cleber	login
2024-11-27 15:15:51.482292	Cleber	login
2024-11-27 15:15:58.080466	Cleber	login
2024-11-27 15:16:05.217998	Cleber	login
2024-11-27 15:16:18.284151	Cleber	login
2024-11-27 15:16:30.158793	Cleber	login
2024-11-27 15:16:36.381634	Cleber	login
2024-11-27 15:16:43.55866	Cleber	login
2024-11-26 15:44:49.634693	Felipe	consulta_licitacao
2024-11-26 15:45:02.651718	Felipe	consulta_licitacao
2024-11-27 15:16:50.655352	Cleber	login
2024-11-27 15:17:08.691398	Cleber	login
2024-11-27 15:17:14.839875	Cleber	login
2024-11-27 15:17:20.953181	Cleber	login
2024-11-27 15:17:30.09034	Cleber	login
2024-11-27 15:18:01.745533	Cleber	login
2024-11-27 15:18:09.286026	Cleber	login
2024-11-27 15:18:16.017297	Cleber	login
2024-11-27 15:18:23.176711	Cleber	login
2024-11-27 15:18:37.602819	Cleber	login
2024-11-27 15:18:45.412485	Cleber	login
2024-11-27 15:18:52.415952	Cleber	login
2024-11-27 15:18:58.584424	Cleber	login
2024-11-27 15:19:11.245882	Cleber	login
2024-11-27 15:19:17.676697	Cleber	login
2024-11-27 15:19:25.888078	Cleber	login
2024-11-27 15:19:33.708201	Cleber	login
2024-11-27 15:19:46.435217	Cleber	login
2024-11-27 15:19:53.023154	Cleber	login
2024-11-27 15:19:59.632789	Cleber	login
2024-11-27 15:20:06.234244	Cleber	login
2024-11-27 15:20:19.37576	Cleber	login
2024-11-27 15:20:27.724644	Cleber	login
2024-11-27 15:20:33.22196	Cleber	login
2024-11-27 15:20:40.562386	Cleber	login
2024-11-27 15:20:53.871903	Cleber	login
2024-11-27 15:21:00.538033	Cleber	login
2024-11-27 15:21:06.979968	Cleber	login
2024-11-27 15:21:13.273729	Cleber	login
2024-11-27 15:21:26.058264	Cleber	login
2024-11-27 15:21:32.744354	Cleber	login
2024-11-27 15:21:38.987127	Cleber	login
2024-11-27 15:21:45.297284	Cleber	login
2024-11-27 15:21:58.033396	Cleber	login
2024-11-27 15:22:04.253237	Cleber	login
2024-11-27 15:22:19.622943	Cleber	login
2024-11-27 15:22:26.60603	Cleber	login
2024-11-27 15:22:40.191284	Cleber	login
2024-11-27 15:22:46.815229	Cleber	login
2024-11-27 15:22:53.071352	Cleber	login
2024-11-27 15:22:59.628842	Cleber	login
2024-11-27 15:23:13.557722	Cleber	login
2024-11-27 15:23:20.144794	Cleber	login
2024-11-27 15:23:26.637287	Cleber	login
2024-11-27 15:23:33.043103	Cleber	login
2024-11-27 15:23:46.963808	Cleber	login
2024-11-27 15:23:53.747183	Cleber	login
2024-11-27 15:24:00.215396	Cleber	login
2024-11-27 15:24:06.465054	Cleber	login
2024-11-27 15:24:19.369165	Cleber	login
2024-11-27 15:24:25.66767	Cleber	login
2024-11-27 15:24:32.705084	Cleber	login
2024-11-27 15:24:39.630726	Cleber	login
2024-11-27 15:24:55.516098	Cleber	login
2024-11-27 15:25:02.44019	Cleber	login
2024-11-27 15:25:09.214148	Cleber	login
2024-11-27 15:25:16.335218	Cleber	login
2024-11-27 15:25:30.444714	Cleber	login
2024-11-27 15:25:36.816038	Cleber	login
2024-11-27 15:25:44.104628	Cleber	login
2024-11-27 15:25:51.213385	Cleber	login
2024-11-27 15:26:05.448618	Cleber	login
2024-11-27 15:26:12.444246	Cleber	login
2024-11-27 15:26:19.402149	Cleber	login
2024-11-27 15:26:26.035619	Cleber	login
2024-11-27 15:26:39.714001	Cleber	login
2024-11-27 15:26:46.483323	Cleber	login
2024-11-27 15:26:53.518467	Cleber	login
2024-11-27 15:27:01.451102	Cleber	login
2024-11-27 15:27:13.543616	Cleber	login
2024-11-27 15:27:20.5415	Cleber	login
2024-11-27 15:27:28.334944	Cleber	login
2024-11-27 15:27:34.963905	Cleber	login
2024-11-27 15:27:48.606837	Cleber	login
2024-11-27 15:27:56.107685	Cleber	login
2024-11-27 15:28:04.617804	Cleber	login
2024-11-27 15:28:11.420979	Cleber	login
2024-11-27 15:28:18.943694	Cleber	login
2024-11-27 15:28:25.01166	Cleber	login
2024-11-27 15:28:31.437272	Cleber	login
2024-11-27 15:28:38.180608	Cleber	login
2024-11-27 15:28:45.417826	Cleber	login
2024-11-27 15:28:52.45914	Cleber	login
2024-11-27 15:29:00.374642	Cleber	login
2024-11-27 15:29:07.390124	Cleber	login
2024-11-27 15:29:14.893332	Cleber	login
2024-11-27 15:29:22.17416	Cleber	login
2024-12-04 18:58:57.882636	Jonata Tyska	login
2024-12-05 20:34:22.910624	Andr├® Teixeira Milioli	login
2024-12-05 20:36:28.129182	Andr├® Teixeira Milioli	login
2024-12-05 20:36:58.855219	Andr├® Teixeira Milioli	login
2024-11-05 17:31:01.127298	Jos├® Eduardo Medeiros Jochem	login
2024-12-03 02:12:59.77766	Cleber	login
2024-12-03 02:13:54.956372	Cleber	login
2024-12-03 02:14:08.992608	Cleber	login
2024-12-03 02:14:23.308453	Cleber	login
2024-12-03 02:14:34.95767	Cleber	login
2024-12-03 02:15:27.894225	Cleber	login
2024-12-03 02:15:51.424946	Cleber	login
2024-12-03 02:16:08.144474	Cleber	login
2024-12-03 02:16:21.912619	Cleber	login
2024-12-03 02:16:36.273231	Cleber	login
2024-11-05 17:31:01.127298	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:31:01.291495	Jos├® Eduardo Medeiros Jochem	login
2024-12-03 12:21:58.005177	Jonata Tyska	login
2024-12-03 12:23:33.940685	Jonata Tyska	login
2024-11-05 17:31:03.699306	Felipe	login
2024-11-05 17:35:41.523432	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:38:52.221349	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:45:07.424689	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:48:02.653688	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:51:03.02767	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:51:03.050653	Jos├® Eduardo Medeiros Jochem	login
2024-12-04 02:58:24.904824	Cleber	login
2024-12-04 02:58:58.722072	Cleber	login
2024-12-04 02:59:10.066339	Cleber	login
2024-12-04 02:59:18.902378	Cleber	login
2024-12-04 02:59:28.050826	Cleber	login
2024-11-22 16:32:44.459664	Felipe	login
2024-11-22 16:37:36.725705	Felipe	login
2024-11-27 15:29:29.047747	Cleber	login
2024-11-27 15:29:35.942987	Cleber	login
2024-11-27 15:29:42.910481	Cleber	login
2024-11-27 15:29:48.986781	Cleber	login
2024-11-27 15:29:56.693535	Cleber	login
2024-11-27 15:30:02.816313	Cleber	login
2024-11-27 15:30:10.976198	Cleber	login
2024-11-27 15:30:18.420995	Cleber	login
2024-11-27 15:30:24.95724	Cleber	login
2024-11-27 15:30:31.473892	Cleber	login
2024-11-27 15:30:38.398518	Cleber	login
2024-11-27 15:30:49.716996	Cleber	login
2024-11-27 15:30:59.737702	Cleber	login
2024-11-27 15:31:14.41019	Cleber	login
2024-11-27 15:31:26.308156	Cleber	login
2024-11-27 15:31:37.099951	Cleber	login
2024-12-04 18:58:58.972874	Jonata Tyska	login
2024-12-05 20:34:23.638292	Andr├® Teixeira Milioli	login
2024-12-05 20:36:28.762808	Andr├® Teixeira Milioli	login
2024-12-05 20:37:28.257121	Andr├® Teixeira Milioli	login
2025-02-22 11:31:34.439576	Andr├® W├╝st Zibetti	login
2025-02-22 11:31:35.326894	Andr├® W├╝st Zibetti	login
2025-02-22 11:31:47.224784	Andr├® W├╝st Zibetti	login
2025-02-22 11:31:47.347963	Andr├® W├╝st Zibetti	login
2025-02-22 11:31:47.552573	Andr├® W├╝st Zibetti	login
2024-11-27 15:48:57.814056	Jonata Tyska	login
2024-11-27 15:49:00.91389	Jonata Tyska	login
2024-11-27 15:49:12.68418	Jonata Tyska	login
2024-11-27 15:49:14.295667	Jonata Tyska	login
2024-11-27 15:49:25.545849	Jonata Tyska	login
2024-11-27 15:49:26.58308	Jonata Tyska	login
2025-02-22 11:32:24.153258	Andr├® W├╝st Zibetti	login
2025-02-22 11:32:31.918815	Andr├® W├╝st Zibetti	login
2025-02-22 11:32:37.516037	Andr├® W├╝st Zibetti	login
2025-02-22 11:32:53.657178	Andr├® W├╝st Zibetti	login
2025-02-22 11:32:54.687058	Andr├® W├╝st Zibetti	login
2025-02-22 11:32:54.770058	Andr├® W├╝st Zibetti	login
2025-02-22 11:33:08.05374	Andr├® W├╝st Zibetti	login
2025-02-22 11:33:08.771037	Andr├® W├╝st Zibetti	login
2025-02-22 11:33:09.428792	Andr├® W├╝st Zibetti	login
2025-02-22 11:33:09.998053	Andr├® W├╝st Zibetti	login
2024-11-25 17:27:01.691954	Felipe	login
2024-11-25 17:28:15.479353	Felipe	login
2024-11-25 19:26:18.555369	Andr├® Teixeira Milioli	login
2024-11-05 17:54:52.57005	Jos├® Eduardo Medeiros Jochem	login
2024-11-25 19:26:34.513449	Andr├® Teixeira Milioli	login
2024-11-05 17:54:59.160391	Jos├® Eduardo Medeiros Jochem	login
2024-11-25 19:27:21.747936	Andr├® Teixeira Milioli	login
2024-11-05 17:54:59.182363	Jos├® Eduardo Medeiros Jochem	login
2024-11-25 19:28:43.281135	Andr├® Teixeira Milioli	login
2024-11-05 17:55:38.991914	Jos├® Eduardo Medeiros Jochem	login
2024-11-25 19:29:29.437519	Andr├® Teixeira Milioli	login
2024-11-05 17:55:55.89219	Jos├® Eduardo Medeiros Jochem	login
2024-11-26 14:28:54.698703	Felipe	login
2024-11-05 18:00:12.009069	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:00:46.520807	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:00:46.530989	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:01:31.784996	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:01:51.679427	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:01:51.693384	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:22.237649	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:22.916687	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:22.916687	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:22.916687	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:22.916687	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:57.684754	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:57.696621	Jos├® Eduardo Medeiros Jochem	login
2024-11-14 13:49:18.699494	Jonata Tyska	login
2024-12-02 03:40:09.323989	Cleber	login
2024-11-05 18:02:57.711773	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:02:58.669004	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:03:48.39565	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:03:48.39565	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:03:48.403949	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:03:48.403949	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:03:48.413984	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:03:49.179582	Jos├® Eduardo Medeiros Jochem	login
2024-11-14 13:49:56.507308	Jonata Tyska	login
2024-11-14 13:51:20.429322	Jonata Tyska	login
2024-12-02 03:40:10.155875	Cleber	login
2024-11-14 13:51:56.244254	Jonata Tyska	login
2024-11-14 13:53:16.775897	Jonata Tyska	login
2024-11-19 12:36:58.593268	Jonata Tyska	login
2024-12-02 03:41:14.309308	Cleber	login
2024-11-26 11:15:33.42788	Andr├® W├╝st Zibetti	login
2024-11-05 18:03:51.9583	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:11:50.897189	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:16:04.293443	Jos├® Eduardo Medeiros Jochem	login
2025-02-21 21:33:07.111649	Luis	login
2025-02-21 21:33:07.837049	Luis	login
2025-02-21 21:33:11.698265	Luis	login
2025-02-21 21:33:11.698265	Luis	login
2025-02-21 21:33:15.483582	Luis	login
2025-02-21 21:33:15.555481	Luis	login
2025-02-21 21:33:15.721963	Luis	login
2024-11-27 17:51:04.692201	Jerusa Marchi	login
2024-11-27 17:51:07.082224	Jerusa Marchi	login
2024-11-27 17:51:15.999876	Jerusa Marchi	login
2024-11-27 17:51:16.032185	Jerusa Marchi	login
2024-11-27 17:51:17.483195	Jerusa Marchi	login
2024-11-27 17:51:22.710649	Jerusa Marchi	login
2024-11-27 17:51:24.343146	Jerusa Marchi	login
2024-11-27 17:51:29.556912	Jerusa Marchi	login
2024-11-27 17:51:30.639764	Jerusa Marchi	login
2024-11-27 17:51:33.067683	Jerusa Marchi	login
2024-11-27 17:51:35.116216	Jerusa Marchi	login
2024-11-27 17:51:54.250828	Jerusa Marchi	login
2024-11-27 17:51:54.279345	Jerusa Marchi	login
2024-11-27 17:51:55.686877	Jerusa Marchi	login
2024-11-27 17:52:08.05903	Jerusa Marchi	login
2024-11-27 17:52:10.592329	Jerusa Marchi	login
2024-11-27 17:52:12.016862	Jerusa Marchi	login
2024-11-27 17:52:14.134463	Jerusa Marchi	login
2024-11-27 17:52:14.73179	Jerusa Marchi	login
2024-11-27 18:18:22.8439	Jerusa Marchi	login
2024-11-27 18:18:32.7791	Jerusa Marchi	login
2024-11-27 18:18:35.31382	Jerusa Marchi	login
2024-11-27 18:18:40.194012	Jerusa Marchi	login
2024-11-27 18:18:40.861003	Jerusa Marchi	login
2024-11-27 18:18:44.912434	Jerusa Marchi	login
2024-11-27 18:18:46.173019	Jerusa Marchi	login
2024-11-27 18:18:52.39562	Jerusa Marchi	login
2024-11-27 18:18:55.657118	Jerusa Marchi	login
2024-11-27 18:18:55.684716	Jerusa Marchi	login
2024-11-05 18:19:03.062123	Jos├® Eduardo Medeiros Jochem	login
2024-11-22 16:38:28.038616	Felipe	login
2024-11-22 16:38:28.038616	Felipe	login
2024-11-25 19:26:04.644069	Andr├® Teixeira Milioli	login
2024-11-05 18:20:52.610191	Jos├® Eduardo Medeiros Jochem	login
2024-11-25 19:26:26.820115	Andr├® Teixeira Milioli	login
2024-11-05 18:23:09.938685	Jos├® Eduardo Medeiros Jochem	login
2024-11-25 19:27:08.509203	Andr├® Teixeira Milioli	login
2024-11-05 18:32:49.314394	Jos├® Eduardo Medeiros Jochem	login
2024-11-25 19:27:57.121212	Andr├® Teixeira Milioli	login
2024-11-25 19:29:13.571581	Andr├® Teixeira Milioli	login
2024-12-05 20:35:29.232246	Andr├® Teixeira Milioli	login
2024-11-25 19:30:37.945274	Andr├® Teixeira Milioli	login
2024-11-26 14:28:56.735173	Felipe	login
2024-11-26 14:28:56.735173	Felipe	login
2024-11-26 14:28:56.735173	Felipe	login
2024-11-26 14:28:56.735173	Felipe	login
2024-11-26 14:28:56.735173	Felipe	login
2024-11-26 14:28:56.735173	Felipe	login
2024-12-05 20:36:47.25447	Andr├® Teixeira Milioli	login
2024-11-05 18:32:52.746154	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:32:52.847835	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:32:52.847835	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:32:52.847835	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:40.117724	Jos├® Eduardo Medeiros Jochem	login
2024-11-26 15:45:36.059093	Felipe	consulta_licitacao
2024-11-05 18:36:40.117724	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:43.692501	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:43.692501	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:55.638158	Jos├® Eduardo Medeiros Jochem	login
2024-11-26 15:56:37.549428	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 17:27:48.540822	Felipe	login
2024-11-26 15:56:37.549428	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 17:27:57.879316	Felipe	login
2024-11-26 15:56:37.549428	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 17:30:07.31424	Felipe	login
2024-11-08 20:29:54.017937	Felipe	login
2024-11-13 20:28:55.273779	Jerusa Marchi	login
2024-11-13 20:31:14.352162	Jerusa Marchi	login
2024-11-26 16:34:16.516295	Jos├® Eduardo Medeiros Jochem	login
2024-11-13 20:31:24.06527	Jerusa Marchi	login
2024-11-27 18:18:44.932627	Jerusa Marchi	login
2024-11-27 18:18:50.643746	Jerusa Marchi	login
2024-11-27 18:18:58.128461	Jerusa Marchi	login
2024-11-27 18:19:39.770412	Jerusa Marchi	login
2024-11-27 18:19:40.383869	Jerusa Marchi	login
2024-11-27 18:20:09.127888	Jerusa Marchi	login
2024-11-27 18:20:17.091745	Jerusa Marchi	login
2024-11-27 18:20:58.204318	Jerusa Marchi	login
2024-11-27 18:21:13.01469	Jerusa Marchi	login
2024-11-27 18:22:11.448475	Jerusa Marchi	login
2024-11-13 20:31:29.848139	Jerusa Marchi	login
2024-11-27 18:22:20.521763	Jonata Tyska	login
2024-11-27 18:22:31.28664	Jonata Tyska	login
2024-11-27 18:22:36.61	Jerusa Marchi	login
2024-11-27 18:23:03.67704	Jonata Tyska	login
2024-11-27 18:24:02.570947	Jonata Tyska	login
2024-11-27 18:24:43.232127	Jonata Tyska	login
2024-11-27 18:27:23.809969	Jonata Tyska	login
2024-11-27 18:27:32.152367	Jerusa Marchi	login
2024-11-27 18:27:37.482633	Jonata Tyska	login
2024-11-27 18:27:39.490755	Jonata Tyska	login
2024-11-27 18:27:53.676912	Jerusa Marchi	login
2024-11-27 18:27:55.149505	Jerusa Marchi	login
2024-11-27 18:28:20.768495	Jonata Tyska	login
2024-11-13 20:31:40.245125	Jerusa Marchi	login
2024-11-26 16:34:31.042529	Jos├® Eduardo Medeiros Jochem	login
2024-11-13 20:32:57.299486	Jerusa Marchi	login
2024-11-13 20:33:18.837369	Jerusa Marchi	login
2024-11-26 11:15:51.940515	Andr├® W├╝st Zibetti	login
2024-11-26 11:16:28.188263	Andr├® W├╝st Zibetti	login
2024-12-03 02:13:12.69748	Cleber	login
2024-12-03 02:13:16.203979	Cleber	login
2024-12-03 02:13:20.040138	Cleber	login
2024-12-03 02:13:21.084693	Cleber	login
2024-12-03 02:13:47.793369	Cleber	login
2024-12-03 02:14:04.716607	Cleber	login
2024-12-03 02:14:22.200528	Cleber	login
2024-12-03 02:14:27.940472	Cleber	login
2024-12-03 02:15:25.981976	Cleber	login
2024-12-03 02:15:49.629416	Cleber	login
2024-12-03 02:16:06.297686	Cleber	login
2024-12-03 02:16:19.60464	Cleber	login
2024-12-03 02:16:34.209174	Cleber	login
2024-11-14 13:49:41.103283	Jonata Tyska	login
2024-11-14 13:49:50.470391	Jonata Tyska	login
2024-12-03 12:22:11.639384	Jonata Tyska	login
2024-11-26 11:16:28.827654	Andr├® W├╝st Zibetti	login
2024-11-26 16:34:33.17895	Jos├® Eduardo Medeiros Jochem	login
2024-11-14 13:49:57.209255	Jonata Tyska	login
2024-11-14 13:50:17.674116	Jonata Tyska	login
2024-11-14 13:51:26.347012	Jonata Tyska	login
2024-11-14 13:51:51.232624	Jonata Tyska	login
2024-11-26 11:17:26.723072	Andr├® W├╝st Zibetti	login
2024-11-14 13:51:57.381927	Jonata Tyska	login
2024-11-14 13:52:11.964525	Jonata Tyska	login
2024-11-26 16:34:33.17895	Jos├® Eduardo Medeiros Jochem	login
2024-11-26 11:17:54.568941	Andr├® W├╝st Zibetti	login
2024-11-18 17:20:20.854311	Felipe	login
2024-11-26 16:34:36.057437	Jos├® Eduardo Medeiros Jochem	login
2024-11-26 14:33:58.013083	Felipe	login
2024-11-19 12:37:31.649623	Jonata Tyska	login
2024-11-26 14:37:06.95997	Felipe	login
2024-11-19 12:38:09.57812	Jonata Tyska	login
2024-11-26 14:37:07.99073	Felipe	login
2024-12-04 02:58:27.51016	Cleber	login
2024-12-04 02:58:59.297934	Cleber	login
2024-12-04 02:59:10.754282	Cleber	login
2024-12-04 02:59:19.47018	Cleber	login
2024-12-04 02:59:28.670881	Cleber	login
2024-12-04 03:00:10.575254	Cleber	login
2024-12-04 03:00:23.782398	Cleber	login
2024-11-19 12:38:17.925302	Jonata Tyska	login
2024-11-26 14:37:08.004741	Felipe	login
2024-11-19 12:38:30.496092	Jonata Tyska	login
2024-12-19 14:33:24.961917	M├írcio Castro	login
2024-11-26 14:37:12.983453	Felipe	login
2024-12-18 12:37:39.858841	Renato Fileto	login
2024-11-19 12:38:40.266294	Jonata Tyska	login
2024-11-26 14:37:12.983453	Felipe	login
2024-11-19 12:39:40.935093	Jonata Tyska	login
2024-11-26 14:37:13.022141	Felipe	login
2024-11-19 12:39:47.598509	Jonata Tyska	login
2024-11-26 14:37:13.022141	Felipe	login
2024-11-19 12:39:52.142952	Jonata Tyska	login
2024-11-26 16:34:45.104706	Jos├® Eduardo Medeiros Jochem	login
2024-11-19 12:40:40.372587	Jonata Tyska	login
2024-11-26 16:34:45.104706	Jos├® Eduardo Medeiros Jochem	login
2024-11-19 12:40:41.298341	Jonata Tyska	login
2025-02-21 23:56:27.920766	Jos├® Eduardo Medeiros Jochem	login
2024-11-19 12:40:55.433045	Jonata Tyska	login
2025-02-21 23:56:41.943009	Jos├® Eduardo Medeiros Jochem	login
2024-11-19 12:41:19.850667	Jonata Tyska	login
2024-11-22 16:36:29.507638	Felipe	login
2024-11-22 16:36:29.507638	Felipe	login
2024-11-22 16:38:29.475124	Felipe	login
2024-11-22 22:02:56.279369	Felipe	login
2025-02-25 22:22:44.825416	Felipe	login
2024-11-25 19:26:19.148032	Andr├® Teixeira Milioli	login
2024-11-27 18:19:13.147447	Jerusa Marchi	login
2024-11-25 19:26:49.401158	Andr├® Teixeira Milioli	login
2024-11-27 18:19:13.752168	Jerusa Marchi	login
2024-11-25 19:27:22.085715	Andr├® Teixeira Milioli	login
2024-11-27 18:19:17.83827	Jerusa Marchi	login
2024-11-25 19:28:45.121273	Andr├® Teixeira Milioli	login
2024-11-27 18:19:17.83827	Jerusa Marchi	login
2024-11-25 19:29:47.540887	Andr├® Teixeira Milioli	login
2024-11-27 18:19:48.055711	Jerusa Marchi	login
2024-11-26 14:28:58.865764	Felipe	login
2024-11-27 18:19:48.089265	Jerusa Marchi	login
2024-11-27 18:19:49.395337	Jerusa Marchi	login
2024-11-27 18:20:07.258348	Jerusa Marchi	login
2024-11-27 18:20:10.489897	Jerusa Marchi	login
2024-11-27 18:20:18.259616	Jerusa Marchi	login
2024-11-27 18:20:55.687805	Jerusa Marchi	login
2024-11-27 18:21:12.381326	Jerusa Marchi	login
2024-11-27 18:21:26.004442	Jerusa Marchi	login
2024-11-27 18:21:26.581437	Jerusa Marchi	login
2024-11-27 18:22:12.074612	Jerusa Marchi	login
2024-11-27 18:22:22.706891	Jonata Tyska	login
2024-11-27 18:22:32.222288	Jonata Tyska	login
2024-11-27 18:22:35.586066	Jerusa Marchi	login
2024-11-27 18:22:48.951632	Jonata Tyska	login
2024-11-27 18:23:05.158519	Jonata Tyska	login
2024-11-27 18:23:57.605077	Jonata Tyska	login
2024-11-27 18:24:42.390784	Jonata Tyska	login
2024-11-27 18:27:16.882915	Jerusa Marchi	login
2024-11-27 18:27:16.915903	Jerusa Marchi	login
2024-11-27 18:27:29.575156	Jonata Tyska	login
2024-11-27 18:27:31.016601	Jonata Tyska	login
2024-11-27 18:27:32.224847	Jonata Tyska	login
2024-11-27 18:27:34.161656	Jerusa Marchi	login
2024-11-27 18:27:35.220791	Jonata Tyska	login
2024-11-27 18:27:36.098687	Jonata Tyska	login
2024-11-27 18:27:40.444023	Jonata Tyska	login
2024-11-27 18:27:42.70163	Jonata Tyska	login
2024-11-27 18:27:44.500204	Jonata Tyska	login
2024-11-27 18:27:57.628677	Jonata Tyska	login
2024-11-27 18:28:10.565477	Jerusa Marchi	login
2024-11-27 18:28:19.699742	Jonata Tyska	login
2024-12-19 14:33:19.12646	M├írcio Castro	login
2024-11-27 22:28:01.802635	Cleber	login
2024-11-27 22:28:04.479212	Cleber	login
2025-02-25 22:22:45.45701	Felipe	login
2025-02-25 22:22:51.962241	Felipe	login
2025-02-25 22:22:51.991599	Felipe	login
2024-12-05 20:35:30.124284	Andr├® Teixeira Milioli	login
2024-12-05 20:36:58.558604	Andr├® Teixeira Milioli	login
2024-12-10 13:08:48.768619	M├írcio Castro	login
2024-12-10 13:08:54.799511	M├írcio Castro	login
2025-02-25 22:22:52.025865	Felipe	login
2025-02-25 22:22:55.775099	Felipe	login
2025-02-25 22:22:55.801031	Felipe	login
2025-02-25 22:22:55.834884	Felipe	login
2024-11-19 12:41:21.136433	Jonata Tyska	login
2024-11-19 12:42:37.282425	Jonata Tyska	login
2024-11-19 12:42:46.124628	Jonata Tyska	login
2024-12-23 19:27:40.362029	M├írcio Castro	login
2025-02-21 23:56:41.943009	Jos├® Eduardo Medeiros Jochem	login
2024-11-19 13:42:08.297404	Jonata Tyska	login
2024-11-28 11:35:44.606162	Jonata Tyska	login
2024-11-28 11:35:54.824699	Jonata Tyska	login
2024-11-28 11:36:06.132633	Jonata Tyska	login
2024-11-28 11:36:07.057768	Jonata Tyska	login
2024-11-28 11:36:20.863477	Jonata Tyska	login
2024-11-28 11:36:21.438583	Jonata Tyska	login
2024-11-28 11:36:37.282207	Jonata Tyska	login
2024-11-28 11:36:52.478656	Jonata Tyska	login
2024-11-28 11:36:54.241954	Jonata Tyska	login
2024-11-28 11:39:30.577885	Jonata Tyska	login
2024-11-28 11:39:31.347444	Jonata Tyska	login
2024-11-28 11:39:40.789523	Jonata Tyska	login
2024-11-28 11:39:41.297923	Jonata Tyska	login
2024-11-28 11:39:44.556162	Jonata Tyska	login
2024-11-28 11:39:46.934931	Jonata Tyska	login
2024-11-28 11:39:49.589806	Jonata Tyska	login
2024-11-19 13:47:04.221418	Jonata Tyska	login
2024-11-28 15:26:07.801529	Jonata Tyska	login
2024-11-28 15:26:11.100566	Jonata Tyska	login
2024-11-28 15:26:26.256176	Jonata Tyska	login
2024-11-28 15:26:28.291505	Jonata Tyska	login
2024-11-28 15:26:33.323644	Jonata Tyska	login
2024-11-28 15:26:52.166307	Jonata Tyska	login
2024-11-28 15:26:55.285701	Jonata Tyska	login
2024-11-28 20:41:54.309696	Cleber	login
2024-11-28 20:41:57.432938	Cleber	login
2024-11-28 20:42:13.494403	Cleber	login
2024-11-28 20:42:30.698444	Cleber	login
2024-11-28 20:42:32.553947	Cleber	login
2024-12-02 03:37:53.66586	Cleber	login
2024-12-02 03:37:56.286933	Cleber	login
2024-12-02 03:38:14.704032	Cleber	login
2024-12-02 03:38:15.343654	Cleber	login
2024-12-02 03:38:31.155888	Cleber	login
2024-12-02 03:38:32.204069	Cleber	login
2024-12-02 03:38:36.216005	Cleber	login
2024-12-02 03:38:37.843988	Cleber	login
2024-12-02 03:38:37.843988	Cleber	login
2024-12-02 03:38:41.832699	Cleber	login
2024-12-02 03:38:43.540351	Cleber	login
2024-12-02 03:38:44.083766	Cleber	login
2024-12-02 03:38:45.53223	Cleber	login
2024-12-02 03:38:56.443797	Cleber	login
2024-12-02 03:38:57.248477	Cleber	login
2024-12-02 03:39:14.9411	Cleber	login
2024-12-02 03:39:15.37701	Cleber	login
2024-12-02 03:39:21.997666	Cleber	login
2024-12-02 03:39:23.080901	Cleber	login
2024-12-02 03:39:23.548009	Cleber	login
2024-12-02 03:39:31.881395	Cleber	login
2024-12-02 03:39:40.145756	Cleber	login
2024-12-02 03:39:41.105278	Cleber	login
2024-12-02 03:39:43.573021	Cleber	login
2024-12-02 03:39:46.14098	Cleber	login
2024-12-02 03:39:58.996722	Cleber	login
2024-12-02 03:39:59.044482	Cleber	login
2024-12-02 03:39:59.08864	Cleber	login
2024-12-02 03:40:05.921983	Cleber	login
2024-12-02 03:40:05.959763	Cleber	login
2024-12-02 03:40:06.003655	Cleber	login
2024-12-02 03:40:06.768385	Cleber	login
2024-12-02 03:40:06.808177	Cleber	login
2024-12-02 03:40:06.851944	Cleber	login
2024-12-02 03:40:07.428351	Cleber	login
2024-12-02 03:40:07.468214	Cleber	login
2024-12-02 03:40:07.507638	Cleber	login
2024-12-02 03:40:07.988416	Cleber	login
2024-12-02 03:40:08.027932	Cleber	login
2024-12-02 03:40:08.067812	Cleber	login
2024-12-02 03:40:08.368384	Cleber	login
2024-12-02 03:40:08.407982	Cleber	login
2024-12-02 03:40:08.476127	Cleber	login
2024-12-02 03:40:08.82422	Cleber	login
2024-12-02 03:40:08.864378	Cleber	login
2024-12-02 03:40:08.907647	Cleber	login
2024-11-22 16:38:22.306391	Felipe	login
2024-11-22 16:38:22.306391	Felipe	login
2024-11-22 16:59:36.040288	Felipe	login
2024-11-22 17:02:31.913982	Felipe	login
2024-11-22 22:03:53.33762	Felipe	login
2024-11-22 19:25:19.109761	Felipe	login
2024-11-25 19:26:05.232596	Andr├® Teixeira Milioli	login
2024-11-22 19:25:21.260721	Felipe	login
2024-11-22 19:28:37.669887	Felipe	login
2024-11-22 19:28:37.669887	Felipe	login
2024-11-22 19:28:49.762618	Felipe	login
2024-11-22 19:28:49.762618	Felipe	login
2024-11-22 19:28:49.762618	Felipe	login
2024-11-22 19:28:49.762618	Felipe	login
2024-11-22 19:28:49.762618	Felipe	login
2024-11-22 19:28:49.812376	Felipe	login
2024-11-25 19:26:34.050531	Andr├® Teixeira Milioli	login
2024-11-22 21:21:38.202901	Felipe	login
2024-11-22 21:21:57.894725	Felipe	login
2024-11-22 21:23:14.798269	Felipe	login
2024-12-18 13:41:41.998127	Matheus Machado dos Santos	login
2024-11-22 21:23:16.96169	Felipe	login
2024-11-25 19:27:08.866845	Andr├® Teixeira Milioli	login
2024-11-22 21:25:31.344762	Felipe	login
2024-12-18 13:41:43.137421	Matheus Machado dos Santos	login
2024-11-22 21:25:33.46147	Felipe	login
2024-11-25 19:28:36.789294	Andr├® Teixeira Milioli	login
2024-11-22 21:25:36.512682	Felipe	login
2024-11-25 19:29:29.065245	Andr├® Teixeira Milioli	login
2024-11-22 21:25:37.276382	Felipe	login
2024-12-18 13:41:53.758688	Matheus Machado dos Santos	login
2024-11-22 21:25:39.874135	Felipe	login
2024-11-25 19:30:38.348503	Andr├® Teixeira Milioli	login
2024-11-22 21:25:50.343978	Felipe	login
2024-11-26 14:30:33.699804	Felipe	login
2024-11-22 21:25:51.981742	Felipe	login
2024-11-26 14:30:38.807634	Felipe	login
2024-11-22 21:28:33.558076	Felipe	login
2024-11-26 14:30:38.807634	Felipe	login
2024-11-22 21:28:35.671958	Felipe	login
2024-11-26 14:30:58.606325	Felipe	login
2024-11-22 21:28:39.344851	Felipe	login
2024-11-26 14:30:58.606325	Felipe	login
2024-11-22 21:28:40.223422	Felipe	login
2024-11-26 14:30:58.606325	Felipe	login
2024-11-22 21:28:46.291471	Felipe	login
2024-11-22 21:28:46.336712	Felipe	login
2024-11-22 21:29:02.293103	Felipe	login
2024-11-22 21:29:02.305836	Felipe	login
2024-11-22 21:29:10.268326	Felipe	login
2024-11-22 21:29:10.268326	Felipe	login
2024-11-22 21:29:10.268326	Felipe	login
2024-11-22 21:29:10.284343	Felipe	login
2024-11-22 21:29:10.284343	Felipe	login
2024-11-22 21:29:10.284343	Felipe	login
2024-11-22 21:29:25.043031	Felipe	login
2024-11-22 21:29:25.043031	Felipe	login
2024-11-22 21:30:46.238953	Felipe	login
2024-11-22 21:42:16.686419	Felipe	login
2024-11-22 21:42:38.860189	Felipe	login
2024-11-22 21:42:38.860189	Felipe	login
2024-11-22 21:42:38.860189	Felipe	login
2024-11-22 21:42:38.860189	Felipe	login
2024-11-22 21:42:38.860189	Felipe	login
2024-11-22 21:42:38.860189	Felipe	login
2024-11-22 21:42:38.860189	Felipe	login
2024-11-22 21:42:51.602076	Felipe	login
2024-11-22 21:42:51.602076	Felipe	login
2024-11-22 21:42:51.635442	Felipe	login
2024-11-26 14:30:58.606325	Felipe	login
2024-11-22 21:43:26.310932	Felipe	login
2024-11-22 21:43:42.422101	Felipe	login
2024-11-22 21:43:42.422101	Felipe	login
2024-11-22 21:43:42.422101	Felipe	login
2024-11-22 21:43:42.422101	Felipe	login
2024-11-22 21:43:42.422101	Felipe	login
2024-11-22 21:43:42.422101	Felipe	login
2024-11-26 14:30:58.606325	Felipe	login
2024-11-26 14:30:58.606325	Felipe	login
2024-11-26 14:31:00.355216	Felipe	login
2024-11-26 14:31:00.370626	Felipe	login
2024-11-26 14:34:07.441239	Felipe	login
2024-11-26 14:34:39.488138	Felipe	login
2024-11-22 21:44:08.647112	Felipe	login
2024-11-26 14:34:39.50276	Felipe	login
2024-12-18 13:41:54.777346	Matheus Machado dos Santos	login
2024-12-02 03:38:16.832295	Cleber	login
2024-12-02 03:38:39.311985	Cleber	login
2024-12-02 03:38:46.163835	Cleber	login
2024-12-02 03:39:17.481205	Cleber	login
2024-12-02 03:40:09.285347	Cleber	login
2024-12-02 03:40:10.107504	Cleber	login
2024-12-02 03:40:15.69193	Cleber	login
2024-12-02 03:41:08.183688	Cleber	login
2024-12-02 03:41:09.131526	Cleber	login
2024-12-02 03:41:15.488644	Cleber	login
2024-12-02 03:41:16.145393	Cleber	login
2024-12-02 03:41:18.621212	Cleber	login
2024-12-02 03:41:19.336452	Cleber	login
2024-11-19 13:47:51.83717	Jonata Tyska	login
2024-12-10 13:08:47.348078	M├írcio Castro	login
2024-12-10 13:08:49.975248	M├írcio Castro	login
2024-12-10 13:08:53.562179	M├írcio Castro	login
2024-12-10 13:08:57.739422	M├írcio Castro	login
2024-12-10 13:09:53.995155	Jonata Tyska	login
2024-12-10 13:11:15.435973	Jonata Tyska	login
2024-12-03 02:13:13.42532	Cleber	login
2024-12-03 02:13:19.121244	Cleber	login
2024-12-03 02:13:20.488877	Cleber	login
2024-12-03 02:13:48.738813	Cleber	login
2024-12-03 02:14:08.076426	Cleber	login
2024-12-03 02:14:22.680616	Cleber	login
2024-12-03 02:14:26.097211	Cleber	login
2024-12-03 02:15:22.013291	Cleber	login
2024-12-03 02:15:45.368661	Cleber	login
2024-12-03 02:15:57.573635	Cleber	login
2024-12-03 02:16:16.437057	Cleber	login
2024-12-03 02:16:30.796652	Cleber	login
2024-12-03 02:16:36.99335	Cleber	login
2024-12-03 12:22:28.977124	Jonata Tyska	login
2024-11-19 13:47:56.033974	Jonata Tyska	login
2024-11-19 13:48:14.851061	Jonata Tyska	login
2024-11-19 13:48:34.884227	Jonata Tyska	login
2024-12-18 13:42:13.752618	Matheus Machado dos Santos	login
2024-12-18 13:42:22.229685	Matheus Machado dos Santos	login
2024-12-18 13:42:23.156417	Matheus Machado dos Santos	login
2024-11-19 14:18:11.498781	Luis	login
2024-11-19 14:18:19.118862	Luis	login
2024-11-19 14:56:13.549836	Luis	login
2024-11-19 14:56:20.596382	Luis	login
2024-11-19 14:56:44.277639	Luis	login
2025-02-21 23:56:44.429671	Jos├® Eduardo Medeiros Jochem	login
2025-02-21 23:56:44.458411	Jos├® Eduardo Medeiros Jochem	login
2024-12-19 22:39:50.180888	Renato Fileto	login
2024-12-04 02:58:53.226937	Cleber	login
2024-12-04 02:59:01.598457	Cleber	login
2024-12-04 02:59:14.798213	Cleber	login
2024-12-04 02:59:22.71453	Cleber	login
2024-12-04 02:59:31.906334	Cleber	login
2024-12-04 03:00:18.620657	Cleber	login
2024-12-04 03:02:28.816639	Cleber	login
2025-02-21 23:56:44.528522	Jos├® Eduardo Medeiros Jochem	login
2024-11-19 14:56:54.215173	Luis	login
2024-11-19 14:56:54.329152	Luis	login
2024-11-19 14:57:10.501953	Luis	login
2024-11-19 14:57:19.30824	Luis	login
2025-02-23 18:04:18.271823	Andr├® W├╝st Zibetti	login
2025-02-23 18:04:18.841474	Andr├® W├╝st Zibetti	login
2024-11-19 14:58:48.523049	Luis	login
2024-11-19 14:58:50.29352	Luis	login
2024-11-19 14:58:50.29352	Luis	login
2024-11-19 14:59:05.759379	Luis	login
2024-11-19 14:59:12.886651	Luis	login
2024-11-19 14:59:12.886651	Luis	login
2024-11-19 14:59:18.469757	Luis	login
2024-11-19 14:59:20.163506	Luis	login
2024-11-19 14:59:20.163506	Luis	login
2025-02-23 18:04:19.439347	Andr├® W├╝st Zibetti	login
2025-02-23 18:05:31.657516	Andr├® W├╝st Zibetti	login
2025-02-23 18:05:32.00392	Andr├® W├╝st Zibetti	login
2024-11-19 20:45:53.429711	Andr├® Teixeira Milioli	login
2024-11-19 20:45:54.756691	Andr├® Teixeira Milioli	login
2024-11-19 20:46:06.904033	Andr├® Teixeira Milioli	login
2025-02-23 18:05:47.800114	Andr├® W├╝st Zibetti	login
2025-02-23 18:05:47.870338	Andr├® W├╝st Zibetti	login
2025-02-23 18:05:47.904483	Andr├® W├╝st Zibetti	login
2024-11-19 20:46:16.315665	Andr├® Teixeira Milioli	login
2024-11-19 20:46:20.095656	Andr├® Teixeira Milioli	login
2024-11-19 20:46:21.12998	Andr├® Teixeira Milioli	login
2025-02-23 18:05:52.130893	Andr├® W├╝st Zibetti	login
2024-12-02 03:40:09.371952	Cleber	login
2024-12-02 03:40:13.275977	Cleber	login
2024-11-19 20:46:43.093283	Andr├® Teixeira Milioli	login
2024-11-19 20:46:43.856821	Andr├® Teixeira Milioli	login
2024-11-19 20:47:30.606641	Andr├® Teixeira Milioli	login
2024-12-02 03:40:53.916032	Cleber	login
2024-12-02 03:41:14.917007	Cleber	login
2024-12-02 03:41:18.013707	Cleber	login
2025-02-23 18:05:52.808396	Andr├® W├╝st Zibetti	login
2025-02-23 18:05:57.167364	Andr├® W├╝st Zibetti	login
2024-11-05 18:03:51.987311	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:04:04.024756	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:04:54.112754	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:05:57.669669	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:06:08.239515	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:07:16.060849	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:08:43.881853	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:09:27.94421	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:10:32.582086	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:12:59.538963	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:17:52.382711	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:20:52.643305	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:23:09.970068	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:32:52.758093	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:35:16.127094	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:35:16.127094	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:35:16.127094	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:26.7694	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:38.975311	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:43.677386	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:43.677386	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:43.677386	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:43.677386	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:54.37819	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:54.37819	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:54.37819	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:54.37819	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:54.395845	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 17:27:42.039376	Felipe	login
2024-11-26 16:34:19.033859	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 17:27:57.50324	Felipe	login
2024-11-26 16:34:40.679772	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 17:30:06.922149	Felipe	login
2024-11-26 16:34:45.11454	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 20:29:57.646987	Felipe	login
2024-11-26 16:34:45.11454	Jos├® Eduardo Medeiros Jochem	login
2024-11-13 20:29:18.387644	Jerusa Marchi	login
2024-11-13 20:30:03.595756	Jerusa Marchi	login
2024-11-13 20:31:18.694492	Jerusa Marchi	login
2024-11-13 20:31:32.896586	Jerusa Marchi	login
2024-11-13 20:31:57.060708	Jerusa Marchi	login
2024-11-26 16:34:45.11454	Jos├® Eduardo Medeiros Jochem	login
2024-11-14 13:49:15.885375	Jonata Tyska	login
2024-11-14 13:49:51.147438	Jonata Tyska	login
2024-11-14 13:50:18.934194	Jonata Tyska	login
2025-02-23 18:05:57.996143	Andr├® W├╝st Zibetti	login
2024-11-14 13:51:51.801619	Jonata Tyska	login
2024-11-14 13:53:15.912375	Jonata Tyska	login
2024-11-18 17:20:18.672552	Felipe	login
2025-02-23 18:05:58.029559	Andr├® W├╝st Zibetti	login
2024-11-18 17:20:43.829954	Felipe	login
2024-11-18 17:20:43.829954	Felipe	login
2024-11-19 12:36:51.371086	Jonata Tyska	login
2025-02-23 18:06:36.750276	Andr├® W├╝st Zibetti	login
2024-11-19 12:38:17.250275	Jonata Tyska	login
2025-02-23 18:06:36.772391	Andr├® W├╝st Zibetti	login
2024-11-19 12:39:11.888506	Jonata Tyska	login
2024-11-19 12:39:52.984534	Jonata Tyska	login
2024-11-19 12:41:04.324523	Jonata Tyska	login
2024-11-19 12:42:44.770173	Jonata Tyska	login
2024-11-19 12:42:47.311623	Jonata Tyska	login
2024-11-26 11:15:35.43582	Andr├® W├╝st Zibetti	login
2024-11-19 13:41:42.646094	Jonata Tyska	login
2024-11-19 13:41:57.855042	Jonata Tyska	login
2024-11-26 11:16:24.93285	Andr├® W├╝st Zibetti	login
2024-11-26 11:16:29.839017	Andr├® W├╝st Zibetti	login
2024-11-19 13:47:20.83571	Jonata Tyska	login
2024-11-19 13:47:44.56233	Jonata Tyska	login
2024-11-26 11:17:53.725729	Andr├® W├╝st Zibetti	login
2024-11-19 13:47:54.543523	Jonata Tyska	login
2024-11-26 14:34:05.98248	Felipe	login
2024-11-19 13:48:13.884467	Jonata Tyska	login
2024-11-26 14:34:05.98248	Felipe	login
2024-11-19 13:48:33.628755	Jonata Tyska	login
2024-11-19 13:48:36.110979	Jonata Tyska	login
2024-11-26 14:34:05.98248	Felipe	login
2024-11-26 14:34:05.98248	Felipe	login
2024-11-26 14:34:05.98248	Felipe	login
2024-11-19 14:18:26.965603	Luis	login
2024-11-19 14:18:27.025585	Luis	login
2024-11-19 14:18:44.612587	Luis	login
2024-11-26 14:34:05.98248	Felipe	login
2024-11-26 14:37:06.999604	Felipe	login
2024-11-19 14:56:45.618426	Luis	login
2024-11-19 14:56:47.05963	Luis	login
2024-11-19 14:57:43.75062	Luis	login
2024-11-19 14:57:43.75062	Luis	login
2024-11-19 14:58:47.18858	Luis	login
2024-11-26 14:37:14.1834	Felipe	login
2024-11-19 14:59:05.714773	Luis	login
2024-11-19 14:59:18.445736	Luis	login
2024-11-19 19:58:34.2014	Andr├® Teixeira Milioli	login
2024-11-19 19:58:41.105482	Andr├® Teixeira Milioli	login
2024-11-26 14:37:14.1834	Felipe	login
2024-11-27 14:38:59.441339	Cleber	login
2024-11-19 20:46:07.918663	Andr├® Teixeira Milioli	login
2024-11-19 20:46:15.227663	Andr├® Teixeira Milioli	login
2024-11-27 14:39:02.048564	Cleber	login
2024-11-27 14:39:02.921513	Cleber	login
2024-11-19 20:46:28.02134	Andr├® Teixeira Milioli	login
2024-11-19 20:46:29.025396	Andr├® Teixeira Milioli	login
2024-11-27 14:39:03.560631	Cleber	login
2024-11-27 14:39:04.873308	Cleber	login
2024-11-19 20:47:31.430959	Andr├® Teixeira Milioli	login
2024-11-19 20:47:39.304607	Andr├® Teixeira Milioli	login
2024-11-27 14:39:06.368732	Cleber	login
2024-11-19 20:47:40.12187	Andr├® Teixeira Milioli	login
2024-11-27 14:39:10.261845	Cleber	login
2024-11-19 20:47:54.968592	Andr├® Teixeira Milioli	login
2024-11-27 14:39:11.417895	Cleber	login
2024-11-19 20:47:55.475391	Andr├® Teixeira Milioli	login
2024-11-27 14:39:12.375531	Cleber	login
2024-11-19 20:48:35.751725	Andr├® Teixeira Milioli	login
2024-11-27 14:39:14.117662	Cleber	login
2024-11-19 20:48:36.249584	Andr├® Teixeira Milioli	login
2024-11-26 17:57:24.587628	Cleber	login
2024-11-19 20:49:17.964921	Andr├® Teixeira Milioli	login
2024-11-27 14:39:15.833424	Cleber	login
2024-11-27 14:39:17.215258	Cleber	login
2024-11-27 14:39:18.74499	Cleber	login
2024-11-27 14:39:20.078382	Cleber	login
2024-11-27 14:39:20.688537	Cleber	login
2024-11-27 14:39:22.200658	Cleber	login
2024-11-27 14:39:23.403598	Cleber	login
2024-11-27 14:39:25.024515	Cleber	login
2024-11-27 14:39:26.396955	Cleber	login
2024-11-27 14:39:27.677475	Cleber	login
2024-11-27 14:39:29.511922	Cleber	login
2024-11-05 18:04:54.094712	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:05:57.650334	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:06:08.220023	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:07:16.042111	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:08:43.826118	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:09:27.886619	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:10:32.530669	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:11:50.849176	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:12:59.490506	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:16:04.244292	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:17:52.339416	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:18:23.249068	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:18:23.249068	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:19:03.101154	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:32:49.340662	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:26.741845	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:38.961636	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:39.34337	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:36:39.34337	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:38:01.780253	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:38:02.029629	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:46:04.213116	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:46:04.395729	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:48:53.722818	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 18:48:53.838069	Jos├® Eduardo Medeiros Jochem	login
2024-11-26 16:34:20.685189	Jos├® Eduardo Medeiros Jochem	login
2024-11-06 13:36:15.195268	Matheus Machado dos Santos	login
2024-11-08 19:42:29.523499	Felipe	login
2024-11-06 13:36:17.277634	Matheus Machado dos Santos	login
2024-11-26 16:34:36.071084	Jos├® Eduardo Medeiros Jochem	login
2024-11-06 13:36:59.005051	Matheus Machado dos Santos	login
2024-11-08 19:42:47.428893	Felipe	login
2024-11-06 13:36:59.191794	Matheus Machado dos Santos	login
2024-11-26 16:34:41.353996	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:42:56.352482	Felipe	login
2024-11-07 21:38:57.036959	Matheus Machado dos Santos	login
2025-02-23 18:06:36.842931	Andr├® W├╝st Zibetti	login
2024-11-07 21:39:01.349912	Matheus Machado dos Santos	login
2024-11-08 19:43:07.95519	Felipe	login
2024-11-07 21:39:24.37747	Matheus Machado dos Santos	login
2024-11-27 14:39:31.879294	Cleber	login
2024-11-07 21:39:24.648373	Matheus Machado dos Santos	login
2024-11-08 19:43:09.93226	Felipe	login
2024-11-27 14:39:39.556997	Cleber	login
2024-11-07 23:38:46.047297	Matheus Machado dos Santos	login
2024-11-08 19:43:14.095976	Felipe	login
2024-11-07 23:38:46.602757	Matheus Machado dos Santos	login
2024-11-27 14:39:44.972616	Cleber	login
2024-11-07 23:39:01.307777	Matheus Machado dos Santos	login
2024-11-08 19:43:19.425418	Felipe	login
2024-11-07 23:39:01.661424	Matheus Machado dos Santos	login
2024-11-27 14:39:52.693655	Cleber	login
2024-11-08 19:44:08.901682	Felipe	login
2024-11-08 02:35:50.651766	Felipe	login
2024-11-26 17:57:25.369026	Cleber	login
2024-11-08 02:35:51.051697	Felipe	login
2024-11-08 19:44:53.884663	Felipe	login
2024-11-08 02:36:01.017504	Felipe	login
2024-11-08 19:45:31.08748	Felipe	login
2024-11-08 02:36:01.241844	Felipe	login
2024-11-27 14:40:05.888374	Cleber	login
2024-11-08 02:36:06.723002	Felipe	login
2024-11-08 19:46:02.174523	Felipe	login
2024-11-08 02:36:06.969591	Felipe	login
2024-11-27 14:40:13.699132	Cleber	login
2024-11-08 02:36:10.559802	Felipe	login
2024-11-08 19:46:06.708494	Felipe	login
2024-11-08 02:36:10.796771	Felipe	login
2024-11-27 14:40:19.692818	Cleber	login
2024-11-08 02:36:11.893808	Felipe	login
2024-11-08 19:46:29.574222	Felipe	login
2024-11-08 02:45:42.992506	Felipe	login
2024-11-08 02:45:42.992506	Felipe	login
2024-11-08 02:45:55.712383	Felipe	login
2024-11-08 02:45:56.652823	Felipe	login
2024-11-08 02:46:05.103909	Felipe	login
2024-11-08 02:46:06.522653	Felipe	login
2024-11-08 02:46:06.522653	Felipe	login
2024-11-08 02:46:32.34798	Felipe	login
2024-11-08 02:46:32.417023	Felipe	login
2024-11-08 02:46:33.202876	Felipe	login
2024-11-08 02:46:34.128642	Felipe	login
2024-11-08 02:46:40.780026	Felipe	login
2024-11-08 02:46:40.807336	Felipe	login
2024-11-08 02:46:41.586998	Felipe	login
2024-11-08 02:46:42.424729	Felipe	login
2024-11-08 02:47:13.030642	Felipe	login
2024-11-08 02:47:37.273938	Felipe	login
2024-11-08 02:47:37.355205	Felipe	login
2024-11-08 19:46:43.43977	Felipe	login
2024-11-08 12:55:04.547609	Matheus Machado dos Santos	login
2024-11-08 19:47:25.825924	Felipe	login
2024-11-08 12:55:06.930656	Matheus Machado dos Santos	login
2024-11-08 19:47:36.497314	Felipe	login
2024-11-08 12:55:18.241181	Matheus Machado dos Santos	login
2024-11-08 19:49:16.08787	Felipe	login
2024-11-08 12:55:18.689603	Matheus Machado dos Santos	login
2024-11-08 19:49:41.689006	Felipe	login
2024-11-08 12:55:23.238421	Matheus Machado dos Santos	login
2024-11-27 14:40:28.008253	Cleber	login
2024-11-08 12:55:23.848865	Matheus Machado dos Santos	login
2024-11-08 19:55:58.901222	Felipe	login
2024-11-27 14:40:38.76604	Cleber	login
2024-11-08 13:07:20.698132	Matheus Machado dos Santos	login
2024-11-08 19:56:35.570458	Felipe	login
2024-11-08 13:07:21.192924	Matheus Machado dos Santos	login
2024-11-08 19:57:17.984407	Felipe	login
2024-11-08 13:07:39.823175	Matheus Machado dos Santos	login
2024-11-08 19:57:17.984407	Felipe	login
2024-11-08 13:07:40.216024	Matheus Machado dos Santos	login
2024-11-27 14:40:45.398942	Cleber	login
2024-11-11 11:20:44.028224	Cleber	login
2024-11-08 14:28:22.379405	Jonata Tyska	login
2024-11-11 11:21:04.933667	Cleber	login
2024-11-08 14:28:24.59354	Jonata Tyska	login
2024-11-27 14:40:56.698864	Cleber	login
2024-11-11 11:21:13.943801	Cleber	login
2024-11-27 14:41:04.917983	Cleber	login
2024-11-11 11:21:16.112374	Cleber	login
2024-11-11 11:21:20.278018	Cleber	login
2024-11-27 14:41:11.771083	Cleber	login
2024-11-11 11:21:37.266227	Cleber	login
2024-11-27 14:41:21.270322	Cleber	login
2024-11-11 11:21:40.746312	Cleber	login
2024-11-11 11:21:41.542961	Cleber	login
2024-11-11 11:21:42.769931	Cleber	login
2024-11-11 11:21:45.109599	Cleber	login
2024-11-13 20:28:59.03916	Jerusa Marchi	login
2024-11-13 20:31:09.965797	Jerusa Marchi	login
2024-11-27 14:41:30.794027	Cleber	login
2024-11-25 06:44:37.670167	Cleber	login
2024-11-25 06:44:55.609972	Cleber	login
2024-11-25 06:44:56.762282	Cleber	login
2024-11-08 19:42:28.933988	Felipe	login
2024-11-08 14:28:39.154355	Jonata Tyska	login
2024-11-26 16:34:21.636588	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 14:28:41.479696	Jonata Tyska	login
2024-11-08 19:42:39.961667	Felipe	login
2024-11-08 14:28:59.000936	Jonata Tyska	login
2024-11-26 16:34:21.636588	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 14:29:01.153613	Jonata Tyska	login
2024-11-08 19:42:55.961279	Felipe	login
2024-11-08 14:29:19.473254	Jonata Tyska	login
2024-11-26 16:34:31.654336	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 14:29:22.200278	Jonata Tyska	login
2024-11-08 19:43:06.239821	Felipe	login
2024-11-08 14:29:27.298924	Jonata Tyska	login
2024-11-26 16:34:33.193641	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 14:29:29.117752	Jonata Tyska	login
2024-11-08 19:43:09.473617	Felipe	login
2024-11-08 14:29:34.145088	Jonata Tyska	login
2024-11-25 06:43:43.322948	Cleber	login
2024-11-08 14:29:35.928198	Jonata Tyska	login
2024-11-08 19:43:12.930619	Felipe	login
2024-11-08 14:29:37.85071	Jonata Tyska	login
2024-11-25 06:44:54.878606	Cleber	login
2024-11-08 14:29:39.048386	Jonata Tyska	login
2024-11-08 19:43:19.031497	Felipe	login
2024-11-08 14:29:41.608295	Jonata Tyska	login
2024-11-25 06:44:56.202328	Cleber	login
2024-11-08 14:29:42.775618	Jonata Tyska	login
2024-11-08 19:43:37.185301	Felipe	login
2024-11-08 14:29:49.740187	Jonata Tyska	login
2024-11-26 16:34:33.193641	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 14:29:51.858488	Jonata Tyska	login
2024-11-08 19:44:38.547185	Felipe	login
2024-11-08 14:29:56.241106	Jonata Tyska	login
2024-11-08 19:45:30.44618	Felipe	login
2024-11-08 14:29:57.847616	Jonata Tyska	login
2024-11-25 06:45:00.782286	Cleber	login
2024-11-08 14:30:00.909433	Jonata Tyska	login
2024-11-08 19:45:59.981658	Felipe	login
2024-11-08 14:30:01.857947	Jonata Tyska	login
2024-11-26 16:34:33.193641	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 14:30:03.09061	Jonata Tyska	login
2024-11-08 19:46:06.236353	Felipe	login
2024-11-08 14:30:06.158863	Jonata Tyska	login
2024-11-25 06:45:12.114175	Cleber	login
2024-11-08 14:30:07.082395	Jonata Tyska	login
2024-11-08 19:46:11.905189	Felipe	login
2024-11-08 14:30:10.437078	Jonata Tyska	login
2024-11-08 19:46:31.714484	Felipe	login
2024-11-08 14:30:11.491627	Jonata Tyska	login
2024-11-08 19:46:45.530456	Felipe	login
2024-11-08 14:30:16.015106	Jonata Tyska	login
2024-11-08 19:47:27.851943	Felipe	login
2024-11-08 14:30:17.08621	Jonata Tyska	login
2024-11-08 19:48:13.775248	Felipe	login
2024-11-08 14:30:21.44223	Jonata Tyska	login
2024-11-08 19:48:17.422696	Felipe	login
2024-11-08 14:30:22.525174	Jonata Tyska	login
2024-11-08 19:48:28.944258	Felipe	login
2024-11-08 19:49:44.07881	Felipe	login
2024-11-08 15:20:24.980378	Felipe	login
2024-11-25 06:45:52.514833	Cleber	login
2024-11-08 15:20:25.384134	Felipe	login
2024-11-08 19:55:59.206699	Felipe	login
2024-11-08 15:23:22.134687	Felipe	login
2024-11-08 15:23:22.214555	Felipe	login
2024-11-08 15:23:37.793195	Felipe	login
2024-11-08 15:25:24.135939	Felipe	login
2024-11-26 16:34:33.193641	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 15:25:24.7271	Felipe	login
2024-11-08 19:56:36.572976	Felipe	login
2024-11-08 15:25:31.966722	Felipe	login
2024-11-08 19:57:45.21069	Felipe	login
2024-11-08 17:09:47.825954	Felipe	login
2024-11-11 11:20:41.553643	Cleber	login
2024-11-08 17:09:50.015124	Felipe	login
2024-11-25 06:47:42.281745	Cleber	login
2024-11-08 17:10:28.715761	Felipe	login
2024-11-08 17:10:37.953301	Felipe	login
2024-11-11 11:20:45.542528	Cleber	login
2024-11-08 17:10:38.400606	Felipe	login
2024-11-11 11:20:47.054324	Cleber	login
2024-11-08 17:10:43.388773	Felipe	login
2024-11-08 17:10:45.595637	Felipe	login
2024-11-08 17:10:51.695814	Felipe	login
2024-11-08 17:10:54.905934	Felipe	login
2024-11-11 11:20:47.097681	Cleber	login
2024-11-11 11:20:50.249961	Cleber	login
2024-11-11 11:20:55.38	Cleber	login
2024-11-11 11:20:55.423448	Cleber	login
2024-11-11 11:20:56.736776	Cleber	login
2024-11-11 11:20:59.249354	Cleber	login
2024-11-11 11:21:00.672525	Cleber	login
2024-11-11 11:21:07.425397	Cleber	login
2024-11-27 14:39:33.794471	Cleber	login
2024-11-11 11:21:14.364944	Cleber	login
2024-11-11 11:21:17.304071	Cleber	login
2024-11-27 14:39:35.668292	Cleber	login
2024-11-11 11:21:27.762331	Cleber	login
2024-11-26 11:15:52.794886	Andr├® W├╝st Zibetti	login
2024-11-11 11:21:37.588806	Cleber	login
2024-11-11 11:21:42.406478	Cleber	login
2024-11-11 11:21:43.711476	Cleber	login
2024-11-27 14:39:36.761084	Cleber	login
2024-11-13 20:29:41.0108	Jerusa Marchi	login
2024-11-13 20:31:17.483711	Jerusa Marchi	login
2024-11-13 20:31:30.825029	Jerusa Marchi	login
2024-10-29 00:47:44.029844	Cleber	login
2024-10-29 00:47:44.078005	Cleber	login
2024-10-23 19:42:22.524766	Luis	login
2024-10-29 00:47:44.512256	Cleber	login
2024-10-29 00:47:44.982915	Cleber	login
2024-10-29 00:47:45.627922	Cleber	login
2024-10-29 00:47:45.673544	Cleber	login
2024-10-29 00:47:46.581877	Cleber	login
2024-10-29 00:47:47.260114	Cleber	login
2024-11-04 20:12:17.388174	Matheus Machado dos Santos	login
2024-10-29 00:47:47.708275	Cleber	login
2024-11-04 20:12:18.539106	Matheus Machado dos Santos	login
2024-10-29 00:48:01.633269	Cleber	login
2024-11-04 20:12:19.711262	Matheus Machado dos Santos	login
2024-10-29 00:48:02.114628	Cleber	login
2024-10-23 20:01:55.189573	Luis	consulta_licitacao
2024-11-04 20:12:20.911142	Matheus Machado dos Santos	login
2024-10-29 00:48:14.289993	Cleber	login
2024-11-04 20:12:22.177164	Matheus Machado dos Santos	login
2024-10-29 00:48:23.224329	Cleber	login
2024-11-04 20:12:23.447622	Matheus Machado dos Santos	login
2024-10-29 00:48:23.525287	Cleber	login
2024-11-04 20:12:24.894071	Matheus Machado dos Santos	login
2024-10-29 00:48:47.537948	Cleber	login
2024-11-04 20:12:26.257122	Matheus Machado dos Santos	login
2024-10-29 00:48:47.917925	Cleber	login
2024-11-04 20:12:27.683046	Matheus Machado dos Santos	login
2024-10-25 21:54:56.115545	Felipe	login
2024-10-29 00:48:54.521465	Cleber	login
2024-10-25 21:54:56.682048	Felipe	login
2024-11-04 20:12:29.124872	Matheus Machado dos Santos	login
2024-10-29 00:48:54.980771	Cleber	login
2024-10-27 17:57:17.791628	Felipe	login
2024-11-04 20:12:30.591138	Matheus Machado dos Santos	login
2024-10-27 17:57:18.349543	Felipe	login
2024-10-29 00:49:42.777353	Cleber	login
2024-10-27 17:57:20.237537	Felipe	login
2024-10-27 17:57:20.237537	Felipe	login
2024-10-27 17:57:21.039052	Felipe	login
2024-10-27 17:57:21.477858	Felipe	login
2024-10-27 17:57:23.817292	Felipe	login
2024-10-27 17:57:27.425463	Felipe	login
2024-10-27 17:57:27.543697	Felipe	login
2024-10-27 17:57:27.968746	Felipe	login
2024-10-27 17:57:28.918074	Felipe	login
2024-10-27 17:57:31.921795	Felipe	login
2024-10-27 17:57:31.921795	Felipe	login
2024-10-27 17:57:33.238046	Felipe	login
2024-10-27 17:57:35.918624	Felipe	login
2024-10-27 17:57:35.918624	Felipe	login
2024-10-27 17:57:37.138044	Felipe	login
2024-11-04 20:12:32.173356	Matheus Machado dos Santos	login
2024-10-27 17:57:37.688216	Felipe	login
2024-10-29 00:49:43.192909	Cleber	login
2024-10-27 17:59:33.328336	Felipe	login
2024-10-27 17:59:33.347056	Felipe	login
2024-10-27 17:59:33.745264	Felipe	login
2024-10-27 17:59:34.131018	Felipe	login
2024-11-04 20:12:33.796666	Matheus Machado dos Santos	login
2024-10-28 11:42:28.979835	Matheus Machado dos Santos	login
2024-10-29 00:50:50.314867	Cleber	login
2024-10-28 11:42:29.784517	Matheus Machado dos Santos	login
2024-11-04 20:12:35.58561	Matheus Machado dos Santos	login
2024-10-29 00:50:50.903661	Cleber	login
2024-10-29 00:45:49.921683	Cleber	login
2024-11-04 20:12:37.530609	Matheus Machado dos Santos	login
2024-10-29 00:45:50.50388	Cleber	login
2024-10-29 00:54:09.776062	Cleber	login
2024-10-29 00:46:30.293008	Cleber	login
2024-10-29 00:46:30.293008	Cleber	login
2024-10-29 00:46:30.349758	Cleber	login
2024-10-29 00:46:30.81031	Cleber	login
2024-10-29 00:46:35.817262	Cleber	login
2024-10-29 00:46:35.861893	Cleber	login
2024-10-29 00:46:40.973138	Cleber	login
2024-11-04 20:12:39.339027	Matheus Machado dos Santos	login
2024-10-29 00:46:41.489917	Cleber	login
2024-10-29 00:54:10.386715	Cleber	login
2024-10-29 00:46:48.066148	Cleber	login
2024-11-04 20:12:41.221987	Matheus Machado dos Santos	login
2024-10-29 00:46:48.601782	Cleber	login
2024-10-29 00:54:11.580202	Cleber	login
2024-10-29 00:46:51.193842	Cleber	login
2024-11-04 20:12:43.281836	Matheus Machado dos Santos	login
2024-10-29 00:46:51.769146	Cleber	login
2024-10-29 00:54:12.168406	Cleber	login
2024-10-29 00:47:03.531009	Cleber	login
2024-11-04 20:12:45.125239	Matheus Machado dos Santos	login
2024-10-29 00:47:03.966902	Cleber	login
2024-10-29 00:54:23.540084	Cleber	login
2024-10-29 00:47:07.574678	Cleber	login
2024-11-04 20:12:47.019606	Matheus Machado dos Santos	login
2024-10-29 00:47:08.000802	Cleber	login
2024-10-29 00:54:23.995051	Cleber	login
2024-10-29 00:47:11.717892	Cleber	login
2024-11-04 20:12:48.931657	Matheus Machado dos Santos	login
2024-10-29 00:47:12.214775	Cleber	login
2024-10-29 00:54:32.047457	Cleber	login
2024-10-29 00:47:13.106076	Cleber	login
2024-11-04 20:12:50.919393	Matheus Machado dos Santos	login
2024-10-29 00:47:13.598281	Cleber	login
2024-10-29 00:54:32.455601	Cleber	login
2024-10-29 00:47:15.038247	Cleber	login
2024-11-04 20:12:52.976922	Matheus Machado dos Santos	login
2024-10-29 00:47:15.613793	Cleber	login
2024-10-29 00:55:37.071981	Cleber	login
2024-10-29 00:47:16.577409	Cleber	login
2024-10-29 00:55:37.121833	Cleber	login
2024-10-29 00:47:17.13108	Cleber	login
2024-10-29 00:55:37.530795	Cleber	login
2024-10-29 00:47:24.98242	Cleber	login
2024-10-29 00:55:38.030742	Cleber	login
2024-10-29 00:47:25.486817	Cleber	login
2024-10-29 00:55:44.127981	Cleber	login
2024-10-29 00:47:30.034924	Cleber	login
2024-11-04 20:12:55.100163	Matheus Machado dos Santos	login
2024-10-29 00:47:30.426638	Cleber	login
2024-10-29 00:55:44.575526	Cleber	login
2024-11-04 20:12:57.67147	Matheus Machado dos Santos	login
2024-10-29 00:56:12.527575	Cleber	login
2024-11-04 20:12:59.940611	Matheus Machado dos Santos	login
2024-10-29 00:56:13.059548	Cleber	login
2024-11-04 20:13:02.134331	Matheus Machado dos Santos	login
2024-10-29 00:56:38.499201	Cleber	login
2024-11-04 20:13:04.773289	Matheus Machado dos Santos	login
2024-10-29 00:56:38.991469	Cleber	login
2024-11-04 20:13:06.906897	Matheus Machado dos Santos	login
2024-10-29 00:58:14.216272	Cleber	login
2024-10-29 00:58:14.266148	Cleber	login
2024-10-29 00:58:14.674934	Cleber	login
2024-10-29 00:58:15.099205	Cleber	login
2024-10-29 00:58:18.987124	Cleber	login
2024-10-29 00:58:20.151661	Cleber	login
2024-10-29 00:58:20.191189	Cleber	login
2024-10-29 00:58:20.687124	Cleber	login
2024-10-29 00:58:20.763296	Cleber	login
2024-11-04 20:13:09.153212	Matheus Machado dos Santos	login
2024-10-29 00:58:21.223648	Cleber	login
2024-10-29 00:58:22.239881	Cleber	login
2024-10-29 00:58:22.691236	Cleber	login
2024-10-29 00:58:23.131593	Cleber	login
2024-10-29 00:58:23.984166	Cleber	login
2024-10-29 00:58:24.489627	Cleber	login
2024-10-29 00:58:27.128706	Cleber	login
2024-10-29 00:58:27.643735	Cleber	login
2024-10-29 00:58:28.14094	Cleber	login
2024-10-29 00:58:29.183668	Cleber	login
2024-10-29 00:58:29.183668	Cleber	login
2024-10-29 00:58:29.633821	Cleber	login
2024-10-29 00:58:30.058387	Cleber	login
2024-10-29 00:58:33.210572	Cleber	login
2024-10-29 00:58:34.092087	Cleber	login
2024-10-29 00:58:34.131091	Cleber	login
2024-10-29 00:58:34.591346	Cleber	login
2024-10-29 00:58:35.32378	Cleber	login
2024-10-29 00:58:35.32378	Cleber	login
2024-10-29 00:58:35.424338	Cleber	login
2024-11-08 17:11:48.676489	Felipe	login
2024-11-08 17:11:50.38406	Felipe	login
2024-11-22 22:03:55.28641	Felipe	login
2025-02-21 23:56:15.970004	Jos├® Eduardo Medeiros Jochem	login
2024-11-25 19:26:26.440485	Andr├® Teixeira Milioli	login
2025-02-21 23:56:16.6322	Jos├® Eduardo Medeiros Jochem	login
2024-11-25 19:26:49.885787	Andr├® Teixeira Milioli	login
2025-02-21 23:56:17.737203	Jos├® Eduardo Medeiros Jochem	login
2024-11-25 19:27:56.685721	Andr├® Teixeira Milioli	login
2024-11-08 19:42:39.395348	Felipe	login
2024-11-25 19:29:13.122649	Andr├® Teixeira Milioli	login
2024-11-08 19:42:47.883621	Felipe	login
2025-02-21 23:56:25.767278	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:43:05.555148	Felipe	login
2024-11-25 19:29:47.918084	Andr├® Teixeira Milioli	login
2024-11-08 19:43:08.326096	Felipe	login
2025-02-21 23:56:25.833814	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:43:12.601492	Felipe	login
2024-11-26 14:30:36.165734	Felipe	login
2024-11-08 19:43:14.514364	Felipe	login
2024-11-26 14:30:36.165734	Felipe	login
2024-11-08 19:43:36.727884	Felipe	login
2024-11-26 14:30:36.165734	Felipe	login
2024-11-08 19:44:09.469283	Felipe	login
2024-11-08 19:44:55.573145	Felipe	login
2024-11-26 14:30:36.165734	Felipe	login
2024-11-08 19:45:59.665427	Felipe	login
2024-11-26 14:30:36.165734	Felipe	login
2024-11-08 19:46:02.629797	Felipe	login
2024-11-26 14:30:36.165734	Felipe	login
2024-11-08 19:46:11.60669	Felipe	login
2024-11-26 14:33:18.768992	Felipe	login
2024-11-08 19:46:30.654025	Felipe	login
2024-11-04 20:13:24.267505	Matheus Machado dos Santos	login
2024-11-04 20:13:24.755947	Matheus Machado dos Santos	login
2024-11-04 20:17:21.469683	Matheus Machado dos Santos	login
2024-11-04 20:17:29.505869	Matheus Machado dos Santos	login
2024-11-04 20:17:30.199942	Matheus Machado dos Santos	login
2024-11-04 20:17:37.716778	Matheus Machado dos Santos	login
2024-11-04 20:17:37.834183	Matheus Machado dos Santos	login
2024-11-05 13:29:48.089008	Breno	login
2024-11-05 13:29:49.794377	Breno	login
2024-11-05 13:30:15.722052	Breno	login
2024-11-05 13:30:15.920928	Breno	login
2024-11-05 13:30:23.528889	Breno	login
2024-11-05 13:30:23.528889	Breno	login
2024-11-05 13:30:23.547513	Breno	login
2024-11-05 13:33:31.617735	Breno	login
2024-11-05 13:33:31.960617	Breno	login
2024-11-05 13:33:38.949968	Breno	login
2024-11-05 13:34:38.762943	Breno	login
2025-02-26 01:58:16.881137	Matheus Machado dos Santos	login
2025-02-26 01:58:23.589707	Matheus Machado dos Santos	login
2025-02-26 01:58:58.024108	Matheus Machado dos Santos	login
2025-02-26 01:59:31.635848	Matheus Machado dos Santos	login
2025-02-26 02:02:25.846936	Matheus Machado dos Santos	login
2025-02-26 02:05:08.480273	Matheus Machado dos Santos	login
2024-11-05 13:34:39.467486	Breno	login
2025-02-26 02:12:16.525505	Felipe	login
2025-02-26 02:12:36.346747	Felipe	login
2025-02-26 02:12:37.774184	Matheus Machado dos Santos	login
2025-02-26 02:12:37.774184	Matheus Machado dos Santos	login
2025-02-26 02:12:37.824662	Matheus Machado dos Santos	login
2025-02-26 02:12:37.896632	Matheus Machado dos Santos	login
2025-02-26 02:13:18.589669	Felipe	login
2025-02-26 02:13:37.500129	Felipe	login
2025-02-26 02:13:52.807195	Felipe	login
2025-02-26 02:14:15.516622	Felipe	login
2025-02-26 02:14:15.516622	Felipe	login
2025-02-26 02:14:21.232397	Felipe	login
2025-02-26 02:14:32.193259	Felipe	login
2025-02-26 02:15:10.852635	Felipe	login
2025-02-26 02:16:44.656161	Matheus Machado dos Santos	login
2025-02-26 02:16:46.859941	Matheus Machado dos Santos	login
2025-02-26 02:18:14.01554	Matheus Machado dos Santos	login
2024-11-05 13:34:39.467486	Breno	login
2025-02-26 02:18:46.788644	Felipe	login
2025-02-26 02:19:29.596724	Matheus Machado dos Santos	login
2025-02-26 02:20:37.725824	Matheus Machado dos Santos	login
2025-02-26 02:20:37.725824	Matheus Machado dos Santos	login
2025-02-26 02:20:37.776462	Matheus Machado dos Santos	login
2025-02-26 02:20:37.854853	Matheus Machado dos Santos	login
2025-02-26 02:21:29.544587	Felipe	login
2025-02-26 02:21:42.264801	Felipe	login
2024-11-05 13:35:48.288057	Breno	login
2024-11-05 13:36:44.793498	Breno	login
2024-11-05 13:36:45.29857	Breno	login
2024-11-05 13:37:07.760421	Breno	login
2024-11-05 13:37:07.997393	Breno	login
2024-11-05 13:37:10.360668	Breno	login
2024-11-05 13:37:10.360668	Breno	login
2024-11-05 13:37:10.369704	Breno	login
2024-11-05 13:37:11.183457	Breno	login
2024-11-08 19:46:44.392467	Felipe	login
2024-11-08 19:47:26.863389	Felipe	login
2024-11-05 14:21:49.792619	Breno	login
2024-11-05 14:23:03.388485	Breno	login
2024-11-05 14:23:07.510759	Breno	login
2024-11-08 19:48:01.586443	Felipe	login
2024-11-08 19:48:01.663936	Felipe	login
2024-11-05 17:02:24.4858	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:49:46.245654	Felipe	login
2024-11-05 17:07:33.37626	Jos├® Eduardo Medeiros Jochem	login
2024-11-08 19:55:44.878438	Felipe	login
2024-11-05 17:07:38.338097	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:38.338097	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:38.338097	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:39.449864	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:40.390239	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:42.144318	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:43.143156	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:41:19.568422	Cleber	login
2024-11-05 17:07:43.157815	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:44.003836	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:07:44.36983	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:08.533065	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:15.372974	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:18.498758	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:18.498758	Jos├® Eduardo Medeiros Jochem	login
2024-11-13 20:31:40.905493	Jerusa Marchi	login
2024-11-05 17:13:25.848106	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:15:38.421316	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:16:22.741573	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:16:22.741573	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:16:22.799297	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:21:32.306893	Felipe	login
2024-11-05 17:21:38.570573	Felipe	login
2024-11-05 17:21:38.570573	Felipe	login
2024-11-05 17:21:39.455662	Felipe	login
2024-11-05 17:21:45.68713	Felipe	login
2024-11-05 17:21:45.68713	Felipe	login
2024-11-05 17:22:16.854559	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:22:16.854559	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:22:16.926034	Jos├® Eduardo Medeiros Jochem	login
2024-11-26 14:34:37.033701	Felipe	login
2024-11-08 19:56:10.449869	Felipe	login
2024-11-08 19:56:54.318318	Felipe	login
2024-11-08 19:57:46.975964	Felipe	login
2025-02-24 17:30:31.271327	Felipe	login
2025-02-24 17:30:32.188009	Felipe	login
2025-02-24 17:30:34.840552	Felipe	login
2025-02-24 17:30:34.961008	Felipe	login
2025-02-24 17:30:35.035104	Felipe	login
2024-11-26 14:34:37.033701	Felipe	login
2024-11-11 11:20:45.498526	Cleber	login
2024-11-11 11:20:45.498526	Cleber	login
2024-11-11 11:21:01.489098	Cleber	login
2024-11-11 11:21:07.860767	Cleber	login
2024-11-26 14:34:37.033701	Felipe	login
2024-11-11 11:21:16.049837	Cleber	login
2024-11-11 11:21:16.049837	Cleber	login
2025-02-24 17:33:05.693366	Myllena	login
2025-02-24 17:33:06.384274	Myllena	login
2024-11-11 11:21:19.937925	Cleber	login
2024-11-26 14:34:37.033701	Felipe	login
2024-11-11 11:21:28.088783	Cleber	login
2024-11-26 14:34:37.033701	Felipe	login
2024-11-11 11:21:40.689732	Cleber	login
2024-11-26 14:34:37.033701	Felipe	login
2024-11-26 14:35:52.615339	Felipe	login
2024-11-26 14:37:06.95997	Felipe	login
2024-11-04 20:13:11.876283	Matheus Machado dos Santos	login
2024-11-04 20:13:14.481513	Matheus Machado dos Santos	login
2024-11-04 20:13:16.741088	Matheus Machado dos Santos	login
2024-11-04 20:13:20.441263	Matheus Machado dos Santos	login
2024-10-29 00:58:35.376751	Cleber	login
2024-10-29 00:58:35.803262	Cleber	login
2024-10-29 00:58:35.803262	Cleber	login
2024-10-29 00:58:35.839323	Cleber	login
2024-10-29 00:58:36.311478	Cleber	login
2024-10-29 00:58:36.443495	Cleber	login
2024-10-29 00:58:36.839295	Cleber	login
2024-10-29 00:58:44.296776	Cleber	login
2025-02-26 01:56:56.890179	Matheus Machado dos Santos	login
2025-02-26 01:56:58.364316	Matheus Machado dos Santos	login
2025-02-26 01:57:37.115551	Matheus Machado dos Santos	login
2024-11-22 22:03:56.807555	Felipe	login
2025-02-26 02:05:55.530969	Jos├® Eduardo Medeiros Jochem	login
2025-02-26 02:05:59.694941	Jos├® Eduardo Medeiros Jochem	login
2025-02-26 02:06:14.45562	Jos├® Eduardo Medeiros Jochem	login
2025-02-26 02:09:42.004361	Matheus Machado dos Santos	login
2024-10-29 00:58:44.756559	Cleber	login
2025-02-26 02:13:41.099903	Felipe	login
2025-02-26 02:14:22.050864	Felipe	login
2025-02-26 02:15:22.639403	Felipe	login
2025-02-26 02:16:52.402487	Matheus Machado dos Santos	login
2025-02-26 02:16:54.959191	Matheus Machado dos Santos	login
2025-02-26 02:18:46.674493	Felipe	login
2025-02-26 02:18:51.964489	Matheus Machado dos Santos	login
2025-02-26 02:18:56.555728	Matheus Machado dos Santos	login
2024-11-08 17:25:16.284595	Felipe	login
2025-02-26 02:21:42.024499	Felipe	login
2024-10-29 00:58:48.099759	Cleber	login
2024-11-08 17:25:17.216058	Felipe	login
2024-10-29 00:58:48.576394	Cleber	login
2024-11-08 17:25:28.289184	Felipe	login
2024-10-29 00:58:49.636636	Cleber	login
2024-11-08 17:25:28.511435	Felipe	login
2024-10-29 00:58:50.1358	Cleber	login
2024-11-08 17:25:42.862516	Felipe	login
2024-10-29 01:01:07.347577	Cleber	login
2024-10-29 01:01:07.401661	Cleber	login
2024-10-29 01:01:07.791115	Cleber	login
2024-10-29 01:01:08.198244	Cleber	login
2024-10-29 01:01:09.138573	Cleber	login
2024-11-08 17:25:43.536595	Felipe	login
2024-10-29 01:01:09.542699	Cleber	login
2024-11-08 17:25:45.104878	Felipe	login
2024-10-29 01:01:11.76943	Cleber	login
2024-10-29 01:01:11.828252	Cleber	login
2024-10-29 01:01:12.209537	Cleber	login
2024-10-29 01:01:12.712967	Cleber	login
2024-10-29 01:01:13.533044	Cleber	login
2024-11-08 17:25:59.721365	Felipe	login
2024-10-29 01:01:13.976248	Cleber	login
2024-11-05 14:20:25.606025	Breno	login
2024-10-29 01:01:40.102665	Cleber	login
2024-11-05 14:20:44.072008	Breno	login
2024-10-29 01:01:40.588397	Cleber	login
2024-11-05 14:20:45.569113	Breno	login
2024-11-05 14:23:04.160136	Breno	login
2024-11-04 02:10:09.947089	Matheus Machado dos Santos	login
2024-11-08 17:26:01.362437	Felipe	login
2024-11-04 02:10:11.796291	Matheus Machado dos Santos	login
2024-11-05 14:23:18.195431	Breno	login
2024-11-05 17:07:42.209332	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 15:26:51.660851	Felipe	login
2024-11-08 17:26:06.186011	Felipe	login
2024-11-04 15:26:53.565035	Felipe	login
2024-11-08 17:26:09.114766	Felipe	login
2024-11-04 15:38:15.19246	Felipe	login
2024-11-08 17:26:50.000031	Felipe	login
2024-11-04 15:38:15.568775	Felipe	login
2024-11-05 17:13:25.840802	Jos├® Eduardo Medeiros Jochem	login
2024-11-05 17:13:25.840802	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 17:58:42.852073	Breno	login
2024-11-04 17:58:42.852073	Breno	login
2024-11-04 17:58:52.769728	Breno	login
2024-11-04 17:58:52.769728	Breno	login
2024-11-04 17:58:57.401039	Breno	login
2024-11-04 17:58:57.401039	Breno	login
2024-11-04 17:59:25.431168	Breno	login
2024-11-04 17:59:25.431168	Breno	login
2024-11-04 17:59:27.760606	Breno	login
2024-11-04 17:59:41.207967	Breno	login
2024-11-05 17:13:25.853274	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 17:59:43.521388	Breno	login
2024-11-05 17:13:25.853274	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 18:00:35.478505	Breno	login
2024-11-05 17:13:25.853274	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 18:00:36.235015	Breno	login
2024-11-05 17:15:38.410745	Jos├® Eduardo Medeiros Jochem	login
2024-11-04 18:00:44.240241	Breno	login
2024-11-04 18:00:44.240241	Breno	login
2024-11-04 18:00:44.313654	Breno	login
2024-11-04 18:00:45.801406	Breno	login
2024-11-04 18:05:59.397035	Breno	login
2024-11-04 18:06:03.422681	Breno	login
2024-11-04 18:06:09.348788	Breno	login
2024-11-04 18:06:09.348788	Breno	login
2024-11-04 18:06:42.972466	Breno	login
2024-11-04 18:06:45.704404	Breno	login
2024-11-26 11:17:25.842681	Andr├® W├╝st Zibetti	login
2024-11-13 20:32:59.049348	Jerusa Marchi	login
2024-11-26 11:17:27.618483	Andr├® W├╝st Zibetti	login
2024-11-27 14:39:38.248108	Cleber	login
2024-11-14 13:49:41.944021	Jonata Tyska	login
2024-11-26 11:17:55.423988	Andr├® W├╝st Zibetti	login
2024-11-14 13:50:02.174516	Jonata Tyska	login
2024-11-14 13:51:27.17372	Jonata Tyska	login
2024-11-27 14:39:40.223057	Cleber	login
2024-11-14 13:51:58.619826	Jonata Tyska	login
2024-11-27 14:39:41.179621	Cleber	login
2024-11-27 14:39:42.472768	Cleber	login
2024-11-18 17:20:41.757758	Felipe	login
2024-11-18 17:20:41.757758	Felipe	login
2024-11-27 14:39:43.581651	Cleber	login
2024-11-19 12:37:46.708413	Jonata Tyska	login
2024-11-27 14:39:46.483688	Cleber	login
2024-11-19 12:38:31.199422	Jonata Tyska	login
2024-11-27 14:39:48.598313	Cleber	login
2024-11-19 12:39:48.32016	Jonata Tyska	login
2024-11-27 14:39:50.888199	Cleber	login
2024-11-19 12:40:54.743975	Jonata Tyska	login
2024-11-19 12:42:34.565805	Jonata Tyska	login
2024-11-19 13:41:35.302434	Jonata Tyska	login
2024-11-27 14:39:52.017704	Cleber	login
2024-11-19 13:42:09.795696	Jonata Tyska	login
2024-11-19 13:47:17.678691	Jonata Tyska	login
2024-11-19 13:47:18.895142	Jonata Tyska	login
2024-11-27 14:39:55.779626	Cleber	login
2024-11-27 14:39:59.023717	Cleber	login
2024-11-27 14:39:59.737244	Cleber	login
2024-11-27 14:40:04.064684	Cleber	login
2024-11-27 14:40:07.851347	Cleber	login
2024-11-27 14:40:09.293188	Cleber	login
2024-11-27 14:40:10.396025	Cleber	login
2024-11-27 14:40:11.562671	Cleber	login
2024-11-27 14:40:14.745664	Cleber	login
2024-11-27 14:40:15.963962	Cleber	login
2024-11-19 20:49:51.995331	Andr├® Teixeira Milioli	login
2024-11-27 14:40:22.498659	Cleber	login
2024-11-27 14:40:30.97341	Cleber	login
2024-11-19 20:52:35.553602	Andr├® Teixeira Milioli	login
2024-11-19 20:53:49.408813	Andr├® Teixeira Milioli	login
2024-11-19 20:54:18.716383	Andr├® Teixeira Milioli	login
2024-11-27 14:40:41.411685	Cleber	login
2024-11-27 14:40:51.26729	Cleber	login
2024-11-27 14:40:59.216355	Cleber	login
2024-11-25 06:44:51.614879	Cleber	login
2024-11-25 06:44:52.710087	Cleber	login
2024-11-25 06:44:57.422701	Cleber	login
2024-11-25 06:44:59.890686	Cleber	login
2024-11-25 06:45:11.282254	Cleber	login
2024-11-25 06:45:51.602276	Cleber	login
2024-11-27 14:41:07.698874	Cleber	login
2024-11-25 06:47:41.430397	Cleber	login
2024-11-26 11:15:37.845634	Andr├® W├╝st Zibetti	login
2024-11-26 11:15:37.845634	Andr├® W├╝st Zibetti	login
2024-11-26 11:16:27.248836	Andr├® W├╝st Zibetti	login
2024-11-26 11:16:28.209362	Andr├® W├╝st Zibetti	login
2024-11-26 11:16:29.274981	Andr├® W├╝st Zibetti	login
2024-11-26 11:17:25.832692	Andr├® W├╝st Zibetti	login
2024-11-26 11:17:46.634948	Andr├® W├╝st Zibetti	login
2024-11-26 11:17:58.917949	Andr├® W├╝st Zibetti	login
2024-11-27 14:41:16.377971	Cleber	login
2024-11-27 14:41:25.497271	Cleber	login
2024-11-27 14:41:33.884768	Cleber	login
2024-11-27 14:41:41.891862	Cleber	login
2024-11-27 14:41:51.542489	Cleber	login
2024-11-27 14:42:05.048783	Cleber	login
2024-11-27 14:42:11.827353	Cleber	login
2024-11-27 14:42:19.070324	Cleber	login
2024-11-27 14:42:26.854764	Cleber	login
2024-11-27 14:42:34.863912	Cleber	login
2024-11-27 14:42:44.091685	Cleber	login
2024-11-27 14:42:53.481996	Cleber	login
2024-11-27 14:43:08.131662	Cleber	login
2024-11-27 14:43:20.091796	Cleber	login
2024-11-27 14:43:31.060824	Cleber	login
2024-11-27 14:43:41.668874	Cleber	login
2024-11-27 14:43:52.061501	Cleber	login
2024-11-27 14:44:04.025446	Cleber	login
2024-11-27 14:44:13.613477	Cleber	login
2024-11-27 14:44:23.388804	Cleber	login
2024-12-02 03:40:10.075844	Cleber	login
2024-12-02 03:41:11.757649	Cleber	login
2024-12-02 03:41:16.757269	Cleber	login
2024-12-04 02:58:54.138038	Cleber	login
2024-12-04 02:59:02.558678	Cleber	login
2024-12-04 02:59:15.716493	Cleber	login
2024-12-04 02:59:23.59915	Cleber	login
2024-12-04 02:59:32.778235	Cleber	login
2024-12-04 03:00:19.555771	Cleber	login
2024-12-04 03:02:30.024939	Cleber	login
2024-12-10 13:07:55.649477	M├írcio Castro	login
2024-12-10 13:08:51.19196	M├írcio Castro	login
2024-12-10 13:08:58.903618	M├írcio Castro	login
2024-12-10 13:09:54.859068	Jonata Tyska	login
2025-04-04 18:03:36.437605	Matheus Machado dos Santos	login
2024-11-19 20:49:30.431201	Andr├® Teixeira Milioli	login
2024-11-19 20:52:14.757591	Andr├® Teixeira Milioli	login
2024-11-19 20:52:58.269166	Andr├® Teixeira Milioli	login
2024-11-27 14:40:16.741233	Cleber	login
2024-11-27 14:40:17.579435	Cleber	login
2024-11-27 14:40:20.817361	Cleber	login
2024-11-27 14:40:24.037819	Cleber	login
2024-11-27 14:40:25.839506	Cleber	login
2024-11-27 14:40:29.606062	Cleber	login
2024-11-27 14:40:33.787139	Cleber	login
2024-11-25 06:43:45.726472	Cleber	login
2024-11-25 06:44:57.857806	Cleber	login
2024-11-25 06:45:08.918625	Cleber	login
2024-11-25 06:45:50.802749	Cleber	login
2024-11-25 06:47:35.481647	Cleber	login
2024-11-25 06:51:33.834399	Cleber	login
2024-11-26 11:16:23.236297	Andr├® W├╝st Zibetti	login
2024-11-26 11:17:46.250932	Andr├® W├╝st Zibetti	login
2024-11-26 11:17:58.553438	Andr├® W├╝st Zibetti	login
2024-11-27 14:40:36.035296	Cleber	login
2024-11-27 14:40:40.600318	Cleber	login
2024-11-27 14:40:43.445877	Cleber	login
2024-11-27 14:40:44.381832	Cleber	login
2024-11-27 14:40:49.696943	Cleber	login
2024-11-27 14:40:53.045069	Cleber	login
2024-11-27 14:40:55.294892	Cleber	login
2024-11-27 14:40:58.390974	Cleber	login
2024-11-27 14:41:00.399607	Cleber	login
2024-11-27 14:41:02.658984	Cleber	login
2024-11-27 14:41:06.827075	Cleber	login
2024-11-27 14:41:08.72666	Cleber	login
2024-11-27 14:41:10.4505	Cleber	login
2024-11-27 14:41:13.691147	Cleber	login
2024-11-27 14:41:18.252122	Cleber	login
2024-11-27 14:41:23.24354	Cleber	login
2024-11-27 14:41:28.140076	Cleber	login
2024-11-27 14:41:29.776686	Cleber	login
2024-11-27 14:41:32.731262	Cleber	login
2024-11-27 14:41:35.499817	Cleber	login
2024-11-27 14:41:37.093526	Cleber	login
2024-11-27 14:41:39.26381	Cleber	login
2024-11-27 14:41:40.567744	Cleber	login
2024-11-27 14:41:43.973334	Cleber	login
2024-11-27 14:41:45.602172	Cleber	login
2024-11-27 14:41:47.485346	Cleber	login
2024-11-27 14:41:49.195184	Cleber	login
2024-11-27 14:41:58.640614	Cleber	login
2024-11-27 14:41:59.91696	Cleber	login
2024-11-27 14:42:01.663872	Cleber	login
2024-11-27 14:42:03.342837	Cleber	login
2024-11-27 14:42:06.289539	Cleber	login
2024-11-27 14:42:07.471667	Cleber	login
2024-11-27 14:42:09.673642	Cleber	login
2024-11-27 14:42:10.808059	Cleber	login
2024-11-27 14:42:14.191114	Cleber	login
2024-11-27 14:42:15.587276	Cleber	login
2024-11-27 14:42:16.6825	Cleber	login
2024-11-27 14:42:18.071777	Cleber	login
2024-11-27 14:42:20.180338	Cleber	login
2024-11-27 14:42:22.38604	Cleber	login
2024-11-27 14:42:24.330468	Cleber	login
2024-11-27 14:42:25.853139	Cleber	login
2024-11-27 14:42:28.161083	Cleber	login
2024-11-27 14:42:29.80033	Cleber	login
2024-11-27 14:42:31.212656	Cleber	login
2024-11-27 14:42:33.531716	Cleber	login
2024-11-27 14:42:35.953343	Cleber	login
2024-11-27 14:42:38.056878	Cleber	login
2024-11-27 14:42:39.922771	Cleber	login
2024-11-27 14:42:41.95743	Cleber	login
2024-11-27 14:42:45.226133	Cleber	login
2024-11-27 14:42:46.705084	Cleber	login
2024-11-27 14:42:48.456903	Cleber	login
2024-11-27 14:42:51.54009	Cleber	login
2024-11-27 14:42:54.653042	Cleber	login
2024-11-27 14:42:56.439709	Cleber	login
2024-11-27 14:42:59.653768	Cleber	login
2024-11-27 14:43:00.784472	Cleber	login
2024-11-27 14:43:09.589808	Cleber	login
2024-11-27 14:43:11.812527	Cleber	login
2024-11-27 14:43:13.962906	Cleber	login
2024-11-27 14:43:16.469423	Cleber	login
2024-11-27 14:43:21.638908	Cleber	login
2024-11-27 14:43:24.48939	Cleber	login
2024-11-27 14:43:26.872357	Cleber	login
2024-11-27 14:43:29.506525	Cleber	login
2024-11-27 14:43:33.797724	Cleber	login
2024-11-27 14:43:35.141764	Cleber	login
2024-11-27 14:43:37.954306	Cleber	login
2024-11-27 14:43:39.752412	Cleber	login
2024-11-27 14:43:44.545805	Cleber	login
2024-11-27 14:43:46.436018	Cleber	login
2024-11-27 14:43:48.364253	Cleber	login
2024-11-27 14:43:50.694267	Cleber	login
2024-11-27 14:43:57.047372	Cleber	login
2024-11-27 14:43:58.259768	Cleber	login
2024-11-27 14:44:00.930882	Cleber	login
2024-11-27 14:44:02.23881	Cleber	login
2024-11-27 14:44:06.034	Cleber	login
2024-11-27 14:44:09.057375	Cleber	login
2024-11-27 14:44:10.535056	Cleber	login
2024-11-27 14:44:11.983101	Cleber	login
2024-11-27 14:44:15.450066	Cleber	login
2024-11-27 14:44:18.108624	Cleber	login
2024-11-27 14:44:19.620169	Cleber	login
2024-11-27 14:44:21.209373	Cleber	login
2024-11-27 14:44:26.218024	Cleber	login
2024-12-02 03:41:17.35373	Cleber	login
2025-02-24 17:35:26.641503	Myllena	login
2025-02-24 17:35:26.686986	Myllena	login
2025-02-24 17:35:26.748228	Myllena	login
2025-02-24 17:35:35.610522	Myllena	login
2025-02-24 17:35:36.281763	Myllena	login
2025-02-24 17:35:38.021622	Myllena	login
2025-02-24 17:35:38.049361	Myllena	login
2025-02-24 17:35:38.105759	Myllena	login
2024-12-04 03:00:09.969015	Cleber	login
2024-12-04 03:00:23.182451	Cleber	login
2024-12-10 13:08:00.828504	M├írcio Castro	login
2024-12-10 13:08:52.368379	M├írcio Castro	login
2024-12-10 13:11:14.57491	Jonata Tyska	login
2024-11-27 14:44:28.306072	Cleber	login
2024-11-19 20:50:04.570588	Andr├® Teixeira Milioli	login
2024-11-19 20:50:47.840224	Andr├® Teixeira Milioli	login
2024-11-27 14:44:29.724848	Cleber	login
2024-11-19 20:52:36.57159	Andr├® Teixeira Milioli	login
2024-11-19 20:53:50.462228	Andr├® Teixeira Milioli	login
2024-11-19 20:54:20.092801	Andr├® Teixeira Milioli	login
2024-11-27 14:44:31.391038	Cleber	login
2024-11-27 14:44:33.45701	Cleber	login
2024-11-27 14:44:36.26454	Cleber	login
2024-11-27 14:44:38.158869	Cleber	login
2024-11-27 14:44:39.780797	Cleber	login
2024-11-25 06:44:51.825821	Cleber	login
2024-11-25 06:45:08.491096	Cleber	login
2024-11-25 06:45:50.022525	Cleber	login
2024-11-25 06:47:35.045643	Cleber	login
2024-11-25 06:51:33.350363	Cleber	login
2024-11-27 14:44:41.975833	Cleber	login
2024-11-26 13:26:05.406624	Jonata Tyska	login
2024-11-26 13:26:50.442323	Jonata Tyska	login
2024-11-27 14:44:43.68032	Cleber	login
2024-11-27 14:44:45.620619	Cleber	login
2024-11-27 14:44:50.684069	Cleber	login
2024-11-27 14:44:52.202081	Cleber	login
2024-11-27 14:44:54.347695	Cleber	login
2024-11-27 14:44:56.759891	Cleber	login
2024-11-27 14:44:58.857911	Cleber	login
2024-11-27 14:45:00.795205	Cleber	login
2024-11-27 14:45:03.335698	Cleber	login
2024-11-27 14:45:05.430399	Cleber	login
2024-11-27 14:45:08.452889	Cleber	login
2024-11-27 14:45:11.7377	Cleber	login
2024-11-27 14:45:14.949856	Cleber	login
2024-11-27 14:45:17.757009	Cleber	login
2024-11-27 14:45:21.555863	Cleber	login
2024-11-27 14:45:23.365013	Cleber	login
2024-11-27 14:45:26.177614	Cleber	login
2024-11-27 14:45:30.670085	Cleber	login
2024-11-27 14:45:33.058331	Cleber	login
2024-11-27 14:45:35.66944	Cleber	login
2024-11-27 14:45:38.86493	Cleber	login
2024-11-27 14:45:41.303541	Cleber	login
2024-11-27 14:45:44.702259	Cleber	login
2024-11-27 14:45:47.500444	Cleber	login
2024-11-27 14:45:50.265353	Cleber	login
2024-11-27 14:45:53.064017	Cleber	login
2024-11-27 14:45:55.67286	Cleber	login
2024-11-27 14:45:58.312436	Cleber	login
2024-11-27 14:46:01.5422	Cleber	login
2024-11-27 14:46:04.678188	Cleber	login
2024-11-27 14:46:06.905244	Cleber	login
2024-11-27 14:46:10.200709	Cleber	login
2024-11-27 14:46:14.298744	Cleber	login
2024-11-27 14:46:18.083695	Cleber	login
2024-11-27 14:46:20.690824	Cleber	login
2024-11-27 14:46:23.76314	Cleber	login
2024-11-27 14:46:26.65961	Cleber	login
2024-11-27 14:46:30.175682	Cleber	login
2024-11-27 14:46:53.57348	Cleber	login
2024-11-27 14:46:55.811148	Cleber	login
2024-11-27 14:46:57.893631	Cleber	login
2024-11-27 14:47:00.512156	Cleber	login
2024-11-27 14:47:03.427633	Cleber	login
2024-11-27 14:47:05.802908	Cleber	login
2024-11-27 14:47:09.519818	Cleber	login
2024-11-27 14:47:30.88692	Cleber	login
2024-11-27 14:47:35.515825	Cleber	login
2024-11-27 14:47:37.59022	Cleber	login
2024-11-27 14:47:40.976956	Cleber	login
2024-11-27 14:48:07.489273	Cleber	login
2024-11-27 14:48:10.760665	Cleber	login
2024-11-27 14:48:13.843649	Cleber	login
2024-11-27 14:48:16.792033	Cleber	login
2024-11-27 14:48:20.222341	Cleber	login
2024-11-27 14:48:24.283623	Cleber	login
2024-11-27 14:48:27.282448	Cleber	login
2024-11-27 14:48:30.011713	Cleber	login
2024-11-27 14:48:32.721384	Cleber	login
2024-11-27 14:48:35.413386	Cleber	login
2024-11-27 14:48:41.269773	Cleber	login
2024-11-27 14:48:44.130696	Cleber	login
2024-11-27 14:48:49.030127	Cleber	login
2024-11-27 14:48:51.387292	Cleber	login
2024-11-27 14:48:54.237523	Cleber	login
2024-11-27 14:48:57.485829	Cleber	login
2024-11-27 14:49:00.151153	Cleber	login
2024-11-27 14:49:04.163293	Cleber	login
2024-11-27 14:49:07.736753	Cleber	login
2024-11-27 14:49:10.318	Cleber	login
2024-11-27 14:49:12.701845	Cleber	login
2024-11-27 14:49:15.973031	Cleber	login
2024-11-27 14:49:18.782051	Cleber	login
2024-11-27 14:49:21.786182	Cleber	login
2024-11-27 14:49:24.762486	Cleber	login
2024-11-27 14:49:28.333424	Cleber	login
2024-11-27 14:49:31.232739	Cleber	login
2024-11-27 14:49:34.779607	Cleber	login
2024-11-27 14:49:39.550773	Cleber	login
2024-11-27 14:49:41.769146	Cleber	login
2024-11-27 14:49:44.476231	Cleber	login
2024-11-27 14:49:47.489934	Cleber	login
2024-11-27 14:49:50.647274	Cleber	login
2024-11-27 14:49:53.717275	Cleber	login
2024-11-27 14:49:56.676115	Cleber	login
2024-11-27 14:49:59.718088	Cleber	login
2024-11-27 14:50:02.841386	Cleber	login
2024-11-27 14:50:05.793612	Cleber	login
2024-11-27 14:50:08.911884	Cleber	login
2024-11-27 14:50:12.714514	Cleber	login
2024-11-27 14:50:16.182958	Cleber	login
2024-11-27 14:50:19.941503	Cleber	login
2024-11-27 14:50:22.729209	Cleber	login
2024-11-27 14:50:26.333869	Cleber	login
2024-11-27 14:50:29.575613	Cleber	login
2024-11-27 14:50:32.653785	Cleber	login
2024-11-27 14:50:35.826756	Cleber	login
2024-11-27 14:50:39.498429	Cleber	login
2024-11-27 14:50:43.119197	Cleber	login
2024-11-27 14:50:45.844448	Cleber	login
2024-11-27 14:50:49.319396	Cleber	login
2024-11-27 14:50:52.977726	Cleber	login
2024-11-27 14:50:56.281623	Cleber	login
2024-11-27 14:50:59.548083	Cleber	login
2024-11-27 14:51:02.831645	Cleber	login
2024-11-27 14:51:06.082348	Cleber	login
2024-11-27 14:51:11.544127	Cleber	login
2024-11-27 14:51:14.018956	Cleber	login
2024-11-27 14:51:17.617359	Cleber	login
2024-11-27 14:51:21.091668	Cleber	login
2024-11-27 14:51:23.95817	Cleber	login
2024-11-27 14:51:27.342904	Cleber	login
2024-11-27 14:51:31.11162	Cleber	login
2024-11-27 14:51:34.839225	Cleber	login
2024-11-27 14:51:38.698996	Cleber	login
2024-11-27 14:51:41.282703	Cleber	login
2024-11-27 14:51:44.699334	Cleber	login
2024-11-27 14:51:48.060685	Cleber	login
2024-11-27 14:51:51.991408	Cleber	login
2024-11-27 14:51:55.492424	Cleber	login
2024-11-27 14:51:58.907532	Cleber	login
2024-11-27 14:52:02.503675	Cleber	login
2024-11-27 14:52:06.145097	Cleber	login
2024-11-27 14:52:09.682043	Cleber	login
2024-11-27 14:52:13.81954	Cleber	login
2024-11-27 14:52:17.041479	Cleber	login
2024-11-27 14:52:25.8478	Cleber	login
2024-11-27 14:52:29.659744	Cleber	login
2024-11-27 14:52:33.480317	Cleber	login
2024-11-27 14:52:37.180354	Cleber	login
2024-11-27 14:52:40.608376	Cleber	login
2024-11-27 14:52:44.935303	Cleber	login
2024-11-27 14:52:47.967651	Cleber	login
2024-11-27 14:52:51.315661	Cleber	login
2024-11-27 14:52:54.932704	Cleber	login
2024-11-27 14:52:58.794025	Cleber	login
2024-11-19 20:49:31.087224	Andr├® Teixeira Milioli	login
2024-11-27 14:53:02.234713	Cleber	login
2024-11-25 06:45:01.729814	Cleber	login
2024-11-19 20:52:15.266721	Andr├® Teixeira Milioli	login
2024-11-19 20:53:04.099649	Andr├® Teixeira Milioli	login
2024-11-27 14:53:21.627351	Cleber	login
2024-11-25 06:45:13.022385	Cleber	login
2024-11-27 14:53:45.575732	Cleber	login
2024-11-25 06:47:43.254341	Cleber	login
2024-11-27 14:54:19.461919	Cleber	login
2024-11-26 13:25:29.913751	Jonata Tyska	login
2024-11-27 14:54:53.419706	Cleber	login
2024-11-26 13:26:24.841955	Jonata Tyska	login
2024-11-27 14:55:44.471436	Cleber	login
2024-11-26 13:33:03.770057	Jonata Tyska	login
2024-11-27 14:56:19.889313	Cleber	login
2024-11-27 14:56:49.821224	Cleber	login
2024-11-27 14:57:20.222456	Cleber	login
2024-11-27 14:57:57.08849	Cleber	login
2024-11-26 14:11:36.895884	Felipe	login
2024-11-27 14:58:28.736755	Cleber	login
2024-11-27 14:59:01.280973	Cleber	login
2024-11-27 14:59:33.733062	Cleber	login
2024-11-27 15:00:07.04224	Cleber	login
2024-11-27 15:00:36.232681	Cleber	login
2024-11-26 15:44:34.464165	Felipe	login
2024-11-27 15:01:07.44754	Cleber	login
2025-02-23 18:32:07.53848	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:08.444644	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:15.35706	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:25.728387	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:26.050633	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:29.776146	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:30.098036	Andr├® W├╝st Zibetti	login
2024-12-03 02:13:04.521038	Cleber	login
2024-12-03 02:13:46.876611	Cleber	login
2024-12-03 02:14:04.040348	Cleber	login
2024-12-03 02:14:20.75727	Cleber	login
2024-12-03 02:14:27.012364	Cleber	login
2024-12-03 02:15:22.64131	Cleber	login
2024-12-03 02:15:46.076516	Cleber	login
2024-12-03 02:15:58.165949	Cleber	login
2024-12-03 02:16:17.341646	Cleber	login
2024-12-03 02:16:31.392314	Cleber	login
2025-02-23 18:32:42.63676	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:46.387712	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:51.997679	Andr├® W├╝st Zibetti	login
2025-02-23 18:32:52.314497	Andr├® W├╝st Zibetti	login
2025-02-23 18:33:19.456111	Andr├® W├╝st Zibetti	login
2025-02-23 18:33:19.787955	Andr├® W├╝st Zibetti	login
2025-02-23 18:42:37.126874	Andr├® W├╝st Zibetti	login
2024-12-03 12:22:10.836835	Jonata Tyska	login
2024-12-03 12:23:35.41525	Jonata Tyska	login
2025-02-23 18:42:39.050715	Andr├® W├╝st Zibetti	login
2025-02-23 18:50:11.888983	Andr├® W├╝st Zibetti	login
2025-02-23 18:50:11.948957	Andr├® W├╝st Zibetti	login
2025-02-23 18:50:11.984871	Andr├® W├╝st Zibetti	login
2024-12-18 13:42:12.20479	Matheus Machado dos Santos	login
2024-11-27 14:53:06.199784	Cleber	login
2024-11-19 20:50:05.834	Andr├® Teixeira Milioli	login
2024-11-19 20:50:48.347934	Andr├® Teixeira Milioli	login
2024-11-27 14:53:09.94799	Cleber	login
2024-11-19 20:52:37.636426	Andr├® Teixeira Milioli	login
2024-11-27 14:53:13.972082	Cleber	login
2024-11-20 22:44:51.460303	Matheus Machado dos Santos	login
2024-11-27 14:53:17.671082	Cleber	login
2024-11-27 14:53:25.538975	Cleber	login
2024-11-21 14:19:27.438069	Andr├® W├╝st Zibetti	login
2024-11-27 14:53:30.040693	Cleber	login
2024-11-21 14:19:31.094297	Andr├® W├╝st Zibetti	login
2024-11-27 14:53:35.967442	Cleber	login
2024-11-27 14:53:42.237118	Cleber	login
2024-11-21 15:13:00.750424	Felipe	login
2024-11-27 14:53:54.754967	Cleber	login
2024-11-21 15:13:04.358008	Felipe	login
2024-11-27 14:54:00.776165	Cleber	login
2024-11-21 15:13:21.850655	Felipe	login
2024-11-21 15:13:21.850655	Felipe	login
2024-11-21 15:13:21.850655	Felipe	login
2024-11-21 15:14:04.102798	Felipe	login
2024-11-21 15:14:04.102798	Felipe	login
2024-11-21 15:14:48.185255	Felipe	login
2024-11-21 15:14:48.257858	Felipe	login
2024-11-21 15:14:49.728223	Felipe	login
2024-11-21 15:16:51.244319	Felipe	login
2024-11-21 15:16:51.244319	Felipe	login
2024-11-25 18:36:18.281868	Andr├® Teixeira Milioli	login
2024-11-21 17:40:14.625317	Andr├® W├╝st Zibetti	login
2024-11-25 18:37:29.657235	Andr├® Teixeira Milioli	login
2024-11-21 17:40:18.335498	Andr├® W├╝st Zibetti	login
2024-11-27 14:54:06.902778	Cleber	login
2024-11-21 17:40:20.207138	Andr├® W├╝st Zibetti	login
2024-11-21 17:40:35.7488	Andr├® W├╝st Zibetti	login
2024-11-21 17:40:37.028479	Andr├® W├╝st Zibetti	login
2024-11-21 17:40:41.726394	Andr├® W├╝st Zibetti	login
2024-11-21 17:40:43.532911	Andr├® W├╝st Zibetti	login
2024-11-25 18:38:07.705627	Andr├® Teixeira Milioli	login
2024-11-21 17:40:52.693579	Luis	login
2024-11-25 18:38:45.530133	Andr├® Teixeira Milioli	login
2024-11-21 17:40:53.615271	Luis	login
2024-11-27 14:54:13.72198	Cleber	login
2024-11-21 17:40:55.824291	Luis	login
2024-11-21 17:40:55.824291	Luis	login
2024-11-21 17:40:55.87183	Luis	login
2024-11-21 17:40:57.585336	Luis	login
2024-11-21 17:41:01.962188	Luis	login
2024-11-21 17:41:01.969278	Luis	login
2024-11-21 17:55:53.651583	Luis	login
2024-11-27 14:54:25.783612	Cleber	login
2024-11-21 17:55:57.19946	Luis	login
2024-11-26 13:26:06.600181	Jonata Tyska	login
2024-11-21 17:56:00.211308	Luis	login
2024-11-21 17:56:00.211308	Luis	login
2024-11-21 17:56:09.22413	Luis	login
2024-11-26 13:26:51.498998	Jonata Tyska	login
2024-11-21 18:26:30.707655	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:54:34.025508	Cleber	login
2024-11-21 18:26:32.357884	Jos├® Eduardo Medeiros Jochem	login
2024-11-26 14:12:33.955583	Felipe	login
2024-11-21 18:26:35.338574	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:54:40.436154	Cleber	login
2024-11-21 18:26:38.752219	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:26:38.752219	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:26:38.752219	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:14.713068	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:18.512834	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:18.512834	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:34.363715	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:34.384235	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:37.279443	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:37.300891	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:51.117725	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:27:51.132733	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:28:05.68621	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:54:46.347149	Cleber	login
2024-11-21 18:28:06.543079	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:55:17.84806	Cleber	login
2024-11-21 18:30:21.201765	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:55:26.546293	Cleber	login
2024-11-21 18:30:22.098084	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:55:33.678113	Cleber	login
2024-11-21 18:31:28.956642	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:31:28.976293	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:31:48.267719	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:55:38.940997	Cleber	login
2024-11-21 18:31:49.139139	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:55:50.412636	Cleber	login
2024-11-21 18:31:50.995057	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:31:51.007291	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:31:51.007291	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:31:51.007291	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:38:52.652981	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:55:57.123161	Cleber	login
2024-11-21 18:38:56.280844	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 14:56:06.031926	Cleber	login
2024-11-21 18:38:58.737068	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:38:58.747633	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:38:58.757853	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:43:38.008903	Luis	login
2024-11-27 14:56:12.274745	Cleber	login
2024-11-21 18:43:38.799284	Luis	login
2024-11-27 14:56:25.940352	Cleber	login
2024-11-21 18:43:40.200608	Luis	login
2024-11-21 18:43:40.200608	Luis	login
2024-11-21 18:43:40.200608	Luis	login
2024-11-21 18:47:46.294189	Luis	login
2024-11-21 18:47:47.719072	Luis	login
2024-11-21 18:47:59.203047	Luis	login
2024-11-27 14:56:31.628669	Cleber	login
2024-11-21 18:47:59.850314	Luis	login
2024-11-27 14:56:37.76601	Cleber	login
2024-11-21 18:48:01.828186	Luis	login
2024-11-21 18:48:01.828186	Luis	login
2024-11-21 18:48:01.842947	Luis	login
2024-11-21 18:48:03.023719	Luis	login
2024-11-21 18:48:07.997623	Luis	login
2024-11-27 14:56:43.808638	Cleber	login
2024-11-21 18:48:08.526411	Luis	login
2024-11-27 14:56:55.5433	Cleber	login
2024-11-21 18:48:09.893063	Luis	login
2024-11-27 14:57:01.172865	Cleber	login
2024-11-27 14:57:06.945777	Cleber	login
2024-11-27 14:57:14.538474	Cleber	login
2024-11-27 14:57:25.85996	Cleber	login
2024-11-27 14:57:33.980471	Cleber	login
2024-11-27 14:57:40.232807	Cleber	login
2024-11-27 14:57:46.701524	Cleber	login
2024-11-27 14:58:03.187842	Cleber	login
2024-11-27 14:58:09.985889	Cleber	login
2024-11-27 14:58:15.982098	Cleber	login
2024-11-27 14:58:22.575963	Cleber	login
2024-11-27 14:58:35.03617	Cleber	login
2024-11-27 14:58:44.130898	Cleber	login
2024-11-27 14:58:49.760739	Cleber	login
2024-11-21 18:48:09.893063	Luis	login
2024-11-21 18:49:29.578875	Luis	login
2024-11-27 14:58:55.57012	Cleber	login
2024-11-21 18:49:53.622139	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:50:07.08271	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:57:56.996604	Luis	login
2024-11-21 18:57:56.996604	Luis	login
2024-11-21 18:58:18.669884	Luis	login
2024-11-27 14:59:27.308605	Cleber	login
2024-11-21 18:58:33.566416	Luis	login
2024-11-21 18:58:37.050972	Luis	login
2024-11-21 18:58:40.567498	Luis	login
2024-11-27 14:59:59.039388	Cleber	login
2024-11-27 15:00:29.822527	Cleber	login
2024-11-25 17:26:55.308439	Felipe	login
2024-11-27 15:01:01.431018	Cleber	login
2024-11-25 17:27:45.025607	Felipe	login
2024-11-25 18:36:07.191369	Andr├® Teixeira Milioli	login
2024-11-25 18:37:11.214704	Andr├® Teixeira Milioli	login
2024-11-25 18:37:47.518814	Andr├® Teixeira Milioli	login
2024-11-25 18:38:27.462326	Andr├® Teixeira Milioli	login
2024-11-26 13:25:34.266703	Jonata Tyska	login
2024-11-26 13:26:26.042603	Jonata Tyska	login
2024-12-03 02:12:57.135351	Cleber	login
2024-12-03 02:13:59.080307	Cleber	login
2024-11-26 15:44:36.91679	Felipe	login
2024-12-03 02:13:59.080307	Cleber	login
2024-12-03 02:14:09.896633	Cleber	login
2024-12-03 02:14:34.281437	Cleber	login
2024-12-03 02:15:26.917281	Cleber	login
2024-12-03 02:15:50.57347	Cleber	login
2024-12-03 02:16:07.260762	Cleber	login
2024-12-03 02:16:20.948409	Cleber	login
2024-12-03 02:16:34.829465	Cleber	login
2024-12-03 12:21:56.5568	Jonata Tyska	login
2024-12-03 12:22:30.081426	Jonata Tyska	login
2024-12-05 20:35:28.355255	Andr├® Teixeira Milioli	login
2024-12-05 20:36:46.949611	Andr├® Teixeira Milioli	login
2024-12-05 20:37:28.570018	Andr├® Teixeira Milioli	login
2024-12-04 02:58:39.965355	Cleber	login
2024-12-04 02:59:00.766145	Cleber	login
2024-12-04 02:59:13.92265	Cleber	login
2024-12-04 02:59:21.758541	Cleber	login
2024-12-04 02:59:31.038025	Cleber	login
2024-12-04 03:00:17.692209	Cleber	login
2024-12-04 03:02:28.10475	Cleber	login
2024-11-21 18:48:09.911811	Luis	login
2024-11-21 18:48:11.20379	Luis	login
2024-11-21 18:48:33.335446	Luis	login
2024-11-21 18:48:33.335446	Luis	login
2024-11-21 18:48:33.335446	Luis	login
2024-11-21 18:49:30.154643	Luis	login
2024-11-27 14:59:08.850625	Cleber	login
2024-11-21 18:49:59.479879	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:49:59.479879	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:49:59.479879	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:49:59.479879	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:58:32.324406	Luis	login
2024-11-21 18:58:37.86409	Luis	login
2024-11-21 18:58:48.656066	Luis	login
2024-11-27 14:59:15.916657	Cleber	login
2024-11-27 14:59:21.48614	Cleber	login
2024-11-27 14:59:39.340984	Cleber	login
2024-11-25 17:27:02.124659	Felipe	login
2024-11-27 14:59:45.638366	Cleber	login
2024-11-25 18:36:18.681322	Andr├® Teixeira Milioli	login
2024-11-25 18:37:37.073963	Andr├® Teixeira Milioli	login
2024-11-27 14:59:53.158602	Cleber	login
2024-11-25 18:38:08.089662	Andr├® Teixeira Milioli	login
2024-11-25 18:38:50.621107	Andr├® Teixeira Milioli	login
2024-11-27 15:00:12.36179	Cleber	login
2024-11-26 13:26:09.654374	Jonata Tyska	login
2024-11-26 13:33:02.695508	Jonata Tyska	login
2024-11-27 15:00:19.367615	Cleber	login
2024-11-27 15:00:24.187956	Cleber	login
2024-11-27 15:00:42.847856	Cleber	login
2024-11-27 15:00:48.742099	Cleber	login
2024-11-27 15:00:54.022149	Cleber	login
2024-11-27 15:01:13.184461	Cleber	login
2024-11-27 15:01:20.235319	Cleber	login
2024-11-27 15:01:26.133993	Cleber	login
2024-11-27 15:01:32.209802	Cleber	login
2024-11-27 15:01:38.163997	Cleber	login
2024-11-27 15:01:44.77633	Cleber	login
2024-11-27 15:01:51.738927	Cleber	login
2024-11-27 15:01:58.584853	Cleber	login
2024-11-27 15:02:06.735742	Cleber	login
2024-11-27 15:02:13.201639	Cleber	login
2024-11-27 15:02:18.906674	Cleber	login
2024-11-27 15:02:27.078206	Cleber	login
2024-11-27 15:02:34.148427	Cleber	login
2024-11-27 15:02:37.367616	Cleber	login
2024-11-27 15:02:42.808709	Cleber	login
2024-11-27 15:02:48.472073	Cleber	login
2024-11-27 15:02:54.071881	Cleber	login
2024-11-27 15:02:59.709164	Cleber	login
2024-11-27 15:03:05.129745	Cleber	login
2024-11-27 15:03:10.73092	Cleber	login
2024-11-27 15:03:17.087388	Cleber	login
2024-11-27 15:03:23.522356	Cleber	login
2024-11-27 15:03:28.058259	Cleber	login
2024-11-27 15:03:35.459519	Cleber	login
2024-11-27 15:03:41.598942	Cleber	login
2024-11-27 15:03:48.846089	Cleber	login
2024-11-27 15:03:54.724135	Cleber	login
2024-11-27 15:04:00.587151	Cleber	login
2024-11-27 15:04:05.007446	Cleber	login
2024-11-27 15:04:10.860812	Cleber	login
2024-11-27 15:04:17.135846	Cleber	login
2024-11-27 15:04:21.4147	Cleber	login
2024-11-27 15:04:27.356148	Cleber	login
2024-11-27 15:04:34.148662	Cleber	login
2024-11-27 15:04:40.732287	Cleber	login
2024-11-27 15:04:44.826723	Cleber	login
2024-11-27 15:04:51.147961	Cleber	login
2024-11-27 15:04:55.555042	Cleber	login
2024-11-27 15:05:01.32128	Cleber	login
2024-11-27 15:05:08.872996	Cleber	login
2024-11-27 15:05:14.79708	Cleber	login
2024-11-27 15:05:22.190371	Cleber	login
2024-11-27 15:05:29.449786	Cleber	login
2024-11-27 15:05:33.99554	Cleber	login
2024-11-27 15:05:40.096504	Cleber	login
2024-11-27 15:05:46.37041	Cleber	login
2024-11-27 15:05:54.87964	Cleber	login
2024-11-27 15:06:02.231346	Cleber	login
2024-11-27 15:06:08.623831	Cleber	login
2024-11-27 15:06:14.440614	Cleber	login
2024-11-27 15:06:20.736037	Cleber	login
2024-11-27 15:06:27.593787	Cleber	login
2024-11-27 15:06:34.306619	Cleber	login
2024-11-27 15:06:40.044663	Cleber	login
2024-11-27 15:06:46.803454	Cleber	login
2024-11-27 15:06:52.774764	Cleber	login
2024-11-27 15:06:59.330717	Cleber	login
2024-11-27 15:07:06.747299	Cleber	login
2024-11-27 15:07:18.550299	Cleber	login
2024-11-27 15:07:26.386875	Cleber	login
2024-11-27 15:07:32.368608	Cleber	login
2024-11-27 15:07:38.224459	Cleber	login
2024-11-27 15:07:42.787638	Cleber	login
2024-11-27 15:07:48.661476	Cleber	login
2024-11-27 15:07:54.51319	Cleber	login
2024-11-27 15:08:02.438785	Cleber	login
2024-11-27 15:08:08.693368	Cleber	login
2024-11-27 15:08:14.908366	Cleber	login
2024-11-27 15:08:21.017809	Cleber	login
2024-11-27 15:08:26.881852	Cleber	login
2024-11-27 15:08:33.40261	Cleber	login
2024-11-27 15:08:40.277716	Cleber	login
2024-11-27 15:08:46.5661	Cleber	login
2024-11-27 15:08:53.529118	Cleber	login
2024-11-27 15:08:59.730996	Cleber	login
2024-11-27 15:09:04.212156	Cleber	login
2024-11-27 15:09:11.905307	Cleber	login
2024-11-27 15:09:17.905794	Cleber	login
2024-11-27 15:09:24.280088	Cleber	login
2024-11-27 15:09:35.653101	Cleber	login
2024-11-27 15:09:41.725794	Cleber	login
2024-11-27 15:09:48.087394	Cleber	login
2024-11-27 15:09:53.899819	Cleber	login
2024-11-27 15:09:59.688481	Cleber	login
2024-11-27 15:10:11.548078	Cleber	login
2024-11-27 15:10:17.963	Cleber	login
2024-11-27 15:10:24.194705	Cleber	login
2024-11-27 15:10:30.459802	Cleber	login
2024-11-27 15:10:37.562644	Cleber	login
2024-11-27 15:10:44.293743	Cleber	login
2024-11-27 15:10:50.258631	Cleber	login
2024-11-27 15:10:56.620338	Cleber	login
2024-11-27 15:11:02.721958	Cleber	login
2024-11-27 15:11:08.920229	Cleber	login
2024-11-27 15:11:14.943501	Cleber	login
2024-11-27 15:11:20.947359	Cleber	login
2024-11-27 15:11:26.852829	Cleber	login
2024-11-27 15:11:33.572956	Cleber	login
2024-11-27 15:11:40.682709	Cleber	login
2024-11-27 15:11:47.625656	Cleber	login
2024-11-27 15:11:53.579352	Cleber	login
2024-11-27 15:12:00.615198	Cleber	login
2024-11-27 15:12:06.734731	Cleber	login
2024-11-27 15:12:11.416667	Cleber	login
2024-11-27 15:12:18.131493	Cleber	login
2024-11-27 15:12:24.505137	Cleber	login
2024-11-27 15:12:30.46828	Cleber	login
2024-11-27 15:12:36.609055	Cleber	login
2024-11-27 15:12:42.894402	Cleber	login
2024-11-27 15:12:49.132999	Cleber	login
2024-11-27 15:12:53.810825	Cleber	login
2024-11-27 15:13:00.796998	Cleber	login
2024-11-27 15:13:07.827641	Cleber	login
2024-11-27 15:13:13.778815	Cleber	login
2024-11-27 15:13:19.687711	Cleber	login
2024-11-27 15:13:25.601218	Cleber	login
2024-11-27 15:13:31.89385	Cleber	login
2024-11-27 15:13:38.864221	Cleber	login
2024-11-27 15:13:44.887752	Cleber	login
2024-11-27 15:13:53.045134	Cleber	login
2024-11-27 15:13:59.606221	Cleber	login
2024-11-21 18:49:15.15967	Luis	login
2024-11-27 15:14:05.663693	Cleber	login
2024-11-21 18:49:53.05819	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 15:14:40.74424	Cleber	login
2024-11-21 18:50:07.06904	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 18:57:57.006416	Luis	login
2024-11-21 18:58:01.123756	Luis	login
2024-11-21 18:58:01.123756	Luis	login
2024-11-21 18:58:01.123756	Luis	login
2024-11-21 18:58:03.172836	Luis	login
2024-11-21 18:58:03.172836	Luis	login
2024-11-21 18:58:09.4774	Luis	login
2024-11-27 15:15:13.973994	Cleber	login
2024-11-21 18:58:12.510919	Luis	login
2024-11-27 15:15:45.007422	Cleber	login
2024-11-21 18:58:14.479436	Luis	login
2024-11-21 18:58:14.479436	Luis	login
2024-11-21 18:58:14.554694	Luis	login
2024-11-21 18:58:19.136865	Luis	login
2024-11-21 18:58:19.136865	Luis	login
2024-11-21 18:58:31.789445	Luis	login
2024-11-27 15:16:24.322457	Cleber	login
2024-11-21 18:58:33.524274	Luis	login
2024-11-21 18:58:33.524274	Luis	login
2024-11-21 18:58:35.014497	Luis	login
2024-11-21 18:58:40.550748	Luis	login
2024-11-21 18:58:40.550748	Luis	login
2024-11-21 18:58:40.59103	Luis	login
2024-11-21 18:58:48.744199	Luis	login
2024-11-21 18:58:50.377621	Luis	login
2024-11-21 18:58:54.316063	Luis	login
2024-11-27 15:17:01.473651	Cleber	login
2024-11-21 18:59:42.209868	Luis	login
2024-11-27 15:17:54.445991	Cleber	login
2024-11-21 18:59:42.809314	Luis	login
2024-11-25 17:26:57.538719	Felipe	login
2024-11-21 18:59:44.81954	Luis	login
2024-11-21 18:59:44.903987	Luis	login
2024-11-21 18:59:45.995898	Luis	login
2024-11-21 18:59:48.739285	Luis	login
2024-11-21 19:00:40.98951	Luis	login
2024-11-27 15:18:30.482863	Cleber	login
2024-11-21 19:00:41.517306	Luis	login
2024-11-25 17:28:13.869608	Felipe	login
2024-11-21 19:00:42.733034	Luis	login
2024-11-21 19:00:42.733034	Luis	login
2024-11-21 19:00:42.764144	Luis	login
2024-11-21 19:00:44.321798	Luis	login
2024-11-21 19:00:46.705369	Luis	login
2024-11-21 19:00:53.093133	Luis	login
2024-11-21 19:01:12.510607	Luis	login
2024-11-25 18:36:09.495953	Andr├® Teixeira Milioli	login
2024-11-21 19:01:13.037738	Luis	login
2024-11-27 15:19:04.751356	Cleber	login
2024-11-21 19:01:30.830269	Luis	login
2024-11-25 18:37:12.103952	Andr├® Teixeira Milioli	login
2024-11-21 19:01:31.363154	Luis	login
2024-11-27 15:19:39.89121	Cleber	login
2024-11-21 19:12:12.914805	Luis	login
2024-11-25 18:37:48.099541	Andr├® Teixeira Milioli	login
2024-11-21 19:12:15.888444	Luis	login
2024-11-27 15:20:12.824537	Cleber	login
2024-11-21 19:12:17.30589	Luis	login
2024-11-21 19:12:17.30589	Luis	login
2024-11-21 19:12:17.30589	Luis	login
2024-11-21 19:12:17.715149	Jos├® Eduardo Medeiros Jochem	login
2024-11-25 18:38:28.333435	Andr├® Teixeira Milioli	login
2024-11-21 19:12:18.278292	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 15:20:47.306016	Cleber	login
2024-11-21 19:12:20.145984	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:20.15715	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:20.166463	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:27.215122	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:27.215122	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:31.206007	Luis	login
2024-11-21 19:12:31.266985	Luis	login
2024-11-21 19:12:35.320127	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:35.320127	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:56.38966	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:56.404276	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:57.725316	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:12:57.738943	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:07.477929	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:07.490812	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:13.608963	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:13.620269	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:16.234817	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:16.246033	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:47.215194	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:47.226065	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:51.084502	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:13:51.095116	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:14:55.502638	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:14:55.520731	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:15:03.058698	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:15:03.069338	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:15:06.714262	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:15:06.726801	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:15:27.244913	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:15:27.257655	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:15:29.264883	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:15:29.276802	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:21:28.701129	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:21:28.701129	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:21:57.259658	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:21:57.278853	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:22:12.380836	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:22:12.405215	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:22:39.373397	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:22:39.40562	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:24:15.847515	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:24:15.881474	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:24:23.333664	Jos├® Eduardo Medeiros Jochem	login
2024-11-21 19:24:23.366225	Jos├® Eduardo Medeiros Jochem	login
2024-11-27 15:21:19.783745	Cleber	login
2024-11-22 16:30:27.919015	Felipe	login
2024-11-27 15:21:51.523902	Cleber	login
2024-11-22 16:30:30.153358	Felipe	login
2024-11-27 15:22:32.989773	Cleber	login
2024-11-22 16:30:34.132692	Felipe	login
2024-11-27 15:23:06.079335	Cleber	login
2024-11-22 16:30:34.747071	Felipe	login
2024-11-27 15:23:39.994053	Cleber	login
2024-11-22 16:30:41.814326	Felipe	login
2024-11-27 15:24:13.0471	Cleber	login
2024-11-22 16:30:42.555764	Felipe	login
2024-11-27 15:24:47.59602	Cleber	login
2024-11-22 16:32:36.332344	Felipe	login
2024-11-22 16:32:42.398487	Felipe	login
2024-11-27 15:25:23.354878	Cleber	login
2024-11-27 15:25:58.328266	Cleber	login
2024-11-27 15:26:32.925619	Cleber	login
2024-11-27 15:27:07.062487	Cleber	login
2024-11-27 15:27:42.444921	Cleber	login
2024-11-27 15:14:12.889279	Cleber	login
2024-11-22 16:38:24.387599	Felipe	login
2024-11-22 16:38:24.387599	Felipe	login
2024-11-27 15:14:20.57223	Cleber	login
2024-11-27 15:14:26.800988	Cleber	login
2024-11-27 15:14:32.929441	Cleber	login
2024-11-27 15:14:48.36246	Cleber	login
2024-11-27 15:14:54.965948	Cleber	login
2024-11-27 15:15:01.189778	Cleber	login
2024-11-27 15:15:07.682885	Cleber	login
2024-11-25 17:27:26.281332	Felipe	login
2024-11-25 17:27:26.281332	Felipe	login
2024-11-27 15:15:20.0893	Cleber	login
2024-11-25 18:36:57.043435	Andr├® Teixeira Milioli	login
2024-11-25 18:37:37.495653	Andr├® Teixeira Milioli	login
2024-11-27 15:15:26.070916	Cleber	login
2024-11-25 18:38:26.627673	Andr├® Teixeira Milioli	login
2024-11-25 18:38:51.057923	Andr├® Teixeira Milioli	login
2024-11-27 15:15:32.684789	Cleber	login
2024-11-27 15:15:38.99298	Cleber	login
2024-11-27 15:15:51.482292	Cleber	login
2024-11-27 15:15:58.080466	Cleber	login
2024-11-27 15:16:05.217998	Cleber	login
2024-11-27 15:16:18.284151	Cleber	login
2024-11-27 15:16:30.158793	Cleber	login
2024-11-27 15:16:36.381634	Cleber	login
2024-11-27 15:16:43.55866	Cleber	login
2024-11-26 15:44:49.634693	Felipe	consulta_licitacao
2024-11-26 15:45:02.651718	Felipe	consulta_licitacao
2024-11-27 15:16:50.655352	Cleber	login
2024-11-27 15:17:08.691398	Cleber	login
2024-11-27 15:17:14.839875	Cleber	login
2024-11-27 15:17:20.953181	Cleber	login
2024-11-27 15:17:30.09034	Cleber	login
2024-11-27 15:18:01.745533	Cleber	login
2024-11-27 15:18:09.286026	Cleber	login
2024-11-27 15:18:16.017297	Cleber	login
2024-11-27 15:18:23.176711	Cleber	login
2024-11-27 15:18:37.602819	Cleber	login
2024-11-27 15:18:45.412485	Cleber	login
2024-11-27 15:18:52.415952	Cleber	login
2024-11-27 15:18:58.584424	Cleber	login
2024-11-27 15:19:11.245882	Cleber	login
2024-11-27 15:19:17.676697	Cleber	login
2024-11-27 15:19:25.888078	Cleber	login
2024-11-27 15:19:33.708201	Cleber	login
2024-11-27 15:19:46.435217	Cleber	login
2024-11-27 15:19:53.023154	Cleber	login
2024-11-27 15:19:59.632789	Cleber	login
2024-11-27 15:20:06.234244	Cleber	login
2024-11-27 15:20:19.37576	Cleber	login
2024-11-27 15:20:27.724644	Cleber	login
2024-11-27 15:20:33.22196	Cleber	login
2024-11-27 15:20:40.562386	Cleber	login
2024-11-27 15:20:53.871903	Cleber	login
2024-11-27 15:21:00.538033	Cleber	login
2024-11-27 15:21:06.979968	Cleber	login
2024-11-27 15:21:13.273729	Cleber	login
2024-11-27 15:21:26.058264	Cleber	login
2024-11-27 15:21:32.744354	Cleber	login
2024-11-27 15:21:38.987127	Cleber	login
2024-11-27 15:21:45.297284	Cleber	login
2024-11-27 15:21:58.033396	Cleber	login
2024-11-27 15:22:04.253237	Cleber	login
2024-11-27 15:22:19.622943	Cleber	login
2024-11-27 15:22:26.60603	Cleber	login
2024-11-27 15:22:40.191284	Cleber	login
2024-11-27 15:22:46.815229	Cleber	login
2024-11-27 15:22:53.071352	Cleber	login
2024-11-27 15:22:59.628842	Cleber	login
2024-11-27 15:23:13.557722	Cleber	login
2024-11-27 15:23:20.144794	Cleber	login
2024-11-27 15:23:26.637287	Cleber	login
2024-11-27 15:23:33.043103	Cleber	login
2024-11-27 15:23:46.963808	Cleber	login
2024-11-27 15:23:53.747183	Cleber	login
2024-11-27 15:24:00.215396	Cleber	login
2024-11-27 15:24:06.465054	Cleber	login
2024-11-27 15:24:19.369165	Cleber	login
2024-11-27 15:24:25.66767	Cleber	login
2024-11-27 15:24:32.705084	Cleber	login
2024-11-27 15:24:39.630726	Cleber	login
2024-11-27 15:24:55.516098	Cleber	login
2024-11-27 15:25:02.44019	Cleber	login
2024-11-27 15:25:09.214148	Cleber	login
2024-11-27 15:25:16.335218	Cleber	login
2024-11-27 15:25:30.444714	Cleber	login
2024-11-27 15:25:36.816038	Cleber	login
2024-11-27 15:25:44.104628	Cleber	login
2024-11-27 15:25:51.213385	Cleber	login
2024-11-27 15:26:05.448618	Cleber	login
2024-11-27 15:26:12.444246	Cleber	login
2024-11-27 15:26:19.402149	Cleber	login
2024-11-27 15:26:26.035619	Cleber	login
2024-11-27 15:26:39.714001	Cleber	login
2024-11-27 15:26:46.483323	Cleber	login
2024-11-27 15:26:53.518467	Cleber	login
2024-11-27 15:27:01.451102	Cleber	login
2024-11-27 15:27:13.543616	Cleber	login
2024-11-27 15:27:20.5415	Cleber	login
2024-11-27 15:27:28.334944	Cleber	login
2024-11-27 15:27:34.963905	Cleber	login
2024-11-27 15:27:48.606837	Cleber	login
2024-11-27 15:27:56.107685	Cleber	login
2024-11-27 15:28:04.617804	Cleber	login
2024-11-27 15:28:11.420979	Cleber	login
2024-11-27 15:28:18.943694	Cleber	login
2024-11-27 15:28:25.01166	Cleber	login
2024-11-27 15:28:31.437272	Cleber	login
2024-11-27 15:28:38.180608	Cleber	login
2024-11-27 15:28:45.417826	Cleber	login
2024-11-27 15:28:52.45914	Cleber	login
2024-11-27 15:29:00.374642	Cleber	login
2024-11-27 15:29:07.390124	Cleber	login
2024-11-27 15:29:14.893332	Cleber	login
2024-11-27 15:29:22.17416	Cleber	login
2024-12-04 18:58:57.882636	Jonata Tyska	login
2024-12-05 20:34:22.910624	Andr├® Teixeira Milioli	login
2024-12-05 20:36:28.129182	Andr├® Teixeira Milioli	login
2024-12-05 20:36:58.855219	Andr├® Teixeira Milioli	login
2024-12-03 02:12:59.77766	Cleber	login
2024-12-03 02:13:54.956372	Cleber	login
2024-12-03 02:14:08.992608	Cleber	login
2024-12-03 02:14:23.308453	Cleber	login
2024-12-03 02:14:34.95767	Cleber	login
2024-12-03 02:15:27.894225	Cleber	login
2024-12-03 02:15:51.424946	Cleber	login
2024-12-03 02:16:08.144474	Cleber	login
2024-12-03 02:16:21.912619	Cleber	login
2024-12-03 02:16:36.273231	Cleber	login
2024-12-03 12:21:58.005177	Jonata Tyska	login
2024-12-03 12:23:33.940685	Jonata Tyska	login
2024-12-04 02:58:24.904824	Cleber	login
2024-12-04 02:58:58.722072	Cleber	login
2024-12-04 02:59:10.066339	Cleber	login
2024-12-04 02:59:18.902378	Cleber	login
2024-12-04 02:59:28.050826	Cleber	login
2024-11-22 16:32:44.459664	Felipe	login
2024-11-22 16:37:36.725705	Felipe	login
2024-11-27 15:29:29.047747	Cleber	login
2024-11-27 15:29:35.942987	Cleber	login
2024-11-27 15:29:42.910481	Cleber	login
2024-11-27 15:29:48.986781	Cleber	login
2024-11-27 15:29:56.693535	Cleber	login
2024-11-27 15:30:02.816313	Cleber	login
2024-11-27 15:30:10.976198	Cleber	login
2024-11-27 15:30:18.420995	Cleber	login
2024-11-27 15:30:24.95724	Cleber	login
2024-11-27 15:30:31.473892	Cleber	login
2024-11-27 15:30:38.398518	Cleber	login
2024-11-27 15:30:49.716996	Cleber	login
2024-11-27 15:30:59.737702	Cleber	login
2024-11-27 15:31:14.41019	Cleber	login
2024-11-27 15:31:26.308156	Cleber	login
2024-11-27 15:31:37.099951	Cleber	login
2024-12-04 18:58:58.972874	Jonata Tyska	login
2024-12-05 20:34:23.638292	Andr├® Teixeira Milioli	login
2024-12-05 20:36:28.762808	Andr├® Teixeira Milioli	login
2024-12-05 20:37:28.257121	Andr├® Teixeira Milioli	login
2025-02-22 11:31:34.439576	Andr├® W├╝st Zibetti	login
2025-02-22 11:31:35.326894	Andr├® W├╝st Zibetti	login
2025-02-22 11:31:47.224784	Andr├® W├╝st Zibetti	login
2025-02-22 11:31:47.347963	Andr├® W├╝st Zibetti	login
2025-02-22 11:31:47.552573	Andr├® W├╝st Zibetti	login
2024-11-27 15:48:57.814056	Jonata Tyska	login
2024-11-27 15:49:00.91389	Jonata Tyska	login
2024-11-27 15:49:12.68418	Jonata Tyska	login
2024-11-27 15:49:14.295667	Jonata Tyska	login
2024-11-27 15:49:25.545849	Jonata Tyska	login
2024-11-27 15:49:26.58308	Jonata Tyska	login
2025-02-22 11:32:24.153258	Andr├® W├╝st Zibetti	login
2025-02-22 11:32:31.918815	Andr├® W├╝st Zibetti	login
2025-02-22 11:32:37.516037	Andr├® W├╝st Zibetti	login
2025-02-22 11:32:53.657178	Andr├® W├╝st Zibetti	login
2025-02-22 11:32:54.687058	Andr├® W├╝st Zibetti	login
2025-02-22 11:32:54.770058	Andr├® W├╝st Zibetti	login
2025-02-22 11:33:08.05374	Andr├® W├╝st Zibetti	login
2025-02-22 11:33:08.771037	Andr├® W├╝st Zibetti	login
2025-02-22 11:33:09.428792	Andr├® W├╝st Zibetti	login
2025-02-22 11:33:09.998053	Andr├® W├╝st Zibetti	login
2024-11-25 17:27:01.691954	Felipe	login
2024-11-25 17:28:15.479353	Felipe	login
2024-11-25 19:26:18.555369	Andr├® Teixeira Milioli	login
2024-11-25 19:26:34.513449	Andr├® Teixeira Milioli	login
2024-11-25 19:27:21.747936	Andr├® Teixeira Milioli	login
2024-11-25 19:28:43.281135	Andr├® Teixeira Milioli	login
2024-11-25 19:29:29.437519	Andr├® Teixeira Milioli	login
2024-11-26 14:28:54.698703	Felipe	login
2025-02-21 21:33:07.111649	Luis	login
2025-02-21 21:33:07.837049	Luis	login
2025-02-21 21:33:11.698265	Luis	login
2025-02-21 21:33:11.698265	Luis	login
2025-02-21 21:33:15.483582	Luis	login
2025-02-21 21:33:15.555481	Luis	login
2025-02-21 21:33:15.721963	Luis	login
2024-11-27 17:51:04.692201	Jerusa Marchi	login
2024-11-27 17:51:07.082224	Jerusa Marchi	login
2024-11-27 17:51:15.999876	Jerusa Marchi	login
2024-11-27 17:51:16.032185	Jerusa Marchi	login
2024-11-27 17:51:17.483195	Jerusa Marchi	login
2024-11-27 17:51:22.710649	Jerusa Marchi	login
2024-11-27 17:51:24.343146	Jerusa Marchi	login
2024-11-27 17:51:29.556912	Jerusa Marchi	login
2024-11-27 17:51:30.639764	Jerusa Marchi	login
2024-11-27 17:51:33.067683	Jerusa Marchi	login
2024-11-27 17:51:35.116216	Jerusa Marchi	login
2024-11-27 17:51:54.250828	Jerusa Marchi	login
2024-11-27 17:51:54.279345	Jerusa Marchi	login
2024-11-27 17:51:55.686877	Jerusa Marchi	login
2024-11-27 17:52:08.05903	Jerusa Marchi	login
2024-11-27 17:52:10.592329	Jerusa Marchi	login
2024-11-27 17:52:12.016862	Jerusa Marchi	login
2024-11-27 17:52:14.134463	Jerusa Marchi	login
2024-11-27 17:52:14.73179	Jerusa Marchi	login
2024-11-27 18:18:22.8439	Jerusa Marchi	login
2024-11-27 18:18:32.7791	Jerusa Marchi	login
2024-11-27 18:18:35.31382	Jerusa Marchi	login
2024-11-27 18:18:40.194012	Jerusa Marchi	login
2024-11-27 18:18:40.861003	Jerusa Marchi	login
2024-11-27 18:18:44.912434	Jerusa Marchi	login
2024-11-27 18:18:46.173019	Jerusa Marchi	login
2024-11-27 18:18:52.39562	Jerusa Marchi	login
2024-11-27 18:18:55.657118	Jerusa Marchi	login
2024-11-27 18:18:55.684716	Jerusa Marchi	login
2024-11-22 16:38:28.038616	Felipe	login
2024-11-22 16:38:28.038616	Felipe	login
2024-11-25 19:26:04.644069	Andr├® Teixeira Milioli	login
2024-11-25 19:26:26.820115	Andr├® Teixeira Milioli	login
2024-11-25 19:27:08.509203	Andr├® Teixeira Milioli	login
2024-11-25 19:27:57.121212	Andr├® Teixeira Milioli	login
2024-11-25 19:29:13.571581	Andr├® Teixeira Milioli	login
2024-12-05 20:35:29.232246	Andr├® Teixeira Milioli	login
2024-11-25 19:30:37.945274	Andr├® Teixeira Milioli	login
2024-11-26 14:28:56.735173	Felipe	login
2024-11-26 14:28:56.735173	Felipe	login
2024-11-26 14:28:56.735173	Felipe	login
2024-11-26 14:28:56.735173	Felipe	login
2024-11-26 14:28:56.735173	Felipe	login
2024-11-26 14:28:56.735173	Felipe	login
2024-12-05 20:36:47.25447	Andr├® Teixeira Milioli	login
2024-11-26 15:45:36.059093	Felipe	consulta_licitacao
2024-11-27 18:18:44.932627	Jerusa Marchi	login
2024-11-27 18:18:50.643746	Jerusa Marchi	login
2024-11-27 18:18:58.128461	Jerusa Marchi	login
2024-11-27 18:19:39.770412	Jerusa Marchi	login
2024-11-27 18:19:40.383869	Jerusa Marchi	login
2024-11-27 18:20:09.127888	Jerusa Marchi	login
2024-11-27 18:20:17.091745	Jerusa Marchi	login
2024-11-27 18:20:58.204318	Jerusa Marchi	login
2024-11-27 18:21:13.01469	Jerusa Marchi	login
2024-11-27 18:22:11.448475	Jerusa Marchi	login
2024-11-27 18:22:20.521763	Jonata Tyska	login
2024-11-27 18:22:31.28664	Jonata Tyska	login
2024-11-27 18:22:36.61	Jerusa Marchi	login
2024-11-27 18:23:03.67704	Jonata Tyska	login
2024-11-27 18:24:02.570947	Jonata Tyska	login
2024-11-27 18:24:43.232127	Jonata Tyska	login
2024-11-27 18:27:23.809969	Jonata Tyska	login
2024-11-27 18:27:32.152367	Jerusa Marchi	login
2024-11-27 18:27:37.482633	Jonata Tyska	login
2024-11-27 18:27:39.490755	Jonata Tyska	login
2024-11-27 18:27:53.676912	Jerusa Marchi	login
2024-11-27 18:27:55.149505	Jerusa Marchi	login
2024-11-27 18:28:20.768495	Jonata Tyska	login
2024-12-03 02:13:12.69748	Cleber	login
2024-12-03 02:13:16.203979	Cleber	login
2024-12-03 02:13:20.040138	Cleber	login
2024-12-03 02:13:21.084693	Cleber	login
2024-12-03 02:13:47.793369	Cleber	login
2024-12-03 02:14:04.716607	Cleber	login
2024-12-03 02:14:22.200528	Cleber	login
2024-12-03 02:14:27.940472	Cleber	login
2024-12-03 02:15:25.981976	Cleber	login
2024-12-03 02:15:49.629416	Cleber	login
2024-12-03 02:16:06.297686	Cleber	login
2024-12-03 02:16:19.60464	Cleber	login
2024-12-03 02:16:34.209174	Cleber	login
2024-12-03 12:22:11.639384	Jonata Tyska	login
2024-12-04 02:58:27.51016	Cleber	login
2024-12-04 02:58:59.297934	Cleber	login
2024-12-04 02:59:10.754282	Cleber	login
2024-12-04 02:59:19.47018	Cleber	login
2024-12-04 02:59:28.670881	Cleber	login
2024-12-04 03:00:10.575254	Cleber	login
2024-12-04 03:00:23.782398	Cleber	login
2024-12-19 14:33:24.961917	M├írcio Castro	login
2024-12-18 12:37:39.858841	Renato Fileto	login
2024-11-22 16:36:29.507638	Felipe	login
2024-11-22 16:36:29.507638	Felipe	login
2024-11-22 16:38:29.475124	Felipe	login
2024-11-22 22:02:56.279369	Felipe	login
2025-02-25 22:22:44.825416	Felipe	login
2024-11-25 19:26:19.148032	Andr├® Teixeira Milioli	login
2024-11-27 18:19:13.147447	Jerusa Marchi	login
2024-11-25 19:26:49.401158	Andr├® Teixeira Milioli	login
2024-11-27 18:19:13.752168	Jerusa Marchi	login
2024-11-25 19:27:22.085715	Andr├® Teixeira Milioli	login
2024-11-27 18:19:17.83827	Jerusa Marchi	login
2024-11-25 19:28:45.121273	Andr├® Teixeira Milioli	login
2024-11-27 18:19:17.83827	Jerusa Marchi	login
2024-11-25 19:29:47.540887	Andr├® Teixeira Milioli	login
2024-11-27 18:19:48.055711	Jerusa Marchi	login
2024-11-26 14:28:58.865764	Felipe	login
2024-11-27 18:19:48.089265	Jerusa Marchi	login
2024-11-27 18:19:49.395337	Jerusa Marchi	login
2024-11-27 18:20:07.258348	Jerusa Marchi	login
2024-11-27 18:20:10.489897	Jerusa Marchi	login
2024-11-27 18:20:18.259616	Jerusa Marchi	login
2024-11-27 18:20:55.687805	Jerusa Marchi	login
2024-11-27 18:21:12.381326	Jerusa Marchi	login
2024-11-27 18:21:26.004442	Jerusa Marchi	login
2024-11-27 18:21:26.581437	Jerusa Marchi	login
2024-11-27 18:22:12.074612	Jerusa Marchi	login
2024-11-27 18:22:22.706891	Jonata Tyska	login
2024-11-27 18:22:32.222288	Jonata Tyska	login
2024-11-27 18:22:35.586066	Jerusa Marchi	login
2024-11-27 18:22:48.951632	Jonata Tyska	login
2024-11-27 18:23:05.158519	Jonata Tyska	login
2024-11-27 18:23:57.605077	Jonata Tyska	login
2024-11-27 18:24:42.390784	Jonata Tyska	login
2024-11-27 18:27:16.882915	Jerusa Marchi	login
2024-11-27 18:27:16.915903	Jerusa Marchi	login
2024-11-27 18:27:29.575156	Jonata Tyska	login
2024-11-27 18:27:31.016601	Jonata Tyska	login
2024-11-27 18:27:32.224847	Jonata Tyska	login
2024-11-27 18:27:34.161656	Jerusa Marchi	login
2024-11-27 18:27:35.220791	Jonata Tyska	login
2024-11-27 18:27:36.098687	Jonata Tyska	login
2024-11-27 18:27:40.444023	Jonata Tyska	login
2024-11-27 18:27:42.70163	Jonata Tyska	login
2024-11-27 18:27:44.500204	Jonata Tyska	login
2024-11-27 18:27:57.628677	Jonata Tyska	login
2024-11-27 18:28:10.565477	Jerusa Marchi	login
2024-11-27 18:28:19.699742	Jonata Tyska	login
2024-12-19 14:33:19.12646	M├írcio Castro	login
2024-11-27 22:28:01.802635	Cleber	login
2024-11-27 22:28:04.479212	Cleber	login
2025-02-25 22:22:45.45701	Felipe	login
2025-02-25 22:22:51.962241	Felipe	login
2025-02-25 22:22:51.991599	Felipe	login
2024-12-05 20:35:30.124284	Andr├® Teixeira Milioli	login
2024-12-05 20:36:58.558604	Andr├® Teixeira Milioli	login
2024-12-10 13:08:48.768619	M├írcio Castro	login
2024-12-10 13:08:54.799511	M├írcio Castro	login
2025-02-25 22:22:52.025865	Felipe	login
2025-02-25 22:22:55.775099	Felipe	login
2025-02-25 22:22:55.801031	Felipe	login
2025-02-25 22:22:55.834884	Felipe	login
2024-12-23 19:27:40.362029	M├írcio Castro	login
2024-11-28 11:35:44.606162	Jonata Tyska	login
2024-11-28 11:35:54.824699	Jonata Tyska	login
2024-11-28 11:36:06.132633	Jonata Tyska	login
2024-11-28 11:36:07.057768	Jonata Tyska	login
2024-11-28 11:36:20.863477	Jonata Tyska	login
2024-11-28 11:36:21.438583	Jonata Tyska	login
2024-11-28 11:36:37.282207	Jonata Tyska	login
2024-11-28 11:36:52.478656	Jonata Tyska	login
2024-11-28 11:36:54.241954	Jonata Tyska	login
2024-11-28 11:39:30.577885	Jonata Tyska	login
2024-11-28 11:39:31.347444	Jonata Tyska	login
2024-11-28 11:39:40.789523	Jonata Tyska	login
2024-11-28 11:39:41.297923	Jonata Tyska	login
2024-11-28 11:39:44.556162	Jonata Tyska	login
2024-11-28 11:39:46.934931	Jonata Tyska	login
2024-11-28 11:39:49.589806	Jonata Tyska	login
2024-11-28 15:26:07.801529	Jonata Tyska	login
2024-11-28 15:26:11.100566	Jonata Tyska	login
2024-11-28 15:26:26.256176	Jonata Tyska	login
2024-11-28 15:26:28.291505	Jonata Tyska	login
2024-11-28 15:26:33.323644	Jonata Tyska	login
2024-11-28 15:26:52.166307	Jonata Tyska	login
2024-11-28 15:26:55.285701	Jonata Tyska	login
2024-11-28 20:41:54.309696	Cleber	login
2024-11-28 20:41:57.432938	Cleber	login
2024-11-28 20:42:13.494403	Cleber	login
2024-11-28 20:42:30.698444	Cleber	login
2024-11-28 20:42:32.553947	Cleber	login
2024-12-02 03:37:53.66586	Cleber	login
2024-12-02 03:37:56.286933	Cleber	login
2024-12-02 03:38:14.704032	Cleber	login
2024-12-02 03:38:15.343654	Cleber	login
2024-12-02 03:38:31.155888	Cleber	login
2024-12-02 03:38:32.204069	Cleber	login
2024-12-02 03:38:36.216005	Cleber	login
2024-12-02 03:38:37.843988	Cleber	login
2024-12-02 03:38:37.843988	Cleber	login
2024-12-02 03:38:41.832699	Cleber	login
2024-12-02 03:38:43.540351	Cleber	login
2024-12-02 03:38:44.083766	Cleber	login
2024-12-02 03:38:45.53223	Cleber	login
2024-12-02 03:38:56.443797	Cleber	login
2024-12-02 03:38:57.248477	Cleber	login
2024-12-02 03:39:14.9411	Cleber	login
2024-12-02 03:39:15.37701	Cleber	login
2024-12-02 03:39:21.997666	Cleber	login
2024-12-02 03:39:23.080901	Cleber	login
2024-12-02 03:39:23.548009	Cleber	login
2024-12-02 03:39:31.881395	Cleber	login
2024-12-02 03:39:40.145756	Cleber	login
2024-12-02 03:39:41.105278	Cleber	login
2024-12-02 03:39:43.573021	Cleber	login
2024-12-02 03:39:46.14098	Cleber	login
2024-12-02 03:39:58.996722	Cleber	login
2024-12-02 03:39:59.044482	Cleber	login
2024-12-02 03:39:59.08864	Cleber	login
2024-12-02 03:40:05.921983	Cleber	login
2024-12-02 03:40:05.959763	Cleber	login
2024-12-02 03:40:06.003655	Cleber	login
2024-12-02 03:40:06.768385	Cleber	login
2024-12-02 03:40:06.808177	Cleber	login
2024-12-02 03:40:06.851944	Cleber	login
2024-12-02 03:40:07.428351	Cleber	login
2024-12-02 03:40:07.468214	Cleber	login
2024-12-02 03:40:07.507638	Cleber	login
2024-12-02 03:40:07.988416	Cleber	login
2024-12-02 03:40:08.027932	Cleber	login
2024-12-02 03:40:08.067812	Cleber	login
2024-12-02 03:40:08.368384	Cleber	login
2024-12-02 03:40:08.407982	Cleber	login
2024-12-02 03:40:08.476127	Cleber	login
2024-12-02 03:40:08.82422	Cleber	login
2024-12-02 03:40:08.864378	Cleber	login
2024-12-02 03:40:08.907647	Cleber	login
2024-11-22 16:38:22.306391	Felipe	login
2024-11-22 16:38:22.306391	Felipe	login
2024-11-22 16:59:36.040288	Felipe	login
2024-11-22 17:02:31.913982	Felipe	login
2024-11-22 22:03:53.33762	Felipe	login
2024-11-22 19:25:19.109761	Felipe	login
2024-11-25 19:26:05.232596	Andr├® Teixeira Milioli	login
2024-11-22 19:25:21.260721	Felipe	login
2024-11-22 19:28:37.669887	Felipe	login
2024-11-22 19:28:37.669887	Felipe	login
2024-11-22 19:28:49.762618	Felipe	login
2024-11-22 19:28:49.762618	Felipe	login
2024-11-22 19:28:49.762618	Felipe	login
2024-11-22 19:28:49.762618	Felipe	login
2024-11-22 19:28:49.762618	Felipe	login
2024-11-22 19:28:49.812376	Felipe	login
2024-11-25 19:26:34.050531	Andr├® Teixeira Milioli	login
2024-11-22 21:21:38.202901	Felipe	login
2024-11-22 21:21:57.894725	Felipe	login
2024-11-22 21:23:14.798269	Felipe	login
2024-12-18 13:41:41.998127	Matheus Machado dos Santos	login
2024-11-22 21:23:16.96169	Felipe	login
2024-11-25 19:27:08.866845	Andr├® Teixeira Milioli	login
2024-11-22 21:25:31.344762	Felipe	login
2024-12-18 13:41:43.137421	Matheus Machado dos Santos	login
2024-11-22 21:25:33.46147	Felipe	login
2024-11-25 19:28:36.789294	Andr├® Teixeira Milioli	login
2024-11-22 21:25:36.512682	Felipe	login
2024-11-25 19:29:29.065245	Andr├® Teixeira Milioli	login
2024-11-22 21:25:37.276382	Felipe	login
2024-12-18 13:41:53.758688	Matheus Machado dos Santos	login
2024-11-22 21:25:39.874135	Felipe	login
2024-11-25 19:30:38.348503	Andr├® Teixeira Milioli	login
2024-11-22 21:25:50.343978	Felipe	login
2024-11-26 14:30:33.699804	Felipe	login
2024-11-22 21:25:51.981742	Felipe	login
2024-11-26 14:30:38.807634	Felipe	login
2024-11-22 21:28:33.558076	Felipe	login
2024-11-26 14:30:38.807634	Felipe	login
2024-11-22 21:28:35.671958	Felipe	login
2024-11-26 14:30:58.606325	Felipe	login
2024-11-22 21:28:39.344851	Felipe	login
2024-11-26 14:30:58.606325	Felipe	login
2024-11-22 21:28:40.223422	Felipe	login
2024-11-26 14:30:58.606325	Felipe	login
2024-11-22 21:28:46.291471	Felipe	login
2024-11-22 21:28:46.336712	Felipe	login
2024-11-22 21:29:02.293103	Felipe	login
2024-11-22 21:29:02.305836	Felipe	login
2024-11-22 21:29:10.268326	Felipe	login
2024-11-22 21:29:10.268326	Felipe	login
2024-11-22 21:29:10.268326	Felipe	login
2024-11-22 21:29:10.284343	Felipe	login
2024-11-22 21:29:10.284343	Felipe	login
2024-11-22 21:29:10.284343	Felipe	login
2024-11-22 21:29:25.043031	Felipe	login
2024-11-22 21:29:25.043031	Felipe	login
2024-11-22 21:30:46.238953	Felipe	login
2024-11-22 21:42:16.686419	Felipe	login
2024-11-22 21:42:38.860189	Felipe	login
2024-11-22 21:42:38.860189	Felipe	login
2024-11-22 21:42:38.860189	Felipe	login
2024-11-22 21:42:38.860189	Felipe	login
2024-11-22 21:42:38.860189	Felipe	login
2024-11-22 21:42:38.860189	Felipe	login
2024-11-22 21:42:38.860189	Felipe	login
2024-11-22 21:42:51.602076	Felipe	login
2024-11-22 21:42:51.602076	Felipe	login
2024-11-22 21:42:51.635442	Felipe	login
2024-11-26 14:30:58.606325	Felipe	login
2024-11-22 21:43:26.310932	Felipe	login
2024-11-22 21:43:42.422101	Felipe	login
2024-11-22 21:43:42.422101	Felipe	login
2024-11-22 21:43:42.422101	Felipe	login
2024-11-22 21:43:42.422101	Felipe	login
2024-11-22 21:43:42.422101	Felipe	login
2024-11-22 21:43:42.422101	Felipe	login
2024-11-26 14:30:58.606325	Felipe	login
2024-11-26 14:30:58.606325	Felipe	login
2024-11-26 14:31:00.355216	Felipe	login
2024-11-26 14:31:00.370626	Felipe	login
2024-11-26 14:34:07.441239	Felipe	login
2024-11-26 14:34:39.488138	Felipe	login
2024-11-22 21:44:08.647112	Felipe	login
2024-11-26 14:34:39.50276	Felipe	login
2024-12-18 13:41:54.777346	Matheus Machado dos Santos	login
2024-12-02 03:38:16.832295	Cleber	login
2024-12-02 03:38:39.311985	Cleber	login
2024-12-02 03:38:46.163835	Cleber	login
2024-12-02 03:39:17.481205	Cleber	login
2024-12-02 03:40:09.285347	Cleber	login
2024-12-02 03:40:10.107504	Cleber	login
2024-12-02 03:40:15.69193	Cleber	login
2024-12-02 03:41:08.183688	Cleber	login
2024-12-02 03:41:09.131526	Cleber	login
2024-12-02 03:41:15.488644	Cleber	login
2024-12-02 03:41:16.145393	Cleber	login
2024-12-02 03:41:18.621212	Cleber	login
2024-12-02 03:41:19.336452	Cleber	login
2024-12-10 13:08:47.348078	M├írcio Castro	login
2024-12-10 13:08:49.975248	M├írcio Castro	login
2024-12-10 13:08:53.562179	M├írcio Castro	login
2024-12-10 13:08:57.739422	M├írcio Castro	login
2024-12-10 13:09:53.995155	Jonata Tyska	login
2024-12-10 13:11:15.435973	Jonata Tyska	login
2024-12-03 02:13:13.42532	Cleber	login
2024-12-03 02:13:19.121244	Cleber	login
2024-12-03 02:13:20.488877	Cleber	login
2024-12-03 02:13:48.738813	Cleber	login
2024-12-03 02:14:08.076426	Cleber	login
2024-12-03 02:14:22.680616	Cleber	login
2024-12-03 02:14:26.097211	Cleber	login
2024-12-03 02:15:22.013291	Cleber	login
2024-12-03 02:15:45.368661	Cleber	login
2024-12-03 02:15:57.573635	Cleber	login
2024-12-03 02:16:16.437057	Cleber	login
2024-12-03 02:16:30.796652	Cleber	login
2024-12-03 02:16:36.99335	Cleber	login
2024-12-03 12:22:28.977124	Jonata Tyska	login
2024-12-18 13:42:13.752618	Matheus Machado dos Santos	login
2024-12-18 13:42:22.229685	Matheus Machado dos Santos	login
2024-12-18 13:42:23.156417	Matheus Machado dos Santos	login
2024-12-19 22:39:50.180888	Renato Fileto	login
2024-12-04 02:58:53.226937	Cleber	login
2024-12-04 02:59:01.598457	Cleber	login
2024-12-04 02:59:14.798213	Cleber	login
2024-12-04 02:59:22.71453	Cleber	login
2024-12-04 02:59:31.906334	Cleber	login
2024-12-04 03:00:18.620657	Cleber	login
2024-12-04 03:02:28.816639	Cleber	login
2025-02-26 01:58:16.881137	Matheus Machado dos Santos	login
2025-02-26 01:58:23.589707	Matheus Machado dos Santos	login
2025-02-26 01:58:58.024108	Matheus Machado dos Santos	login
2025-02-26 01:59:31.635848	Matheus Machado dos Santos	login
2025-02-26 02:02:25.846936	Matheus Machado dos Santos	login
2025-02-26 02:05:08.480273	Matheus Machado dos Santos	login
2025-02-26 02:12:16.525505	Felipe	login
2025-02-26 02:12:36.346747	Felipe	login
2025-02-26 02:12:37.774184	Matheus Machado dos Santos	login
2025-02-26 02:12:37.774184	Matheus Machado dos Santos	login
2025-02-26 02:12:37.824662	Matheus Machado dos Santos	login
2025-02-26 02:12:37.896632	Matheus Machado dos Santos	login
2025-02-26 02:13:18.589669	Felipe	login
2025-02-26 02:13:37.500129	Felipe	login
2025-02-26 02:13:52.807195	Felipe	login
2025-02-26 02:14:15.516622	Felipe	login
2025-02-26 02:14:15.516622	Felipe	login
2025-02-26 02:14:21.232397	Felipe	login
2025-02-26 02:14:32.193259	Felipe	login
2025-02-26 02:15:10.852635	Felipe	login
2025-02-26 02:16:44.656161	Matheus Machado dos Santos	login
2025-02-26 02:16:46.859941	Matheus Machado dos Santos	login
2025-02-26 02:18:14.01554	Matheus Machado dos Santos	login
2025-02-26 02:18:46.788644	Felipe	login
2025-02-26 02:19:29.596724	Matheus Machado dos Santos	login
2025-02-26 02:20:37.725824	Matheus Machado dos Santos	login
2025-02-26 02:20:37.725824	Matheus Machado dos Santos	login
2025-02-26 02:20:37.776462	Matheus Machado dos Santos	login
2025-02-26 02:20:37.854853	Matheus Machado dos Santos	login
2025-02-26 02:21:29.544587	Felipe	login
2025-02-26 02:21:42.264801	Felipe	login
2025-02-24 17:30:31.271327	Felipe	login
2025-02-24 17:30:32.188009	Felipe	login
2025-02-24 17:30:34.840552	Felipe	login
2025-02-24 17:30:34.961008	Felipe	login
2025-02-24 17:30:35.035104	Felipe	login
2025-02-24 17:33:05.693366	Myllena	login
2025-02-24 17:33:06.384274	Myllena	login
2025-02-26 01:56:56.890179	Matheus Machado dos Santos	login
2025-02-26 01:56:58.364316	Matheus Machado dos Santos	login
2025-02-26 01:57:37.115551	Matheus Machado dos Santos	login
2025-02-26 02:05:55.530969	Jos├® Eduardo Medeiros Jochem	login
2025-02-26 02:05:59.694941	Jos├® Eduardo Medeiros Jochem	login
2025-02-26 02:06:14.45562	Jos├® Eduardo Medeiros Jochem	login
2025-02-26 02:09:42.004361	Matheus Machado dos Santos	login
2025-02-26 02:13:41.099903	Felipe	login
2025-02-26 02:14:22.050864	Felipe	login
2025-02-26 02:15:22.639403	Felipe	login
2025-02-26 02:16:52.402487	Matheus Machado dos Santos	login
2025-02-26 02:16:54.959191	Matheus Machado dos Santos	login
2025-02-26 02:18:46.674493	Felipe	login
2025-02-26 02:18:51.964489	Matheus Machado dos Santos	login
2025-02-26 02:18:56.555728	Matheus Machado dos Santos	login
2025-02-26 02:21:42.024499	Felipe	login
2025-07-14 20:14:24.547921	Patrick Varela	login
2025-11-14 17:19:31.276689	Joshua Cruz	login
2025-11-15 00:25:37.307774	Matheus Machado dos Santos	login
2025-11-15 13:45:11.311177	Matheus Machado dos Santos	login
2025-11-17 17:40:08.557849	Joshua Cruz	login
2025-11-17 20:41:30.616101	Joshua Cruz	login
2025-11-18 12:42:25.707595	Zainab Ibrahim	login
2025-11-18 13:24:50.417288	Everton	login
2025-11-18 13:29:12.202653	Gabriel Vinícius Heisler	login
2025-11-18 14:49:47.905609	Hudson Afonso Batista da Silva	login
2025-11-18 16:15:03.098959	Joshua Cruz	login
2025-11-18 16:35:13.951643	Márcio Castro	login
2025-11-18 16:51:15.386023	Hudson Afonso Batista da Silva	login
2025-11-18 17:19:14.964126	Mariana Amaral Steffen	login
2025-11-18 19:10:03.545351	Cleber	login
2025-11-18 19:24:01.162597	Márcio Castro	login
2025-11-18 22:01:57.235776	Zainab Ibrahim	login
2025-11-18 22:08:22.363801	Joshua Cruz	login
2025-11-18 22:08:28.03495	Matheus Machado dos Santos	login
2025-11-18 22:39:46.679037	Cleber	login
2025-11-19 01:26:22.167063	Zainab Ibrahim	login
2025-11-19 01:26:27.111696	Zainab Ibrahim	login
2025-11-19 01:26:30.493768	Zainab Ibrahim	login
2025-11-19 01:26:32.013	Zainab Ibrahim	login
2025-11-19 01:27:09.86135	Zainab Ibrahim	login
2025-11-19 01:27:12.157148	Zainab Ibrahim	login
2025-11-19 01:28:24.503261	Zainab Ibrahim	login
2025-11-19 01:28:28.444943	Zainab Ibrahim	login
2025-11-19 01:28:30.159176	Zainab Ibrahim	login
2025-11-19 18:20:53.404744	Matheus Machado dos Santos	login
2025-11-19 18:45:12.633695	Joshua Cruz	login
2025-11-19 18:54:29.726321	Márcio Castro	login
2025-11-19 18:57:50.037599	Zainab Ibrahim	login
2025-11-19 21:48:30.576881	Cleber	login
2025-11-19 21:49:02.777197	Cleber	login
2025-11-20 11:07:01.668177	Márcio Castro	login
2025-11-20 11:08:38.873844	Cleber	login
2025-11-20 11:35:11.870661	Márcio Castro	login
2025-11-20 18:33:56.386923	Zainab Ibrahim	login
2025-11-21 00:55:55.214629	Joshua Cruz	login
2025-11-21 12:29:53.25272	Cleber	login
2025-11-21 14:45:07.575216	Zainab Ibrahim	login
2025-11-21 15:19:31.252256	André Wüst Zibetti	login
2025-11-21 17:14:29.598591	Márcio Castro	login
2025-11-21 18:13:21.505184	André Wüst Zibetti	login
2025-11-21 19:56:03.295096	Cleber	login
2025-11-21 20:01:31.771604	Joshua Cruz	login
2025-11-21 21:10:03.974768	Joshua Cruz	login
2025-11-22 21:55:42.388077	André Wüst Zibetti	login
2025-11-24 12:10:43.855106	Cleber	login
2025-11-24 12:10:56.286751	Cleber	login
2025-11-24 17:43:29.77025	Joshua Cruz	login
2025-11-24 18:08:53.042986	Lucas Vieira	login
2025-11-24 18:15:47.849008	Cleber	login
2025-11-24 18:17:02.451719	Cleber	login
2025-11-24 18:39:19.062406	Zainab Ibrahim	login
2025-11-24 19:22:55.989258	Joshua Cruz	login
2025-11-24 20:27:12.271165	Lucas Vieira	login
2025-11-24 22:47:55.254294	Pedro Henrique Azevedo	login
2025-11-25 00:11:22.063625	Sofia Bianchi Schmitz	login
2025-11-25 02:07:10.413538	André Wüst Zibetti	login
2025-11-25 04:34:16.947454	Cleber	login
2025-11-25 10:52:43.200735	André Wüst Zibetti	login
2025-11-25 13:42:42.463582	Joshua Cruz	login
2025-11-25 15:31:45.931228	Gabriel Vinícius Heisler	login
2025-11-25 16:16:28.069843	Sofia Bianchi Schmitz	login
2025-11-25 16:27:55.95056	Mariana Amaral Steffen	login
2025-11-25 21:44:47.688614	Joshua Cruz	login
2025-11-25 22:48:10.719983	Joshua Cruz	login
2025-11-25 22:54:34.518195	Cleber	login
2025-11-25 23:03:34.045546	Cleber	login
2025-11-25 23:35:35.953722	Zainab Ibrahim	login
2025-11-26 03:35:26.850721	Zainab Ibrahim	login
2025-11-26 03:57:09.299778	Zainab Ibrahim	login
2025-11-26 05:36:44.152904	Zainab Ibrahim	login
2025-11-26 11:08:20.170088	Zainab Ibrahim	login
2025-11-26 11:18:18.291172	Márcio Castro	login
2025-11-26 11:18:20.038702	André Wüst Zibetti	login
2025-11-26 11:18:23.842838	Gabriel Vinícius Heisler	login
2025-11-26 11:18:46.093184	Simone Silmara Werner	login
2025-11-26 11:22:15.571822	Joshua Cruz	login
2025-11-26 18:58:15.97919	Cleber	login
2025-11-27 00:19:49.748639	Cleber	login
2025-11-27 11:11:00.728094	Zainab Ibrahim	login
2025-11-27 11:14:24.215395	Márcio Castro	login
2025-11-27 11:22:49.770182	Joshua Cruz	login
2025-11-27 11:28:16.061759	Zainab Ibrahim	login
2025-11-27 12:04:02.523403	Joshua Cruz	login
2025-11-27 12:54:50.055965	Cleber	login
2025-11-27 13:26:35.268959	Cleber	login
2025-11-27 13:46:28.084444	Márcio Castro	login
2025-11-27 17:15:09.708563	Cleber	login
2025-11-27 20:11:39.342136	Cleber	login
2025-11-27 20:14:39.66059	Sofia Bianchi Schmitz	login
2025-11-27 21:02:30.207716	Cleber	login
2025-11-27 21:10:30.505436	Cleber	login
2025-11-27 21:15:54.794344	André Wüst Zibetti	login
2025-11-27 21:16:19.560562	Lucas Vieira	login
2025-11-28 01:54:11.187012	Pedro Henrique Azevedo	login
2025-11-28 14:33:46.38726	Jonata Tyska	login
2025-11-28 16:32:14.286154	Márcio Castro	login
2025-11-28 16:50:54.16575	Pedro Henrique Azevedo	login
2025-11-28 16:51:01.054506	André Wüst Zibetti	login
2025-11-28 17:10:39.176535	Matheus Machado dos Santos	login
2025-11-28 17:21:32.639235	Cleber	login
2025-11-28 19:12:59.992144	Cleber	login
2025-11-28 19:53:43.96666	Pedro Henrique Azevedo	login
2025-11-28 20:33:37.826951	Lucas Vieira	login
2025-11-28 20:35:46.640693	Simone Silmara Werner	login
2025-11-28 22:05:04.528889	Pedro Henrique Azevedo	login
2025-11-28 22:58:56.198935	Joshua Cruz	login
2025-11-29 00:04:30.849045	Joshua Cruz	login
2025-11-29 02:39:25.581481	Zainab Ibrahim	login
2025-11-29 02:59:55.28809	Zainab Ibrahim	login
2025-11-29 03:16:40.501944	Zainab Ibrahim	login
2025-11-29 03:32:44.843921	Joshua Cruz	login
2025-11-29 04:14:33.257761	Zainab Ibrahim	login
2025-11-29 06:27:08.39854	Zainab Ibrahim	login
2025-11-29 14:53:18.560591	Pedro Henrique Azevedo	login
2025-11-30 01:58:06.085717	Joshua Cruz	login
2025-11-30 04:22:30.227241	Joshua Cruz	login
2025-11-30 11:45:16.017082	Zainab Ibrahim	login
2025-11-30 13:39:01.174888	Zainab Ibrahim	login
2025-11-30 13:39:10.526103	Zainab Ibrahim	login
2025-11-30 23:23:59.415252	Zainab Ibrahim	login
2025-12-01 00:01:46.720674	Cleber	login
2025-12-01 00:47:39.062134	Joshua Cruz	login
2025-12-01 10:31:02.977393	Márcio Castro	login
2025-12-01 11:34:05.351826	Simone Silmara Werner	login
2025-12-01 12:32:24.889946	Márcio Castro	login
2025-12-01 12:34:10.439764	Francisco de Paula Lemos	login
2025-12-01 13:12:37.04421	Pedro Henrique Azevedo	login
2025-12-01 13:25:10.429289	Zainab Ibrahim	login
2025-12-01 13:42:26.090222	Joshua Cruz	login
2025-12-01 17:14:09.49033	Eduardo Vinícius Faleiro	login
2025-12-01 17:18:20.449812	Joshua Cruz	login
2025-12-01 17:26:24.204946	Zainab Ibrahim	login
2025-12-01 19:01:59.135049	Joshua Cruz	login
2025-12-01 19:12:32.03917	Eduardo Vinícius Faleiro	login
2025-12-01 20:51:42.862823	Cleber	login
2025-12-01 21:03:02.132479	Joshua Cruz	login
2025-12-01 21:04:42.901261	Pedro Henrique Azevedo	login
2025-12-01 21:09:48.254553	Simone Silmara Werner	login
2025-12-01 21:16:21.105241	André Wüst Zibetti	login
2025-12-01 21:23:20.80151	Lucas Vieira	login
2025-12-01 22:00:10.975252	Eduardo Vinícius Faleiro	login
2025-12-01 22:11:21.660759	Sofia Bianchi Schmitz	login
2025-12-01 22:58:14.057815	Simone Silmara Werner	login
2025-12-02 00:12:36.788626	Zainab Ibrahim	login
2025-12-02 01:43:35.943681	Joshua Cruz	login
2025-12-02 11:56:09.417936	Cleber	login
2025-12-02 12:01:38.789625	Márcio Castro	login
2025-12-02 12:36:02.235462	Jonata Tyska	login
2025-12-02 12:56:55.546202	Pedro Henrique Azevedo	login
2025-12-02 13:05:17.216185	Lucas Vieira	login
2025-12-02 13:17:07.570192	André Wüst Zibetti	login
2025-12-02 13:37:49.068346	Joshua Cruz	login
2025-12-02 14:34:50.734188	Carina Friedrich Dorneles	login
2025-12-02 14:44:50.191898	Sofia Bianchi Schmitz	login
2025-12-02 14:50:24.796174	Joshua Cruz	login
2025-12-02 16:42:50.925642	Márcio Castro	login
2025-12-02 17:33:45.636036	Francisco de Paula Lemos	login
2025-12-02 18:03:57.884182	Lucas Vieira	login
2025-12-02 18:19:32.640151	Joshua Cruz	login
2025-12-02 18:35:32.645213	Sofia Bianchi Schmitz	login
2025-12-02 19:12:19.159275	Zainab Ibrahim	login
2025-12-02 19:14:35.992511	Márcio Castro	login
2025-12-02 19:16:54.257722	Eduardo Vinícius Faleiro	login
2025-12-02 19:29:26.85713	Lucas Vieira	login
2025-12-02 19:39:15.737941	Cleber	login
2025-12-02 20:38:23.997597	Lucas Vieira	login
2025-12-02 20:57:02.287873	Márcio Castro	login
2025-12-02 21:04:49.057715	Joshua Cruz	login
2025-12-02 21:08:30.202641	Jonata Tyska	login
2025-12-02 21:11:53.356573	Pedro Henrique Azevedo	login
2025-12-02 22:12:06.454347	Pedro Henrique Azevedo	login
2025-12-02 22:37:03.717327	Francisco de Paula Lemos	login
2025-12-02 23:27:51.715962	Lucas Vieira	login
2025-12-03 01:19:24.137938	Joshua Cruz	login
2025-12-03 02:14:05.263324	Sofia Bianchi Schmitz	login
2025-12-03 04:06:18.894683	Cleber	login
2025-12-03 11:06:55.793386	Simone Silmara Werner	login
2025-12-03 11:13:10.235531	Gabriel Vinícius Heisler	login
2025-12-03 11:13:28.468038	André Wüst Zibetti	login
2025-12-03 11:24:18.709073	Jonata Tyska	login
2025-12-03 11:37:53.487761	Cleber	login
2025-12-03 12:03:35.234286	Sofia Bianchi Schmitz	login
2025-12-03 12:32:53.041338	Carina Friedrich Dorneles	login
2025-12-03 12:48:15.734397	Márcio Castro	login
2025-12-03 13:20:02.900342	Sofia Bianchi Schmitz	login
2025-12-03 13:20:26.270297	Lucas Vieira	login
2025-12-03 14:49:22.601588	Márcio Castro	login
2025-12-03 15:11:11.764071	Joshua Cruz	login
2025-12-03 15:26:24.874041	Sofia Bianchi Schmitz	login
2025-12-03 15:26:58.494598	Lucas Vieira	login
2025-12-03 15:54:35.984835	Gabriel Vinícius Heisler	login
2025-12-03 16:30:53.295106	Carina Friedrich Dorneles	login
2025-12-03 16:36:05.686425	Lucas Vieira	login
2025-12-03 18:02:04.339826	Cleber	login
2025-12-03 18:45:46.586985	Joshua Cruz	login
2025-12-03 19:11:50.618227	Eduardo Vinícius Faleiro	login
2025-12-03 19:41:04.219461	Lucas Vieira	login
2025-12-03 20:06:58.127683	Joshua Cruz	login
2025-12-03 20:07:07.459969	Lucas Vieira	login
2025-12-03 20:16:13.316901	Sofia Bianchi Schmitz	login
2025-12-03 20:53:08.897136	Pedro Henrique Azevedo	login
2025-12-03 20:53:55.29893	Joshua Cruz	login
2025-12-03 23:56:52.017235	Cleber	login
2025-12-04 01:25:54.9745	Joshua Cruz	login
2025-12-04 11:02:34.548297	Márcio Castro	login
2025-12-04 11:12:44.223696	Francisco de Paula Lemos	login
2025-12-04 11:16:53.747467	Cleber	login
2025-12-04 14:13:24.323613	Joshua Cruz	login
2025-12-04 14:22:29.78012	Cleber	login
2025-12-04 15:37:11.684623	Everton	login
2025-12-04 15:40:41.932926	Everton	login
2025-12-04 16:42:55.432153	Eduardo Vinícius Faleiro	login
2025-12-04 16:43:21.199277	Eduardo Vinícius Faleiro	login
2025-12-04 16:43:29.746031	Eduardo Vinícius Faleiro	login
2025-12-04 16:44:43.7161	Eduardo Vinícius Faleiro	login
2025-12-04 17:13:58.055206	Joshua Cruz	login
2025-12-04 17:57:44.147006	Francisco de Paula Lemos	login
2025-12-04 20:29:59.736286	Eduardo Vinícius Faleiro	login
2025-12-04 20:31:48.543246	Lucas Vieira	login
2025-12-04 21:01:31.540593	Sofia Bianchi Schmitz	login
2025-12-04 21:10:01.557116	Sofia Bianchi Schmitz	login
2025-12-04 21:14:26.20794	Sofia Bianchi Schmitz	login
2025-12-04 21:18:16.733813	Sofia Bianchi Schmitz	login
2025-12-04 21:27:58.421917	Sofia Bianchi Schmitz	login
2025-12-04 23:59:21.214931	Cleber	login
2025-12-05 14:53:26.429328	André Wüst Zibetti	login
2025-12-05 16:59:19.012708	Eduardo Vinícius Faleiro	login
2025-12-05 17:16:33.005888	Márcio Castro	login
2025-12-05 17:22:08.15398	Jonata Tyska	login
2025-12-05 17:36:04.028069	Matheus Machado dos Santos	login
2025-12-05 18:36:39.057209	Cleber	login
2025-12-05 18:48:24.760641	André Wüst Zibetti	login
2025-12-05 19:01:39.597356	Eduardo Vinícius Faleiro	login
2025-12-05 19:13:18.738074	Eduardo Vinícius Faleiro	login
2025-12-05 20:28:22.453672	Cleber	login
2025-12-05 20:58:18.157246	Márcio Castro	login
2025-12-05 22:23:06.525667	Cleber	login
2025-12-05 23:14:03.186317	Eduardo Vinícius Faleiro	login
2025-12-05 23:16:03.918434	Eduardo Vinícius Faleiro	login
2025-12-06 00:15:55.127912	Cleber	login
2025-12-06 13:37:42.577446	Jonata Tyska	login
2025-12-06 13:41:27.255703	Márcio Castro	login
2025-12-06 14:32:27.848641	Gabriel Vinícius Heisler	login
2025-12-06 14:36:29.224227	Márcio Castro	login
2025-12-06 14:50:42.233992	Cleber	login
2025-12-06 17:27:50.386509	Francisco de Paula Lemos	login
2025-12-06 17:33:34.589763	Francisco de Paula Lemos	login
2025-12-06 17:34:04.020206	Francisco de Paula Lemos	login
2025-12-06 17:37:50.625823	Cleber	login
2025-12-06 18:13:30.643371	Francisco de Paula Lemos	login
2025-12-06 18:36:51.666621	Francisco de Paula Lemos	login
2025-12-06 18:53:58.033368	Francisco de Paula Lemos	login
2025-12-07 02:12:50.985874	Joshua Cruz	login
2025-12-07 17:10:56.585336	Jonata Tyska	login
2025-12-07 19:30:01.87173	Gabriel Vinícius Heisler	login
2025-12-08 10:46:42.064431	Francisco de Paula Lemos	login
2025-12-08 11:09:17.507484	Márcio Castro	login
2025-12-08 11:11:30.254998	Cleber	login
2025-12-08 12:09:15.503387	Jonata Tyska	login
2025-12-08 13:08:03.457286	Joshua Cruz	login
2025-12-08 13:08:28.125321	Joshua Cruz	login
2025-12-08 13:08:52.733551	Joshua Cruz	login
2025-12-08 13:09:47.601516	Joshua Cruz	login
2025-12-08 13:10:55.231971	Joshua Cruz	login
2025-12-08 13:19:24.951934	Joshua Cruz	login
2025-12-08 13:20:22.870077	Gabriel Vinícius Heisler	login
2025-12-08 13:39:30.024034	Márcio Castro	login
2025-12-08 14:43:17.894026	Jonata Tyska	login
2025-12-08 16:09:43.214126	Lucas Vieira	login
2025-12-08 16:25:10.336823	Francisco de Paula Lemos	login
2025-12-08 17:16:21.302831	Eduardo Vinícius Faleiro	login
2025-12-08 17:37:10.170806	Francisco de Paula Lemos	login
2025-12-08 17:40:30.498947	Lucas Vieira	login
2025-12-08 18:02:03.425573	Mariana Amaral Steffen	login
2025-12-08 18:15:10.700411	Joshua Cruz	login
2025-12-08 18:31:44.711701	Márcio Castro	login
2025-12-08 18:34:54.851827	Francisco de Paula Lemos	login
2025-12-08 19:20:50.908024	Simone Silmara Werner	login
2025-12-08 20:01:17.324154	André Wüst Zibetti	login
2025-12-08 20:14:04.215985	Eduardo Vinícius Faleiro	login
2025-12-08 20:14:15.543975	Joshua Cruz	login
2025-12-08 22:08:05.428834	Cleber	login
2025-12-08 23:11:45.788807	Cleber	login
2025-12-09 00:04:06.251856	Sofia Bianchi Schmitz	login
2025-12-09 00:32:53.204948	Márcio Castro	login
2025-12-09 11:18:54.225913	Cleber	login
2025-12-09 11:26:03.795623	Cleber	login
2025-12-09 11:36:11.928057	Joshua Cruz	login
2025-12-09 11:41:24.515586	André Wüst Zibetti	login
2025-12-09 13:11:29.42363	Márcio Castro	login
2025-12-09 13:55:17.089285	Francisco de Paula Lemos	login
2025-12-09 14:02:15.943409	Joshua Cruz	login
2025-12-09 14:59:28.297995	Lucas Vieira	login
2025-12-09 15:20:36.723817	Lucas Vieira	login
2025-12-09 16:51:35.107028	Simone Silmara Werner	login
2025-12-09 17:14:45.114999	Francisco de Paula Lemos	login
2025-12-09 17:49:05.343077	Eduardo Vinícius Faleiro	login
2025-12-09 17:50:40.157763	Jonata Tyska	login
2025-12-09 18:15:59.614504	Márcio Castro	login
2025-12-09 18:54:17.543462	Francisco de Paula Lemos	login
2025-12-09 19:10:51.432886	Joshua Cruz	login
2025-12-09 19:11:33.429761	Eduardo Vinícius Faleiro	login
2025-12-09 19:11:41.948002	Eduardo Vinícius Faleiro	login
2025-12-09 20:10:29.509174	Gabriel Vinícius Heisler	login
2025-12-09 20:12:09.246627	Francisco de Paula Lemos	login
2025-12-09 20:44:46.699949	Eduardo Vinícius Faleiro	login
2025-12-09 21:43:05.674931	Matheus Machado dos Santos	login
2025-12-09 21:43:13.273668	Matheus Machado dos Santos	login
2025-12-09 22:40:57.716141	Cleber	login
2025-12-09 22:46:51.065499	Cleber	login
2025-12-10 00:45:34.543161	Cleber	login
2025-12-10 02:17:01.207245	Pedro Henrique Azevedo	login
2025-12-10 10:28:50.889993	Pedro Henrique Azevedo	login
2025-12-10 10:29:52.172971	Márcio Castro	login
2025-12-10 11:14:38.655481	André Wüst Zibetti	login
2025-12-10 11:47:12.311965	Lucas Vieira	login
2025-12-10 11:54:06.933526	Márcio Castro	login
2025-12-10 12:39:51.268986	Gabriel Vinícius Heisler	login
2025-12-10 13:16:45.492938	Márcio Castro	login
2025-12-10 14:12:56.423052	Márcio Castro	login
2025-12-10 14:31:54.726934	Everton	login
2025-12-10 15:01:28.476994	Joshua Cruz	login
2025-12-10 17:43:22.579765	Cleber	login
2025-12-10 18:27:16.888971	Francisco de Paula Lemos	login
2025-12-10 18:28:25.642331	Márcio Castro	login
2025-12-10 18:34:14.694043	André Wüst Zibetti	login
2025-12-10 18:44:29.137421	Joshua Cruz	login
2025-12-10 18:46:07.257169	Eduardo Vinícius Faleiro	login
2025-12-10 19:32:37.100213	Cleber	login
2025-12-10 20:11:33.442423	Eduardo Vinícius Faleiro	login
2025-12-10 21:02:08.22033	Joshua Cruz	login
2025-12-10 22:18:06.169082	Mariana Amaral Steffen	login
2025-12-10 22:35:57.004946	Eduardo Vinícius Faleiro	login
2025-12-10 22:40:41.029808	Cleber	login
2025-12-11 00:16:11.592477	Joshua Cruz	login
2025-12-11 00:55:19.376046	Francisco de Paula Lemos	login
2025-12-11 01:28:35.143008	Joshua Cruz	login
2025-12-11 10:35:12.192227	Cleber	login
2025-12-11 11:01:23.577107	Márcio Castro	login
2025-12-11 11:01:46.191623	Jonata Tyska	login
2025-12-11 11:07:49.443806	Márcio Castro	login
2025-12-11 11:20:46.203476	Greici Capellari	login
2025-12-11 11:25:49.017757	Joshua Cruz	login
2025-12-11 12:56:33.527268	Everton	login
2025-12-11 13:04:50.878413	Márcio Castro	login
2025-12-11 13:42:17.969265	Greici Capellari	login
2025-12-11 13:53:59.334446	Carina Friedrich Dorneles	login
2025-12-11 14:04:19.410696	Lucas Vieira	login
2025-12-11 14:04:45.079632	Eduardo Vinícius Faleiro	login
2025-12-11 14:44:18.956207	Joshua Cruz	login
2025-12-11 15:01:44.261021	Francisco de Paula Lemos	login
2025-12-11 15:09:48.41497	Mariana Amaral Steffen	login
2025-12-11 16:09:57.73279	Lucas Vieira	login
2025-12-11 16:18:57.170153	Gabriel Vinícius Heisler	login
2025-12-11 16:41:36.032584	Paulo Marcos	login
2025-12-11 17:43:51.923198	Paulo Marcos	login
2025-12-11 17:50:40.857913	Greici Capellari	login
2025-12-11 19:43:14.395876	Joshua Cruz	login
2025-12-11 20:08:51.225629	Cleber	login
2025-12-11 21:30:04.594341	Cleber	login
2025-12-11 21:35:00.202994	Lucas Vieira	login
2025-12-11 22:02:12.826351	Pedro Henrique Azevedo	login
2025-12-12 00:51:32.071062	Sofia Bianchi Schmitz	login
2025-12-12 01:25:17.660344	André Wüst Zibetti	login
2025-12-12 01:36:26.336772	Pedro Henrique Azevedo	login
2025-12-12 02:41:06.570345	Sofia Bianchi Schmitz	login
2025-12-12 11:52:47.603776	Paulo Marcos	login
2025-12-12 11:56:27.734221	Sofia Bianchi Schmitz	login
2025-12-12 13:10:26.149159	Lucas Vieira	login
2025-12-12 13:23:10.684066	Márcio Castro	login
2025-12-12 13:58:17.631406	Carina Friedrich Dorneles	login
2025-12-12 14:04:34.773108	Francisco de Paula Lemos	login
2025-12-12 14:19:12.945211	Lucas Vieira	login
2025-12-12 14:21:09.809091	André Wüst Zibetti	login
\.


--
-- Data for Name: log_user; Type: TABLE DATA; Schema: audit; Owner: -
--

COPY audit.log_user (id, cpf_user, url_backend, data_acesso) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: audit; Owner: -
--

COPY audit.users (cpf, id_pessoa, nome, tipo_acesso, email, cpf_crypt) FROM stdin;
2892164001	100000001448920	Matheus Machado dos Santos	completo	\N	\\xc30d0407030276cdcee1d483fa997ad23b0170a0f42f064600ad84690f56fce15632e5b5f9fdeb7934e4d1e9d1c68f019904b9512242e20bbcb5a6530e531e1f479f85f2e91ffffe34659ba8
987216902	\N	Patrick Varela	completo	pvarela@mpsc.mp.br	\\xc30d04070302e56ec01a59318b3578d23a018629aec1ef320684483f678fda9ac9f93fcf420fc12ea90aa626df66b85d8dac251013e64aa5a0f01c3c5a088a9e581c2c83bc0cf87bbdd0ca
6935194954	100000001278239	José Eduardo Medeiros Jochem	completo	\N	\\xc30d040703026aa10f12ad77d2cf79d23b016a3cddb451f8b24ada91014f0049fb0e4d0546f91ce34b2339ba0f6dc0f0e1dfa484dd5dba31e35fc715d0d0950ec4bf52b7be8cb128e03cc1af
9646242901	100000000775755	João Pedro Dell Osbel da Silva	completo	\N	\\xc30d040703026d878df747feb43976d23b01e3744e4d903bb7c1c66485c4aba65b1ea1fa95686dc24e45e1a00bd5491619c7d5f351ad7013738806555fc0961a94dde965f38806b168263a80
82841756068	\N	Fabrício Pinto Weiblen	completo	fweiblen@mpsc.mp.br	\\xc30d040703029e65c0b9a724abb67bd23c0113d16dcccc5600f43539f0ec05222605d073b3617e05ea2a8c8faa25066c6b61eadd95344d7d75e1461908a617491a96441100a90ec25a27997213
84879980978	\N	Milani Maurílio Bento	completo	mbento@mpsc.mp.br	\\xc30d040703026f3deba3159f38b77cd23c01b542a1408bf6c0d9f7b2743464985367ce7d849c06cd9414232030d860915819f86d38a38f24a0ddf3892ec07b91a993f4cce9e0c9c28ab8b9e93b
3117319964	\N	Marina Modesto Rebelo	completo	mmodesto@mpsc.mp.br	\\xc30d04070302841362b7f33da03063d23b01c384cf4e2822609a28fdccda3a68623fb05a7bf7b92c6b68a0bc95bccc2832c2aa5b28cedd96fc489ccb13efcd9ade9f0759ef4b70b86b67b940
6538469914	\N	Lucas dos Santos Machado	completo	lsmachado@mpsc.mp.br	\\xc30d04070302cae6d0ef883232d862d23b01a2fab82429e837c55828eaddcff23276fb56a68dd28489ffb6022d49c2d521df0e8d19b6c3dd64160cc0450144a677400e05ed16f3ce85be532d
5719723900	\N	Fernando Jahn Bessa	completo	fjbessa@mpsc.mp.br	\\xc30d0407030241367f27da8d112169d23b0193273b5d2c0f8fe32334849afc5ff39ddba5583d5f1b2f20e10bb8736998c0d5280fb60873d310f170e7a951e256c257af202e090f99dc53d3bf
13241750957	\N	Felipe	completo	\N	\\xc30d04070302b42e1600e212308e6cd23c013f03a279df93d0b9f31c7bf2a53d37f216288e8e17f394e99f106df521d69d6d8f148c9cc0bf08974a527151f46fae64346b853ec82554ad488f81
6951853908	\N	Luis	completo	\N	\\xc30d04070302d12623e69027c0c468d23b016af90d4573046eef7c97670dd5481497784822600aba98b4efdfa4cbd9df34581e5d919c049e2cc8135ee5c59dd9d5c5fbd3931c750d8529a6b0
195779150	\N	Vitória Soares dos Santos	completo	\N	\\xc30d04070302818bc991970f8d1873d23a0178bc3beb20bbd239c96ba47e47092e692c7a1113e9836ec8e5f3d2a9573387c61bdba53a75a22502b5ea2111833774b42b5a9441412c7e445c
2105746152	\N	Tatiana Popia Freitas	completo	\N	\\xc30d04070302ef53b0a452bfeca26fd23b01ac47f648285be61b04444b63f9b33153465059b21a051e980d7c808d79f45ea10134efe8b4a0313e8f71726e687c9a15f9458784925ccc81eb3c
13305595680	\N	Cleber	completo	clebertonoliveira.cnt@gmail.com	\\xc30d04070302fa8dd42a129fb78f6cd23c01b2f2960c617ded3ffda82e1270803c083e44b78fc2649a3fc0a064b0cf83ef0ef74ce44e46b326227781b4a19bcce8b64341aed08611f36bdd9463
3280133904	\N	Rubens Orbatos da Silva Neto	completo	rneto@mpsc.mp.br	\\xc30d040703026018cf29db4f58e369d23b01509f99505d6f5f5c934109810ba60ab512544f9aeaf9f88486fbc351500f95b8501ecd06ed192b9dd6add8ae6ce4c6c118b6938f6ab65868652a
2403115746	\N	Patrícia Maria Quintanilha de Moura	completo	\N	\\xc30d040703022dcb475944603cef62d23b0104bc206e9cb5faf1693cf0011af13eabed80011444708ce04367edef7baa053bdf1180865bdf65ad369238ab9847f8f104b4845c16e8520d1835
370772016	\N	Márcio Castro	completo	mbcastro@gmail.com	\\xc30d04070302c093d4576fba07187bd23a01abc03d19387296bebd021524e25d5a1f54a987e54a0e54e1a34070a71440e75ae01ab9995da5150f3115b6c3bdd5711700b64e3d7c1c30dd6b
2342616929	\N	Leandra do Rocio Santos Geraldo	completo	lrsantos@mpsc.mp.br	\\xc30d040703021c6e37d0ab82f89b69d23b01047c737e4fe05731a81448166bf14f478314aaa696acffb58497641b33d275238c6b46992f9fcfba408861fbbd4877e9abe6561392b7eb3bd580
12083639995	\N	Breno	completo	breno@breno.com	\\xc30d040703029cfc6ccb26c510af64d23c01915eb1e61a1f0e44c02929e72629a77eabf014547b1899760c70532fb6c73ca51f3d6083753c20888b9c3cb0b3578754da3926c04b0a6c0e5bcbb6
92183425091	\N	Carina Friedrich Dorneles	completo	carina.dorneles@ufsc.br	\\xc30d0407030245825c616bf0af976ad23c0107458c5b68e03973f7079886dedb404f87cd045fa5384d47c55d59f3a3e271556b2e84dfd771b7b34a21ebcdf8583a382c86eadd0779e49e67b460
03852383048	\N	Arthur Erpen	completo	\N	\\xc30d0407030277e70b7bec52d82465d23c01f3377fb7125ec4bcf3b2be0d177f24d115b6328346393c55c9c7a1b7aaa9c366c31e1ec29fe8a7f53f77ee252372b848ec53fe4725f37a4c3a55fa
2990345000	\N	Greici Capellari	completo	greicicapellari@gmail.com	\\xc30d0407030273c6b85a106fd6566fd23b01d804aacb7aa60b43a32a756d4740d56c1dc49e6600b493c4bbf775b91dba6dd748d6d04c6d0c8657b897cf13dcba0b27d0ec247befcc636095cb
3928877038	\N	Gabriel Vinícius Heisler	completo	gvheisler@gmail.com	\\xc30d040703024b7211db522b47a06fd23b01ee4858cfd064e541dd9e17408daed0b2590be4753229cf9b7d4f98e97726630dcce853b65a41724d541c4882cb5412e4cec031afda3b1a4f3dda
10606900632	\N	Pedro Otávio Lima Gazzola	completo	\N	\\xc30d04070302b6cfa12d83f9094862d23c019bfd577b37e845566f79bd193d8cf8c68df4f171879bccc7b50e483058c55a0d81b2e4de3d494d4dce57539ce38ba9c1c7789cc92fce59a67ca564
86679953120	\N	Joyce Lustosa Belga	completo	\N	\\xc30d04070302147642dc80a8a8e066d23c01b45fcfd3708aa74f30c4808176c4fbbe6a617df84e374e89febfd4c037182733161ad91fc1282687569fc0731f7b13e7e85fb80a31129055d17eec
2547485460	\N	Alysson Barros de Morais	completo	\N	\\xc30d04070302314569b95dea2edd76d23b0121d12316dcef41dd39243a99c2ce675360a9c9044cc2d3e80fb8a3ed8177da55335532f80b278c9a1b4d7e2b29c17247ded077c9481e5786a4e4
57527563168	\N	Alessandro de Oliveira Borges	completo	\N	\\xc30d0407030235b6868efb5995886ad23c01389006d4d0d7035ca6950d1e05ffa82508df745629a1441c21733627257310881251e5c903552e678355fa986ef245fe4497d77ee37fd5432b5aaa
1580711154	\N	Christopher Bruno Costa Aviz	completo	\N	\\xc30d04070302cf0e3a10a1be72ef7bd23b01a681f652b65b675da153833e41df1eb5534aa6ee6dbeb5b19dbe1d6745183775ced2fd4fb3b7e35c9b569a003cc92f28f8fe11dba6b3c09a1021
90563034734	\N	Fernando Rodrigues João Júnior	completo	\N	\\xc30d0407030283ea9725774fb1a66ed23c012115bd0317d47eed334dca94ece7f64e6571004d423c6c250fa9fb512a57f805f8b07a2de939fbea3960113efb9f22db06b7f81e03ba275a2767ec
4305155966	\N	Guilherme Martins Willemann	completo	\N	\\xc30d0407030278585041d90dd3ed6cd23b015b3b88ac3adac8830ff54e6d53cbd7ffc84fed57bbdbbe4619a944940f561c5a33db515e30fd901f78ec528683acc2257629940cea97eb1590cd
3591503304	\N	Ticiana Linhares Coelho da Silva	completo	\N	\\xc30d04070302bb5a981ade46988374d23b01aa7d4a688655f36efd251e15229e865d62009fb671069ccec8b44cc80cdf988343b75f71915169aa4403019e610856dcf97cce7b9c834161c3f5
80056540906	\N	Lucas Vieira	completo	\N	\\xc30d040703024561788ced1a5ef874d23c0179e99beaaeb990b275b8fe016f3e6c81961254df9ddf6eff9a9b44c34b705913aeccbd02644e3d5d4575410cd3f47e00cb519501bede4f1463a1f6
4992521959	\N	Simone Silmara Werner	completo	simone.werner@ufsc.br	\\xc30d04070302c1414d5d0bdf19ec6dd23c01ddaac870ee07d4bfaac7f2032d7f143380491f3fc4d93a02dfca0baa6b6e6fd163dcd40f233df2aa550418d8ab06655c375f9300ecb8a1de74b0b4
14530537943	\N	Myllena	completo	\N	\\xc30d040703022426ffa7719efb9766d23c013829723920e2175ec03051a621c8561d291994be7a7c07c4bbea3003127f28bbe2e4b40e799c11709333dd432671b7b128a2161adc7f9e659ded61
52990591249	\N	Hudson Afonso Batista da Silva	completo	hudson.silva@ifpa.edu.br	\\xc30d04070302d93ec6bddeb646db74d23c011b014ab7b90753f51dc727051bc8147f053d3e033f697363e6582d8dfb2995162579a5269f314b3df98ffc8104fc46b591d9b84dee85caae70180a
7005063902	\N	Everton	completo	\N	\\xc30d040703021325ed38284b6b5e65d23b0150e1359383c7a113c3bbf7e2b9063e9e3feb1cdadc3757daf348be7f42ab1bec4259c562799dccd2ebc2330d8130c0b608a56f555d038cd01600
2669179096	\N	André Luis Blanco Strohschoen	completo	sb.andreluis@gmail.com	\\xc30d04070302fd363d5b9de3c80a74d23b01d0d9b9326e429c7462feb95f01d0ad1a2b1d0b1469aaa9d5412251534e9555406111ebeaba1582ab31b0af3b1b8ea8035925ece2912a8dd7ad84
9916239754	\N	Adriana Ferraz	completo	aferraz@mpsc.mp.br	\\xc30d04070302fdd21f6f5092fee575d23b01bce5924001c40d30fb78b65c3adcf9f0bf0ac5c3fb08703057ab40ae0c49233ec1cbea3e16503f48f8a40c2f2b7ef606053c4841abad006ecb1b
46113642836	\N	Paulo Marcos	completo	paulo.marcos.de.assis@gmail.com	\\xc30d04070302bd7239feb8c305e469d23c01766649f47a092f8d9709b29f655e13e39362e132e3dbafa33d1847fa166beebde385e8001344b9e9eb9984adab11ccd47212615edb155f804d879e
8649436951	\N	Roberta Eduarda	completo	robertaeduarda06@gmail.com	\\xc30d04070302d0baaafdcd7342dc7cd23b018be3d9feac4f74386f8da059197e490bdba058529255e17fa984cf63b83d9a76acbb99607f05f731b332ee4eb9050fd8482612554cda92b5c4cd
7622103977	\N	Leticia Boaroli Back	completo	lbback@mpsc.mp.br	\\xc30d040703029ecc1c24836eb55c60d23b01233cf5e96eeff6f2cd1df77e8fb7c15a18d7219cca9ccc34dfb1920b623afd292e8cbd60f13d1ff2889b23a460b4c45a30d43e5858e30fdb8a91
7935600988	\N	Otávio Augusto Bennech Aranha Alves	completo	oaranha@mpsc.mp.br	\\xc30d040703029a18474b01e4159f7ed23b01276517f387d047a7c9c6c39ca9cc4865b14451bd14394d75bb591529d463cd9f257342d6c8572ba166067e611c342d819f58534165a5842099ef
3592954954	\N	Paulo César Allembrandt	completo	pallebrandt@mpsc.mp.br	\\xc30d040703026320641f3ea4184d6cd23b01d811a28c2b1fddd5277fcaa72bcc54901b3b44308b17f3232f4fda03c3368a0417ad1a0a051ff231979e735dd49da1b6f079ebdea12d0cb7d2cc
6812505935	\N	Lanna Gabriela Bruning Simoni	completo	lsimoni@mpsc.mp.br	\\xc30d04070302f409d775226c9e5272d23b01f0b4c7ac759c0790af53ac63effd67d74bcff825ce882b24cbe9d1adfae65946ecd1d7e46f5fb2a83f466dc2a60c1ded8bea8c1771643bac5f4e
4115194928	\N	João Paulo Biachi Beal	completo	jpbbeal@mpsc.mp.br	\\xc30d040703023cb05e1a43d07b576fd23b015eb8ac7afe0080698d63c54061f6728975128e28b5c4f70540eae2256db19fa42090d8331768b5d0077a19f98d973d27917004388cccd6865abb
4035498920	\N	Rafael Bortoli	completo	rbortoli@mpsc.mp.br	\\xc30d0407030205fed0be871c20f066d23b0122650184872981c30c752329ff98530fc41b4296ecd3973d1a6c7216c199eccc70f63e204632240eb0eae5ad3e6d6f36507eefbc32b953f73001
4255421900	\N	Cristóvão Claudinei Morvan	completo	ccmorvan@mpsc.mp.br	\\xc30d04070302fac3be9eff42e40060d23b0122f03c514bfb65123ff6a01c609933e27dc75297aba6fafd865a6a95cfaddc5a17ea76b18eb794f9ec2cf03589e09eca3d77ea9a33a02c6dbc02
7426468909	4321	Joshua Cruz	completo	joshua.cruz0520@gmail.com	\\xc30d04070302b2a4ae3990bf120f62d23b01c4f498dd509f9e4c2db241a7cab77bd942739824141ad60916683e96a9163928c104cab67bc432985dda405092fd3e394dd5381b7ebb4159f442
2938404905	\N	André Teixeira Milioli	completo	amilioli@mpsc.mp.br	\\xc30d0407030224f6a953396c643c78d23b014c196a8fe55442b1d62067dbf0078bb722f04bba16f1595a62d28d7af6c63c7be3a617620296c42bf3b12004fda00a4991b1c16d1a5a86e7bf32
2917900970	\N	Douglas da Silveira	completo	dsilveira@mpsc.mp.br	\\xc30d0407030201a3beb0d1cead7661d23b01df552480f0f1554c76e341f804aa35faafa6bcdae9c1ec8f636982c1eca4ba9e44cf4cd3ae5fc9d390b458bf922847858e4bd63767c7a48669ec
1729529992	\N	Edair do Amaral	completo	eamaral@mpsc.mp.br	\\xc30d0407030218eee7a6baf0ad7b73d23b01372a24364272f668aea8ecd5f7f1531f0b7d230445a9ccbb7db6df6e6e5928fb9b2dae6771679928a9c2b807fc5f530b7d506bccbb11f105fee4
2082333930	\N	Eder Moreira Ribeiro	completo	emribeiro@mpsc.mp.br	\\xc30d04070302850d0dcf82e0473b70d23b0106c1dc59a542842976d6ede1c4c9a5ec451e582a05345482a0ddb6ebad688aae12b282f7e0de50b5e194cc4d926616f7be09723dc1d28cb7ac06
89464249900	\N	Elton Davi Staub	completo	edstaub@mpsc.mp.br	\\xc30d04070302302f3820eee8f0887ad23c01ad8e3fac7b040a8b5469c2ce83ff58c402f60c4821eb6c5bf8dfac528b4ef39033431e1ec63c9799c1f4f359c0552d581c1f89ecda5d0ffca85dab
448316927	\N	Marcos Augusto Brandalise	completo	mbrandalise@mpsc.mp.br	\\xc30d04070302bf29f48d6838691a66d23a0133b57c45df2ae27a493a4a02d318f73a3cdc89dcf546b58ea254a42e5a9646bebe96cdde0ffd53af109fec1299c949e3e63c8c388f2494b6fb
88808785904	\N	Ricardo Viviani de Souza	completo	rsouza@mpsc.mp.br	\\xc30d04070302a699238155162f7d69d23c015e113a31d9c033a10f369f515d1c4f63d014f456f2947fe3fa1ffe0b9f8a3852fac454dd5a87d2c300ff04f3186a708fbad30eaf785a082ccf28ca
94749167991	\N	Eduardo Varella Vieceli	completo	\N	\\xc30d04070302ea5aa73b3a95e25b7ed23c0149510f06ead199c2a9142a42b59d6eafecf02f87936dc11436f6323c74a482603a1cc22d58462c201b5056e574004c91c2d165a6013f0796e2edc7
2620841984	\N	Jerusa Marchi	completo	jerusa.marchi@ufsc.br	\\xc30d0407030210a585388cd69da567d23b01dc28cb63efd6c7ebc17cf2b379a31836d8e295394b91395da65b5919e584bd5369c7bcec81f99852be5d4e4a509efb1cbef8fb6cd1008743638e
930125002	\N	Jonata Tyska	completo	\N	\\xc30d040703024c931a2b13febd5d7fd23a013f9f998559b3f82410c91e74d696ee90436d9972c2c77f22d3d115cb153678ca7369527e086835691525ccdd88b02dd4403f18b609fc058714
10631599894	\N	Renato Fileto	completo	fileto@gmail.com	\\xc30d04070302f2ced54d99a2378b61d23c01ecad72d3b06a2f4031f61693c693237f3c0845691bd5fb3c3c76f2e176069379f9b4ee97ae475bcd8bffd7cad307fcdd2d39b6cd98f6d8d24f8ebd
81693680068	\N	André Wüst Zibetti	completo	andre.zibetti@ufsc.br	\\xc30d04070302140d039bda0c770366d23c01c0893eb9d80195e0280178448ae7dfcccfaabc48588ca01599ed89ec91a6f2fdb0f0b7d17d03ffb95ecec2dd612693d77d2fca839d3a2f78052663
8054971966	\N	Fernanda de Ávila Moukarzel	completo	fmoukarzel@mpsc.mp.br	\\xc30d04070302fc594183d32a1e057ed23b010ae09551d207b933b553b3d44f702eee7c1c6669a96d70c265ba40774815a4fd3210ecba041637ff9bc750cc3cc8a8e02d59f496d5dc92a4ca66
2440859940	\N	Jean Pierre Campos	completo	jcampos@mpsc.mp.br	\\xc30d04070302279658ba9579db7e75d23b014386818e4840ffcb1c7a31659b9174439a503965588d49891f71acfb5266accb3b4c45b4832fbab48a555120f9ffdd370eb391497460ea22b463
4480938982	\N	Márcio Vieira	completo	marciovieira@mpsc.mp.br	\\xc30d040703022d260eb8cc77336a6dd23b010abee9d95a036f439c2228b1f7be3edb23ee5b446d1dd7e4f9d49220d92bdc5b45513709c6242f5eda405989dd0eb85473e49c901f451880c16d
13255870950	\N	Mariana Amaral Steffen	completo	marianaamaralsteffen@gmail.com	\\xc30d040703028efdb3efe5725ec86cd23c0117471d7a466ba727bd3aac5e21b304697a9a38c8cbd8eb60c5b97a82bef936adf0399e89563619ad3cd68c90190a1764a4a3fab68e0deaba372e43
5081797936	\N	Welliton Marlon Bosse	completo	wmbosse@mpsc.mp.br	\\xc30d04070302ffcc868c5dc6e88770d23b01eaf02645158cf7e7a2e43cd97bdb7be89587f9b1275fdb52be095870b5301b5507e15edcd0f692255c0823c9aaafcabb8fe4eb78ac9beb12e62e
4122290996	\N	Guilherme Teodoro de Amorim	completo	gtamorim@mpsc.mp.br	\\xc30d04070302eae59823ed01af8666d23b0195dbcf27911afa1704d9b9c183004b9906a8b993c0782bb0638c2c6fa416e49454c83f21cec33033ff3c7bca98ac6583ed8ce35ea0c737ffb805
2903575002	\N	Lívia Corazza Ferrão	completo	livia.ferrao@grad.ufsc.br	\\xc30d04070302ac9bc6f66c7c8c0977d23c011e35d48b65e883a85495b57fe69e363044b692b1e16a99c54ef2633169e01224d9fca8fb68bd8c2ca79f751d434a9df762e0ce8050977b303a25cb
33359125860	\N	João Paulo Schiavon	completo	schiavonjp@yahoo.com.br	\\xc30d040703025dc971b909bbe2ca72d23c01721882be18ac718ebd9a079ca20f3a91ef9c2b603c9b479f8e065492d94db42c935a5b9b2b0c57ea075972db5bc47c35a098357612f263f1f51f83
4847882997	\N	Guilherme Arthur Geronimo	completo	guilherme.geronimo@ufsc.br	\\xc30d040703021384f749d8b0d0b57ed23b01ac135057432176c6ba9c885e809ff6990e1d3f1468057359c1a8e1c6cfb78586eb613f6b6878092424203e3eea47fcb887f6d0d3b89d9f803857
10064364992	\N	Gustavo Konescki Führ	completo	gustavokf2003@gmail.com	\\xc30d04070302f061e68773cfc06266d23c01ef9d92950a5f47a5b1e8c48d82543956a0886a909391e35f05519bb65c4dfaea9583ba8f97eb2377b62b4a3f98371b794ebedbfd54effb74b8b378
9883783965	\N	Sofia Bianchi Schmitz	completo	sofiabschmitz@gmail.com	\\xc30d040703025562875341395fbe6cd23b012701f903ed7fba6eeab7f312bf7e2c0e7858e6eb25773f813cce6613ca44c4b539faf3bde3a4a5bdd608b8903b6f46bce342b5869baaa1ac559c
8166321971	\N	João Victor Albanaes	completo	joaoalbanaes5@gmail.com	\\xc30d040703021fbf41264850a62278d23b01990ddf9c9b903d314f2410e2e5c00a48da844579b07a08a7dd1108547fa242157afa45f3cf2051abcd418de052234863a2fcc283b836cde2c915
7208909938	\N	Ricardo Henrique	completo	ricardohenrique0421@gmail.com	\\xc30d04070302a445380f3c1319ac70d23b015d36ab8c18a15e09c5de7d6823746ea75755e94b11ccc4db1ba99997a8bcf1ddcda3df11e8a9c28d717b9b5172c87ebce5705c3ff21131354a26
10178560952	\N	Hanna de Castro Serratine	completo	HCSERRATINE@mpsc.mp.br	\\xc30d0407030293de6187e5bad9c26ad23c01a657b053dadef2cc0121be29ceaf9fd3d0c71c6c3d75706123e2d03f283f191528d76e2089867fe78dcc04d6e21299554f44d93358216cc115e5ad
11008583936	\N	Maria Eduarda Sagás	completo	MESagas@mpsc.mp.br	\\xc30d040703023f7f1dbd39de1cb074d23c019f930fd3f411255d7422d91e7e267b972f9ac84c329e0ecdd53eff155b38674a7a5fe2f0a2782bfc779db74a6a69bf906aaac44682b58f6f6fcb3c
7213098950	\N	Artur Brandes de Azevedo Ferreira	completo	ABAFerreira@mpsc.mp.br	\\xc30d040703027efaf6cf8620ec7f7ad23b01ffddefb2bb47c97e44982e052dd22c070bb1d55802b74fcffcd50ea71ebf6213179ac897c8522b233f676adcd2df5463aa900fa95df8317cae82
2619894999	\N	Eduardo Sens dos Santos	completo	esens@mpsc.mp.br	\\xc30d04070302d1cd05ba4716471a6bd23b01d5fbbccb57d51927c1fcdb1894dbcdd7a50c4a0eed15c6c2460e585d7fb9687828eb8f48cbeaa47d34f225e43387f400af4b8845ef92c14bff0a
9794460907	\N	Arthur Maeda	completo	akg.maeda@gmail.com	\\xc30d040703027a84e72498f08bff77d23b019497da0e9d5ca27aeb68d1d40e09a199e281f25f80bc2ea4352be44a8ecc21bd90cd789c73fd23a2db16b1cccc9d2c40f799fe0eb01601ac8104
12066836605	\N	Anderson Sales Zambeli	completo	anderson.s.zambeli@grad.ufsc.br	\\xc30d040703027bffdbe9f75b837877d23c018f253a989537412d305c2a10a04ecebd884b36bfc5d7961f58bf0014d726c9c3089d86eb2feb7405ae8397f985619995cba85616e41fbe7ad57c57
2606670051	\N	Zainab Ibrahim	completo	zainabhanadyi@gmail.com	\N
14071772905	\N	Eduardo Cacilha Steinbach	completo	ecacilhaa@gmail.com	\\xc30d04070302951af94712d40ab07cd23c015859c457eb20177405454fe703f7fccc98ed2eeb14ef590db8124a8150beeb90ef1b49473301387cd7d517028c895aeaf9f9b397e7a1a59d20857c
6665009165	\N	Eduardo Farias Ribeiro de Souza	completo	farias.e@grad.ufsc.br	\\xc30d04070302f62614c87187e54e69d23b015e5913f6ec3b0f196a9337e14016a7572dcfd1af77643601401ef41f5384da687f9c73235fb1d9ac78542233b0bdbbe11779431a9b21f5511757
9348593960	\N	Pedro Henrique Azevedo	completo	pedro.henrique.azevedo@posgrad.ufsc.br	\\xc30d04070302f4fffa68e3819ca465d23b0157b28fc93e60b12d187e72b0835487d2bcc1318b383921c348dce2d751ef82047f7cfe7cffe403023ab7e695fce74c377bc7fef51fc4ca9be2c4
3875877055	\N	Eduardo Vinícius Faleiro	completo	eduardoviniciusfaleiro@gmail.com	\\xc30d040703023db01da979bb36017cd23b015758d57c9d32fd5c16947c71ab2d787c47c9e8e0f751b4f1e31aacc6a1645417174a92d5fca0d68264fb779a1f0af4a1b49fc0ddfbc545118544
4004270952	\N	Guilherme André Pacheco Zattar	completo	GZATTAR@mpsc.mp.br	\\xc30d04070302dda01c6c571ab3d675d23b01d908597a9d4547753b40f26e254f02ad6c4003c58359db8d631196f3e8658e23b78472eef00c3b83e48b1b1e8992e5a32885acf93b92bddd920a
7678677936	\N	Francisco de Paula Lemos	completo	franciscolemosfisio@gmail.com	\\xc30d04070302b06fb74e2fa5165776d23b01ed66717c7b375f7f3d05174e24f15f8df3f89a05bc636d2b2cffa0230aa862f6f47edd24b50187e93a1ee57c8c1705279d73decb23ec0fa69225
7966998959	\N	Amabyle Heck	completo	amabyle.heck@gmail.com	\\xc30d04070302425c257103cabf017fd23b0172ee9bb18ce34be51fbe299216576cad7d2e9b91ac406381774c6cb017c778411c4bf32ed8b54407c4740d84cd41cdb439e539b501d66ff1898f
9563527909	\N	Roberta Piskor Gomes	completo	robertapgomes29@gmail.com	\\xc30d04070302c9bf121ba2845d5666d23b010f80cdae4968457a526cd5c412b3569aa6e8d9f72fd9d52b587b7ff923400abeeca3a0c298d098128f4eb175bf5328e107ec9be1b08f12da1a66
\.


--
-- Data for Name: alerta; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alerta (id_alerta, nome, nivel, descricao_longa, descricao_curta, id_execucao_metodo) FROM stdin;
\.


--
-- Data for Name: analise_agente; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.analise_agente (id_analise_agente, id_processo_licitatorio, data_analise, versao_sistema) FROM stdin;
\.


--
-- Data for Name: cnae; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cnae (id_cnae, cnae, descricao) FROM stdin;
1	111301	Cultivo de Arroz
1207	8422100	Defesa
2	111302	Cultivo de Milho
3	111303	Cultivo de Trigo
4	111399	Cultivo de Outros Cereais Não Especificados Anteriormente
5	112101	Cultivo de Algodão Herbáceo
6	112102	Cultivo de Juta
7	112199	Cultivo de Outras Fibras de Lavoura Temporária Não Especificadas Anteriormente
8	113000	Cultivo de Cana-de-Açúcar
9	114800	Cultivo de Fumo
10	115600	Cultivo de Soja
11	116401	Cultivo de Amendoim
12	116402	Cultivo de Girassol
13	116403	Cultivo de Mamona
14	116499	Cultivo de Outras Oleaginosas de Lavoura Temporária Não Especificadas Anteriormente
15	119901	Cultivo de Abacaxi
16	119902	Cultivo de Alho
17	119903	Cultivo de Batata-Inglesa
18	119904	Cultivo de Cebola
19	119905	Cultivo de Feijão
20	119906	Cultivo de Mandioca
21	119907	Cultivo de Melão
22	119908	Cultivo de Melancia
23	119909	Cultivo de Tomate Rasteiro
24	119999	Cultivo de Outras Plantas de Lavoura Temporária Não Especificadas Anteriormente
25	121101	Horticultura, Exceto Morango
26	121102	Cultivo de Morango
27	122900	Cultivo de Flores e Plantas Ornamentais
28	131800	Cultivo de Laranja
29	132600	Cultivo de Uva
30	133401	Cultivo de Açaí
31	133402	Cultivo de Banana
32	133403	Cultivo de Caju
33	133404	Cultivo de Cítricos, Exceto Laranja
34	133405	Cultivo de Coco-da-Baía
35	133406	Cultivo de Guaraná
36	133407	Cultivo de Maçã
37	133408	Cultivo de Mamão
38	133409	Cultivo de Maracujá
39	133410	Cultivo de Manga
40	133411	Cultivo de Pêssego
41	133499	Cultivo de Frutas de Lavoura Permanente Não Especificadas Anteriormente
42	134200	Cultivo de Café
43	135100	Cultivo de Cacau
44	139301	Cultivo de Chá-da-Índia
45	139302	Cultivo de Erva-Mate
46	139303	Cultivo de Pimenta-do-Reino
47	139304	Cultivo de Plantas para Condimento, Exceto Pimenta-do-Reino
48	139305	Cultivo de Dendê
49	139306	Cultivo de Seringueira
50	139399	Cultivo de Outras Plantas de Lavoura Permanente Não Especificadas Anteriormente
51	141501	Produção de Sementes Certificadas, Exceto de Forrageiras para Pasto
52	141502	Produção de Sementes Certificadas de Forrageiras para Formação de Pasto
53	142300	Produção de Mudas e Outras Formas de Propagação Vegetal, Certificadas
54	151201	Criação de Bovinos para Corte
55	151202	Criação de Bovinos para Leite
56	151203	Criação de Bovinos, Exceto para Corte e Leite
57	152101	Criação de Bufalinos
58	152102	Criação de Eqüinos
59	152103	Criação de Asininos e Muares
60	153901	Criação de Caprinos
61	153902	Criação de Ovinos, Inclusive para Produção de Lã
62	154700	Criação de Suínos
63	155501	Criação de Frangos para Corte
64	155502	Produção de Pintos de Um Dia
65	155503	Criação de Outros Galináceos, Exceto para Corte
66	155504	Criação de Aves, Exceto Galináceos
67	155505	Produção de Ovos
68	159801	Apicultura
69	159802	Criação de Animais de Estimação
70	159803	Criação de Escargô
71	159804	Criação de Bicho-da-Seda
72	159899	Criação de Outros Animais Não Especificados Anteriormente
73	161001	Serviço de Pulverização e Controle de Pragas Agrícolas
74	161002	Serviço de Poda de Árvores para Lavouras
75	161003	Serviço de Preparação de Terreno, Cultivo e Colheita
76	161099	Atividades de Apoio À Agricultura Não Especificadas Anteriormente
77	162801	Serviço de Inseminação Artificial em Animais
78	162802	Serviço de Tosquiamento de Ovinos
79	162803	Serviço de Manejo de Animais
80	162899	Atividades de Apoio À Pecuária Não Especificadas Anteriormente
1343	9603302	Serviços de Cremação
81	163600	Atividades de Pós-Colheita
82	170900	Caça e Serviços Relacionados
83	210101	Cultivo de Eucalipto
84	210102	Cultivo de Acácia-Negra
85	210103	Cultivo de Pinus
86	210104	Cultivo de Teca
87	210105	Cultivo de Espécies Madeireiras, Exceto Eucalipto, Acácia-Negra, Pinus e Teca
88	210106	Cultivo de Mudas em Viveiros Florestais
89	210107	Extração de Madeira em Florestas Plantadas
90	210108	Produção de Carvão Vegetal - Florestas Plantadas
91	210109	Produção de Casca de Acácia-Negra - Florestas Plantadas
92	210199	Produção de Produtos Não-Madeireiros Não Especificados Anteriormente em Florestas Plantadas
93	220901	Extração de Madeira em Florestas Nativas
94	220902	Produção de Carvão Vegetal - Florestas Nativas
95	220903	Coleta de Castanha-do-Pará em Florestas Nativas
96	220904	Coleta de Látex em Florestas Nativas
97	220905	Coleta de Palmito em Florestas Nativas
98	220906	Conservação de Florestas Nativas
99	220999	Coleta de Produtos Não-Madeireiros Não Especificados Anteriormente em Florestas Nativas
100	230600	Atividades de Apoio À Produção Florestal
101	311601	Pesca de Peixes em Água Salgada
102	311602	Pesca de Crustáceos e Moluscos em Água Salgada
103	311603	Coleta de Outros Produtos Marinhos
104	311604	Atividades de Apoio À Pesca em Água Salgada
105	312401	Pesca de Peixes em Água Doce
106	312402	Pesca de Crustáceos e Moluscos em Água Doce
107	312403	Coleta de Outros Produtos Aquáticos de Água Doce
108	312404	Atividades de Apoio À Pesca em Água Doce
109	321301	Criação de Peixes em Água Salgada e Salobra
110	321302	Criação de Camarões em Água Salgada e Salobra
111	321303	Criação de Ostras e Mexilhões em Água Salgada e Salobra
112	321304	Criação de Peixes Ornamentais em Água Salgada e Salobra
113	321305	Atividades de Apoio À Aqüicultura em Água Salgada e Salobra
114	321399	Cultivos e Semicultivos da Aqüicultura em Água Salgada e Salobra Não Especificados Anteriormente
115	322101	Criação de Peixes em Água Doce
116	322102	Criação de Camarões em Água Doce
117	322103	Criação de Ostras e Mexilhões em Água Doce
118	322104	Criação de Peixes Ornamentais em Água Doce
119	322105	Ranicultura
120	322106	Criação de Jacaré
121	322107	Atividades de Apoio À Aqüicultura em Água Doce
122	322199	Cultivos e Semicultivos da Aqüicultura em Água Doce Não Especificados Anteriormente
123	500301	Extração de Carvão Mineral
124	500302	Beneficiamento de Carvão Mineral
125	600001	Extração de Petróleo e Gás Natural
126	600002	Extração e Beneficiamento de Xisto
127	600003	Extração e Beneficiamento de Areias Betuminosas
128	710301	Extração de Minério de Ferro
129	710302	Pelotização, Sinterização e Outros Beneficiamentos de Minério de Ferro
130	721901	Extração de Minério de Alumínio
131	721902	Beneficiamento de Minério de Alumínio
132	722701	Extração de Minério de Estanho
133	722702	Beneficiamento de Minério de Estanho
134	723501	Extração de Minério de Manganês
135	723502	Beneficiamento de Minério de Manganês
136	724301	Extração de Minério de Metais Preciosos
137	724302	Beneficiamento de Minério de Metais Preciosos
138	725100	Extração de Minerais Radioativos
139	729401	Extração de Minérios de Nióbio e Titânio
140	729402	Extração de Minério de Tungstênio
141	729403	Extração de Minério de Níquel
142	729404	Extração de Minérios de Cobre, Chumbo, Zinco e Outros Minerais Metálicos Não-Ferrosos Não Especificados Anteriormente
143	729405	Beneficiamento de Minérios de Cobre, Chumbo, Zinco e Outros Minerais Metálicos Não-Ferrosos Não Especificados Anteriormente
144	810001	Extração de Ardósia e Beneficiamento Associado
145	810002	Extração de Granito e Beneficiamento Associado
146	810003	Extração de Mármore e Beneficiamento Associado
147	810004	Extração de Calcário e Dolomita e Beneficiamento Associado
148	810005	Extração de Gesso e Caulim
149	810006	Extração de Areia, Cascalho Ou Pedregulho e Beneficiamento Associado
150	810007	Extração de Argila e Beneficiamento Associado
151	810008	Extração de Saibro e Beneficiamento Associado
152	810009	Extração de Basalto e Beneficiamento Associado
153	810010	Beneficiamento de Gesso e Caulim Associado À Extração
154	810099	Extração e Britamento de Pedras e Outros Materiais para Construção e Beneficiamento Associado
155	891600	Extração de Minerais para Fabricação de Adubos, Fertilizantes e Outros Produtos Químicos
156	892401	Extração de Sal Marinho
157	892402	Extração de Sal-Gema
158	892403	Refino e Outros Tratamentos do Sal
159	893200	Extração de Gemas (Pedras Preciosas e Semipreciosas)
160	899101	Extração de Grafita
161	899102	Extração de Quartzo
162	899103	Extração de Amianto
163	899199	Extração de Outros Minerais Não-Metálicos Não Especificados Anteriormente
164	910600	Atividades de Apoio À Extração de Petróleo e Gás Natural
165	990401	Atividades de Apoio À Extração de Minério de Ferro
166	990402	Atividades de Apoio À Extração de Minerais Metálicos Não-Ferrosos
167	990403	Atividades de Apoio À Extração de Minerais Não-Metálicos
168	1011201	Frigorífico - Abate de Bovinos
169	1011202	Frigorífico - Abate de Eqüinos
170	1011203	Frigorífico - Abate de Ovinos e Caprinos
171	1011204	Frigorífico - Abate de Bufalinos
172	1011205	Matadouro - Abate de Reses Sob Contrato - Exceto Abate de Suínos
173	1012101	Abate de Aves
174	1012102	Abate de Pequenos Animais
175	1012103	Frigorífico - Abate de Suínos
176	1012104	Matadouro - Abate de Suínos Sob Contrato
177	1013901	Fabricação de Produtos de Carne
178	1013902	Preparação de Subprodutos do Abate
179	1020101	Preservação de Peixes, Crustáceos e Moluscos
180	1020102	Fabricação de Conservas de Peixes, Crustáceos e Moluscos
181	1031700	Fabricação de Conservas de Frutas
182	1032501	Fabricação de Conservas de Palmito
183	1032599	Fabricação de Conservas de Legumes e Outros Vegetais, Exceto Palmito
184	1033301	Fabricação de Sucos Concentrados de Frutas, Hortaliças e Legumes
185	2093200	Fabricação de Aditivos de Uso Industrial
186	1033302	Fabricação de Sucos de Frutas, Hortaliças e Legumes, Exceto Concentrados
187	1041400	Fabricação de Óleos Vegetais em Bruto, Exceto Óleo de Milho
188	1042200	Fabricação de Óleos Vegetais Refinados, Exceto Óleo de Milho
189	1043100	Fabricação de Margarina e Outras Gorduras Vegetais e de Óleos Não-Comestíveis de Animais
190	1051100	Preparação do Leite
191	1052000	Fabricação de Laticínios
192	1053800	Fabricação de Sorvetes e Outros Gelados Comestíveis
193	1061901	Beneficiamento de Arroz
194	1061902	Fabricação de Produtos do Arroz
195	1062700	Moagem de Trigo e Fabricação de Derivados
196	1063500	Fabricação de Farinha de Mandioca e Derivados
197	1064300	Fabricação de Farinha de Milho e Derivados, Exceto Óleos de Milho
198	1065101	Fabricação de Amidos e Féculas de Vegetais
199	1065102	Fabricação de Óleo de Milho em Bruto
200	1065103	Fabricação de Óleo de Milho Refinado
201	1066000	Fabricação de Alimentos para Animais
202	1069400	Moagem e Fabricação de Produtos de Origem Vegetal Não Especificados Anteriormente
203	1071600	Fabricação de Açúcar em Bruto
204	1072401	Fabricação de Açúcar de Cana Refinado
205	1072402	Fabricação de Açúcar de Cereais (Dextrose) e de Beterraba
206	1081301	Beneficiamento de Café
207	1081302	Torrefação e Moagem de Café
208	1082100	Fabricação de Produtos À Base de Café
209	1091100	Fabricação de Produtos de Panificação
210	1091101	Fabricação de Produtos de Panificação Industrial
211	1091102	Fabricação de Produtos de Padaria e Confeitaria com Predominância de Produção Própria
212	1092900	Fabricação de Biscoitos e Bolachas
213	1093701	Fabricação de Produtos Derivados do Cacau e de Chocolates
214	1093702	Fabricação de Frutas Cristalizadas, Balas e Semelhantes
215	1094500	Fabricação de Massas Alimentícias
216	1095300	Fabricação de Especiarias, Molhos, Temperos e Condimentos
217	1096100	Fabricação de Alimentos e Pratos Prontos
218	1099601	Fabricação de Vinagres
219	1099602	Fabricação de Pós Alimentícios
220	1099603	Fabricação de Fermentos e Leveduras
221	1099604	Fabricação de Gelo Comum
222	1099605	Fabricação de Produtos para Infusão (Chá, Mate, Etc.)
223	1099606	Fabricação de Adoçantes Naturais e Artificiais
224	1099607	Fabricação de Alimentos Dietéticos e Complementos Alimentares
225	1099699	Fabricação de Outros Produtos Alimentícios Não Especificados Anteriormente
226	1111901	Fabricação de Aguardente de Cana-de-Açúcar
227	1111902	Fabricação de Outras Aguardentes e Bebidas Destiladas
228	1112700	Fabricação de Vinho
229	1113501	Fabricação de Malte, Inclusive Malte Uísque
230	1113502	Fabricação de Cervejas e Chopes
231	1121600	Fabricação de Águas Envasadas
232	1122401	Fabricação de Refrigerantes
233	1122402	Fabricação de Chá Mate e Outros Chás Prontos para Consumo
234	1122403	Fabricação de Refrescos, Xaropes e Pós para Refrescos, Exceto Refrescos de Frutas
235	1122404	Fabricação de Bebidas Isotônicas
236	1122499	Fabricação de Outras Bebidas Não-Alcoólicas Não Especificadas Anteriormente
237	1210700	Processamento Industrial do Fumo
238	1220401	Fabricação de Cigarros
239	1220402	Fabricação de Cigarrilhas e Charutos
240	1220403	Fabricação de Filtros para Cigarros
241	1220499	Fabricação de Outros Produtos do Fumo, Exceto Cigarros, Cigarrilhas e Charutos
242	1311100	Preparação e Fiação de Fibras de Algodão
243	1312000	Preparação e Fiação de Fibras Têxteis Naturais, Exceto Algodão
244	1313800	Fiação de Fibras Artificiais e Sintéticas
245	1314600	Fabricação de Linhas para Costurar e Bordar
246	1321900	Tecelagem de Fios de Algodão
247	1322700	Tecelagem de Fios de Fibras Têxteis Naturais, Exceto Algodão
248	1323500	Tecelagem de Fios de Fibras Artificiais e Sintéticas
249	1330800	Fabricação de Tecidos de Malha
250	1340501	Estamparia e Texturização em Fios, Tecidos, Artefatos Têxteis e Peças do Vestuário
251	1340502	Alvejamento, Tingimento e Torção em Fios, Tecidos, Artefatos Têxteis e Peças do Vestuário
252	1340599	Outros Serviços de Acabamento em Fios, Tecidos, Artefatos Têxteis e Peças do Vestuário
253	1351100	Fabricação de Artefatos Têxteis para Uso Doméstico
254	1352900	Fabricação de Artefatos de Tapeçaria
255	1353700	Fabricação de Artefatos de Cordoaria
256	1354500	Fabricação de Tecidos Especiais, Inclusive Artefatos
257	1359600	Fabricação de Outros Produtos Têxteis Não Especificados Anteriormente
258	1411801	Confecção de Roupas Íntimas
259	1411802	Facção de Roupas Íntimas
260	1412601	Confecção de Peças de Vestuário, Exceto Roupas Íntimas e As Confeccionadas Sob Medida
261	1412602	Confecção, Sob Medida, de Peças do Vestuário, Exceto Roupas Íntimas
262	1412603	Facção de Peças do Vestuário, Exceto Roupas Íntimas
263	1413401	Confecção de Roupas Profissionais, Exceto Sob Medida
264	1413402	Confecção, Sob Medida, de Roupas Profissionais
265	1413403	Facção de Roupas Profissionais
266	1414200	Fabricação de Acessórios do Vestuário, Exceto para Segurança e Proteção
267	1421500	Fabricação de Meias
268	2094100	Fabricação de Catalisadores
269	1422300	Fabricação de Artigos do Vestuário, Produzidos em Malharias e Tricotagens, Exceto Meias
270	1510600	Curtimento e Outras Preparações de Couro
271	1521100	Fabricação de Artigos para Viagem, Bolsas e Semelhantes de Qualquer Material
272	1529700	Fabricação de Artefatos de Couro Não Especificados Anteriormente
273	1531901	Fabricação de Calçados de Couro
274	1531902	Acabamento de Calçados de Couro Sob Contrato
275	1532700	Fabricação de Tênis de Qualquer Material
276	1533500	Fabricação de Calçados de Material Sintético
277	1539400	Fabricação de Calçados de Materiais Não Especificados Anteriormente
278	1540800	Fabricação de Partes para Calçados, de Qualquer Material
279	1610201	Serrarias com Desdobramento de Madeira
280	1610202	Serrarias Sem Desdobramento de Madeira
281	1610203	Serrarias com Desdobramento de Madeira em Bruto
282	1610204	Serrarias Sem Desdobramento de Madeira em Bruto  -Resserragem
283	1610205	Serviço de Tratamento de Madeira Realizado Sob Contrato
284	1621800	Fabricação de Madeira Laminada e de Chapas de Madeira Compensada, Prensada e Aglomerada
285	1622601	Fabricação de Casas de Madeira Pré-Fabricadas
286	1622602	Fabricação de Esquadrias de Madeira e de Peças de Madeira para Instalações Industriais e Comerciais
287	1622699	Fabricação de Outros Artigos de Carpintaria para Construção
288	1623400	Fabricação de Artefatos de Tanoaria e de Embalagens de Madeira
289	1629301	Fabricação de Artefatos Diversos de Madeira, Exceto Móveis
290	1629302	Fabricação de Artefatos Diversos de Cortiça, Bambu, Palha, Vime e Outros Materiais Trançados, Exceto Móveis
291	1710900	Fabricação de Celulose e Outras Pastas para A Fabricação de Papel
292	1721400	Fabricação de Papel
293	1722200	Fabricação de Cartolina e Papel-Cartão
294	1731100	Fabricação de Embalagens de Papel
295	1732000	Fabricação de Embalagens de Cartolina e Papel-Cartão
296	1733800	Fabricação de Chapas e de Embalagens de Papelão Ondulado
297	1741901	Fabricação de Formulários Contínuos
298	1741902	Fabricação de Produtos de Papel, Cartolina, Papel Cartão e Papelão Ondulado para Uso Comercial e de Escritório, Exceto Formulário Contínuo
299	1742701	Fabricação de Fraldas Descartáveis
300	1742702	Fabricação de Absorventes Higiênicos
301	1742799	Fabricação de Produtos de Papel para Uso Doméstico e Higiênico-Sanitário Não Especificados Anteriormente
302	1749400	Fabricação de Produtos de Pastas Celulósicas, Papel, Cartolina, Papel-Cartão e Papelão Ondulado Não Especificados Anteriormente
303	1811301	Impressão de Jornais
304	1811302	Impressão de Livros, Revistas e Outras Publicações Periódicas
305	1812100	Impressão de Material de Segurança
306	1813001	Impressão de Material para Uso Publicitário
307	1813099	Impressão de Material para Outros Usos
308	1821100	Serviços de Pré-Impressão
309	1822900	Serviços de Acabamentos Gráficos
310	1822901	Serviços de Encadernação e Plastificação
311	1822999	Serviços de Acabamentos Gráficos, Exceto Encadernação e Plastificação
312	1830001	Reprodução de Som em Qualquer Suporte
313	1830002	Reprodução de Vídeo em Qualquer Suporte
314	1830003	Reprodução de Software em Qualquer Suporte
315	1910100	Coquerias
316	1921700	Fabricação de Produtos do Refino de Petróleo
317	1922501	Formulação de Combustíveis
318	1922502	Rerrefino de Óleos Lubrificantes
319	1922599	Fabricação de Outros Produtos Derivados do Petróleo, Exceto Produtos do Refino
320	1931400	Fabricação de Álcool
321	1932200	Fabricação de Biocombustíveis, Exceto Álcool
322	2011800	Fabricação de Cloro e Álcalis
323	2012600	Fabricação de Intermediários para Fertilizantes
324	2013400	Fabricação de Adubos e Fertilizantes
325	2013401	Fabricação de Adubos e Fertilizantes Organo-Minerais
326	2013402	Fabricação de Adubos e Fertilizantes, Exceto Organo-Minerais
327	2014200	Fabricação de Gases Industriais
328	2019301	Elaboração de Combustíveis Nucleares
329	2019399	Fabricação de Outros Produtos Químicos Inorgânicos Não Especificados Anteriormente
330	2021500	Fabricação de Produtos Petroquímicos Básicos
903	4912403	Transporte Metroviário
331	2022300	Fabricação de Intermediários para Plastificantes, Resinas e Fibras
332	2029100	Fabricação de Produtos Químicos Orgânicos Não Especificados Anteriormente
333	2031200	Fabricação de Resinas Termoplásticas
334	2032100	Fabricação de Resinas Termofixas
335	2033900	Fabricação de Elastômeros
336	2040100	Fabricação de Fibras Artificiais e Sintéticas
337	2051700	Fabricação de Defensivos Agrícolas
338	2052500	Fabricação de Desinfestantes Domissanitários
339	2061400	Fabricação de Sabões e Detergentes Sintéticos
340	2062200	Fabricação de Produtos de Limpeza e Polimento
341	2063100	Fabricação de Cosméticos, Produtos de Perfumaria e de Higiene Pessoal
342	2071100	Fabricação de Tintas, Vernizes, Esmaltes e Lacas
343	2072000	Fabricação de Tintas de Impressão
344	2073800	Fabricação de Impermeabilizantes, Solventes e Produtos Afins
345	2091600	Fabricação de Adesivos e Selantes
346	2092401	Fabricação de Pólvoras, Explosivos e Detonantes
347	2092402	Fabricação de Artigos Pirotécnicos
348	2092403	Fabricação de Fósforos de Segurança
349	7911200	Agências de Viagens
350	2099101	Fabricação de Chapas, Filmes, Papéis e Outros Materiais e Produtos Químicos para Fotografia
351	2099199	Fabricação de Outros Produtos Químicos Não Especificados Anteriormente
352	2110600	Fabricação de Produtos Farmoquímicos
353	2121101	Fabricação de Medicamentos Alopáticos para Uso Humano
354	2121102	Fabricação de Medicamentos Homeopáticos para Uso Humano
355	2121103	Fabricação de Medicamentos Fitoterápicos para Uso Humano
356	2122000	Fabricação de Medicamentos para Uso Veterinário
357	2123800	Fabricação de Preparações Farmacêuticas
358	2211100	Fabricação de Pneumáticos e de Câmaras-de-Ar
359	2212900	Reforma de Pneumáticos Usados
360	2219600	Fabricação de Artefatos de Borracha Não Especificados Anteriormente
361	2221800	Fabricação de Laminados Planos e Tubulares de Material Plástico
362	2222600	Fabricação de Embalagens de Material Plástico
363	2223400	Fabricação de Tubos e Acessórios de Material Plástico para Uso Na Construção
364	2229301	Fabricação de Artefatos de Material Plástico para Uso Pessoal e Doméstico
365	2229302	Fabricação de Artefatos de Material Plástico para Usos Industriais
366	2229303	Fabricação de Artefatos de Material Plástico para Uso Na Construção, Exceto Tubos e Acessórios
367	2229399	Fabricação de Artefatos de Material Plástico para Outros Usos Não Especificados Anteriormente
368	2311700	Fabricação de Vidro Plano e de Segurança
369	2312500	Fabricação de Embalagens de Vidro
370	2319200	Fabricação de Artigos de Vidro
371	2320600	Fabricação de Cimento
372	2330301	Fabricação de Estruturas Pré-Moldadas de Concreto Armado, em Série e Sob Encomenda
373	2330302	Fabricação de Artefatos de Cimento para Uso Na Construção
374	2330303	Fabricação de Artefatos de Fibrocimento para Uso Na Construção
375	2330304	Fabricação de Casas Pré-Moldadas de Concreto
376	2330305	Preparação de Massa de Concreto e Argamassa para Construção
377	2330399	Fabricação de Outros Artefatos e Produtos de Concreto, Cimento, Fibrocimento, Gesso e Materiais Semelhantes
378	2341900	Fabricação de Produtos Cerâmicos Refratários
379	2342701	Fabricação de Azulejos e Pisos
380	2342702	Fabricação de Artefatos de Cerâmica e Barro Cozido para Uso Na Construção, Exceto Azulejos e Pisos
381	2349401	Fabricação de Material Sanitário de Cerâmica
382	2349499	Fabricação de Produtos Cerâmicos Não-Refratários Não Especificados Anteriormente
383	2391501	Britamento de Pedras, Exceto Associado À Extração
384	2391502	Aparelhamento de Pedras para Construção, Exceto Associado À Extração
385	2391503	Aparelhamento de Placas e Execução de Trabalhos em Mármore, Granito, Ardósia e Outras Pedras
386	2392300	Fabricação de Cal e Gesso
387	2399101	Decoração, Lapidação, Gravação, Vitrificação e Outros Trabalhos em Cerâmica, Louça, Vidro e Cristal
388	2399102	Fabricação de Abrasivos
389	2399199	Fabricação de Outros Produtos de Minerais Não-Metálicos Não Especificados Anteriormente
390	2411300	Produção de Ferro-Gusa
391	2412100	Produção de Ferroligas
392	2421100	Produção de Semi-Acabados de Aço
393	2422901	Produção de Laminados Planos de Aço Ao Carbono, Revestidos Ou Não
394	2422902	Produção de Laminados Planos de Aços Especiais
395	2423701	Produção de Tubos de Aço Sem Costura
396	2423702	Produção de Laminados Longos de Aço, Exceto Tubos
397	2424501	Produção de Arames de Aço
398	2424502	Produção de Relaminados, Trefilados e Perfilados de Aço, Exceto Arames
399	2431800	Produção de Tubos de Aço com Costura
400	2439300	Produção de Outros Tubos de Ferro e Aço
401	2441501	Produção de Alumínio e Suas Ligas em Formas Primárias
402	2441502	Produção de Laminados de Alumínio
403	2442300	Metalurgia dos Metais Preciosos
404	2443100	Metalurgia do Cobre
405	2449101	Produção de Zinco em Formas Primárias
406	2449102	Produção de Laminados de Zinco
407	2449103	Fabricação de Ânodos para Galvanoplastia
408	2449199	Metalurgia de Outros Metais Não-Ferrosos e Suas Ligas Não Especificados Anteriormente
409	2451200	Fundição de Ferro e Aço
410	2452100	Fundição de Metais Não-Ferrosos e Suas Ligas
411	2511000	Fabricação de Estruturas Metálicas
412	2512800	Fabricação de Esquadrias de Metal
413	2513600	Fabricação de Obras de Caldeiraria Pesada
414	2521700	Fabricação de Tanques, Reservatórios Metálicos e Caldeiras para Aquecimento Central
415	2522500	Fabricação de Caldeiras Geradoras de Vapor, Exceto para Aquecimento Central e para Veículos
416	2531401	Produção de Forjados de Aço
417	2531402	Produção de Forjados de Metais Não-Ferrosos e Suas Ligas
418	2532201	Produção de Artefatos Estampados de Metal
419	2532202	Metalurgia do Pó
420	2539000	Serviços de Usinagem, Solda, Tratamento e Revestimento em Metais
421	2539001	Serviços de Usinagem, Tornearia e Solda
422	2539002	Serviços de Tratamento e Revestimento em Metais
423	2541100	Fabricação de Artigos de Cutelaria
424	2542000	Fabricação de Artigos de Serralheria, Exceto Esquadrias
425	2543800	Fabricação de Ferramentas
426	2550101	Fabricação de Equipamento Bélico Pesado, Exceto Veículos Militares de Combate
427	2550102	Fabricação de Armas de Fogo, Outras Armas e Munições
428	2591800	Fabricação de Embalagens Metálicas
429	2592601	Fabricação de Produtos de Trefilados de Metal Padronizados
430	2592602	Fabricação de Produtos de Trefilados de Metal, Exceto Padronizados
431	2593400	Fabricação de Artigos de Metal para Uso Doméstico e Pessoal
432	2599301	Serviços de Confecção de Armações Metálicas para A Construção
433	2599302	Serviço de Corte e Dobra de Metais
434	2599399	Fabricação de Outros Produtos de Metal Não Especificados Anteriormente
435	2610800	Fabricação de Componentes Eletrônicos
436	2621300	Fabricação de Equipamentos de Informática
437	2622100	Fabricação de Periféricos para Equipamentos de Informática
438	2631100	Fabricação de Equipamentos Transmissores de Comunicação, Peças e Acessórios
439	2632900	Fabricação de Aparelhos Telefônicos e de Outros Equipamentos de Comunicação, Peças e Acessórios
440	2640000	Fabricação de Aparelhos de Recepção, Reprodução, Gravação e Amplificação de Áudio e Vídeo
441	2651500	Fabricação de Aparelhos e Equipamentos de Medida, Teste e Controle
442	2652300	Fabricação de Cronômetros e Relógios
443	2660400	Fabricação de Aparelhos Eletromédicos e Eletroterapêuticos e Equipamentos de Irradiação
444	2670101	Fabricação de Equipamentos e Instrumentos Ópticos, Peças e Acessórios
445	2670102	Fabricação de Aparelhos Fotográficos e Cinematográficos, Peças e Acessórios
446	2680900	Fabricação de Mídias Virgens, Magnéticas e Ópticas
447	2710401	Fabricação de Geradores de Corrente Contínua e Alternada, Peças e Acessórios
448	2710402	Fabricação de Transformadores, Indutores, Conversores, Sincronizadores e Semelhantes, Peças e Acessórios
449	2710403	Fabricação de Motores Elétricos, Peças e Acessórios
450	2721000	Fabricação de Pilhas, Baterias e Acumuladores Elétricos, Exceto para Veículos Automotores
451	2722801	Fabricação de Baterias e Acumuladores para Veículos Automotores
452	2722802	Recondicionamento de Baterias e Acumuladores para Veículos Automotores
453	2731700	Fabricação de Aparelhos e Equipamentos para Distribuição e Controle de Energia Elétrica
454	2732500	Fabricação de Material Elétrico para Instalações em Circuito de Consumo
455	2733300	Fabricação de Fios, Cabos e Condutores Elétricos Isolados
456	2740601	Fabricação de Lâmpadas
457	2740602	Fabricação de Luminárias e Outros Equipamentos de Iluminação
458	2751100	Fabricação de Fogões, Refrigeradores e Máquinas de Lavar e Secar para Uso Doméstico, Peças e Acessórios
459	2759701	Fabricação de Aparelhos Elétricos de Uso Pessoal, Peças e Acessórios
460	2759799	Fabricação de Outros Aparelhos Eletrodomésticos Não Especificados Anteriormente, Peças e Acessórios
461	2790201	Fabricação de Eletrodos, Contatos e Outros Artigos de Carvão e Grafita para Uso Elétrico, Eletroímãs e Isoladores
462	2790202	Fabricação de Equipamentos para Sinalização e Alarme
463	2790299	Fabricação de Outros Equipamentos e Aparelhos Elétricos Não Especificados Anteriormente
464	2811900	Fabricação de Motores e Turbinas, Peças e Acessórios, Exceto para Aviões e Veículos Rodoviários
465	2812700	Fabricação de Equipamentos Hidráulicos e Pneumáticos, Peças e Acessórios, Exceto Válvulas
466	2813500	Fabricação de Válvulas, Registros e Dispositivos Semelhantes, Peças e Acessórios
467	2814301	Fabricação de Compressores para Uso Industrial, Peças e Acessórios
468	2814302	Fabricação de Compressores para Uso Não Industrial, Peças e Acessórios
469	2815101	Fabricação de Rolamentos para Fins Industriais
470	2815102	Fabricação de Equipamentos de Transmissão para Fins Industriais, Exceto Rolamentos
471	2821601	Fabricação de Fornos Industriais, Aparelhos e Equipamentos Não-Elétricos para Instalações Térmicas, Peças e Acessórios
472	2821602	Fabricação de Estufas e Fornos Elétricos para Fins Industriais, Peças e Acessórios
473	2822401	Fabricação de Máquinas, Equipamentos e Aparelhos para Transporte e Elevação de Pessoas, Peças e Acessórios
474	2822402	Fabricação de Máquinas, Equipamentos e Aparelhos para Transporte e Elevação de Cargas, Peças e Acessórios
475	2823200	Fabricação de Máquinas e Aparelhos de Refrigeração e Ventilação para Uso Industrial e Comercial, Peças e Acessórios
476	2824101	Fabricação de Aparelhos e Equipamentos de Ar Condicionado para Uso Industrial
477	2824102	Fabricação de Aparelhos e Equipamentos de Ar Condicionado para Uso Não-Industrial
478	2825900	Fabricação de Máquinas e Equipamentos para Saneamento Básico e Ambiental, Peças e Acessórios
479	2829101	Fabricação de Máquinas de Escrever, Calcular e Outros Equipamentos Não-Eletrônicos para Escritório, Peças e Acessórios
480	2829199	Fabricação de Outras Máquinas e Equipamentos de Uso Geral Não Especificados Anteriormente, Peças e Acessórios
481	2831300	Fabricação de Tratores Agrícolas, Peças e Acessórios
482	2832100	Fabricação de Equipamentos para Irrigação Agrícola, Peças e Acessórios
483	2833000	Fabricação de Máquinas e Equipamentos para A Agricultura e Pecuária, Peças e Acessórios, Exceto para Irrigação
484	2840200	Fabricação de Máquinas-Ferramenta, Peças e Acessórios
485	2851800	Fabricação de Máquinas e Equipamentos para A Prospecção e Extração de Petróleo, Peças e Acessórios
486	2852600	Fabricação de Outras Máquinas e Equipamentos para Uso Na Extração Mineral, Peças e Acessórios, Exceto Na Extração de Petróleo
487	2853400	Fabricação de Tratores, Peças e Acessórios, Exceto Agrícolas
488	2854200	Fabricação de Máquinas e Equipamentos para Terraplenagem, Pavimentação e Construção, Peças e Acessórios, Exceto Tratores
489	2861500	Fabricação de Máquinas para A Indústria Metalúrgica, Peças e Acessórios, Exceto Máquinas-Ferramenta
490	2862300	Fabricação de Máquinas e Equipamentos para As Indústrias de Alimentos, Bebidas e Fumo, Peças e Acessórios
491	2863100	Fabricação de Máquinas e Equipamentos para A Indústria Têxtil, Peças e Acessórios
492	2864000	Fabricação de Máquinas e Equipamentos para As Indústrias do Vestuário, do Couro e de Calçados, Peças e Acessórios
493	2865800	Fabricação de Máquinas e Equipamentos para As Indústrias de Celulose, Papel e Papelão e Artefatos, Peças e Acessórios
494	2866600	Fabricação de Máquinas e Equipamentos para A Indústria do Plástico, Peças e Acessórios
495	2869100	Fabricação de Máquinas e Equipamentos para Uso Industrial Específico Não Especificados Anteriormente, Peças e Acessórios
496	2910701	Fabricação de Automóveis, Camionetas e Utilitários
497	2910702	Fabricação de Chassis com Motor para Automóveis, Camionetas e Utilitários
498	2910703	Fabricação de Motores para Automóveis, Camionetas e Utilitários
499	2920401	Fabricação de Caminhões e Ônibus
500	2920402	Fabricação de Motores para Caminhões e Ônibus
501	2930101	Fabricação de Cabines, Carrocerias e Reboques para Caminhões
502	2930102	Fabricação de Carrocerias para Ônibus
503	2930103	Fabricação de Cabines, Carrocerias e Reboques para Outros Veículos Automotores, Exceto Caminhões e Ônibus
504	2941700	Fabricação de Peças e Acessórios para O Sistema Motor de Veículos Automotores
505	2942500	Fabricação de Peças e Acessórios para Os Sistemas de Marcha e Transmissão de Veículos Automotores
506	2943300	Fabricação de Peças e Acessórios para O Sistema de Freios de Veículos Automotores
507	2944100	Fabricação de Peças e Acessórios para O Sistema de Direção e Suspensão de Veículos Automotores
508	2945000	Fabricação de Material Elétrico e Eletrônico para Veículos Automotores, Exceto Baterias
509	2949201	Fabricação de Bancos e Estofados para Veículos Automotores
510	2949299	Fabricação de Outras Peças e Acessórios para Veículos Automotores Não Especificadas Anteriormente
511	2950600	Recondicionamento e Recuperação de Motores para Veículos Automotores
512	3011301	Construção de Embarcações de Grande Porte
513	3011302	Construção de Embarcações para Uso Comercial e para Usos Especiais, Exceto de Grande Porte
514	3012100	Construção de Embarcações para Esporte e Lazer
515	3031800	Fabricação de Locomotivas, Vagões e Outros Materiais Rodantes
516	3032600	Fabricação de Peças e Acessórios para Veículos Ferroviários
517	3041500	Fabricação de Aeronaves
518	3042300	Fabricação de Turbinas, Motores e Outros Componentes e Peças para Aeronaves
519	3050400	Fabricação de Veículos Militares de Combate
520	3091100	Fabricação de Motocicletas, Peças e Acessórios
521	3091101	Fabricação de Motocicletas
522	3091102	Fabricação de Peças e Acessórios para Motocicletas
523	3092000	Fabricação de Bicicletas e Triciclos Não-Motorizados, Peças e Acessórios
524	3099700	Fabricação de Equipamentos de Transporte Não Especificados Anteriormente
525	3101200	Fabricação de Móveis com Predominância de Madeira
526	3102100	Fabricação de Móveis com Predominância de Metal
527	3103900	Fabricação de Móveis de Outros Materiais, Exceto Madeira e Metal
528	3104700	Fabricação de Colchões
529	3211601	Lapidação de Gemas
530	3211602	Fabricação de Artefatos de Joalheria e Ourivesaria
531	3211603	Cunhagem de Moedas e Medalhas
532	3212400	Fabricação de Bijuterias e Artefatos Semelhantes
533	3220500	Fabricação de Instrumentos Musicais, Peças e Acessórios
534	3230200	Fabricação de Artefatos para Pesca e Esporte
535	3240001	Fabricação de Jogos Eletrônicos
536	3240002	Fabricação de Mesas de Bilhar, de Sinuca e Acessórios Não Associada À Locação
537	3240003	Fabricação de Mesas de Bilhar, de Sinuca e Acessórios Associada À Locação
538	3240099	Fabricação de Outros Brinquedos e Jogos Recreativos Não Especificados Anteriormente
539	3250701	Fabricação de Instrumentos Não-Eletrônicos e Utensílios para Uso Médico, Cirúrgico, Odontológico e de Laboratório
540	3250702	Fabricação de Mobiliário para Uso Médico, Cirúrgico, Odontológico e de Laboratório
541	3250703	Fabricação de Aparelhos e Utensílios para Correção de Defeitos Físicos e Aparelhos Ortopédicos em Geral Sob Encomenda
542	3250704	Fabricação de Aparelhos e Utensílios para Correção de Defeitos Físicos e Aparelhos Ortopédicos em Geral, Exceto Sob Encomenda
543	3250705	Fabricação de Materiais para Medicina e Odontologia
544	3250706	Serviços de Prótese Dentária
545	3250707	Fabricação de Artigos Ópticos
546	3250708	Fabricação de Artefatos de Tecido Não Tecido para Uso Odonto-Médico-Hospitalar
547	3250709	Serviço de Laboratório Óptico
548	3291400	Fabricação de Escovas, Pincéis e Vassouras
549	3292201	Fabricação de Roupas de Proteção e Segurança e Resistentes A Fogo
550	3292202	Fabricação de Equipamentos e Acessórios para Segurança Pessoal e Profissional
551	3299001	Fabricação de Guarda-Chuvas e Similares
552	3299002	Fabricação de Canetas, Lápis e Outros Artigos para Escritório
553	3299003	Fabricação de Letras, Letreiros e Placas de Qualquer Material, Exceto Luminosos
554	3299004	Fabricação de Painéis e Letreiros Luminosos
555	3299005	Fabricação de Aviamentos para Costura
556	3299006	Fabricação de Velas, Inclusive Decorativas
557	3299099	Fabricação de Produtos Diversos Não Especificados Anteriormente
558	3311200	Manutenção e Reparação de Tanques, Reservatórios Metálicos e Caldeiras, Exceto para Veículos
559	3312101	Manutenção e Reparação de Equipamentos Transmissores de Comunicação
560	3312102	Manutenção e Reparação de Aparelhos e Instrumentos de Medida, Teste e Controle
561	3312103	Manutenção e Reparação de Aparelhos Eletromédicos e Eletroterapêuticos e Equipamentos de Irradiação
562	3312104	Manutenção e Reparação de Equipamentos e Instrumentos Ópticos
563	3313901	Manutenção e Reparação de Geradores, Transformadores e Motores Elétricos
564	3313902	Manutenção e Reparação de Baterias e Acumuladores Elétricos, Exceto para Veículos
565	3313999	Manutenção e Reparação de Máquinas, Aparelhos e Materiais Elétricos Não Especificados Anteriormente
566	3314701	Manutenção e Reparação de Máquinas Motrizes Não-Elétricas
567	3314702	Manutenção e Reparação de Equipamentos Hidráulicos e Pneumáticos, Exceto Válvulas
568	3314703	Manutenção e Reparação de Válvulas Industriais
569	3314704	Manutenção e Reparação de Compressores
570	3314705	Manutenção e Reparação de Equipamentos de Transmissão para Fins Industriais
571	3314706	Manutenção e Reparação de Máquinas, Aparelhos e Equipamentos para Instalações Térmicas
572	3314707	Manutenção e Reparação de Máquinas e Aparelhos de Refrigeração e Ventilação para Uso Industrial e Comercial
573	3314708	Manutenção e Reparação de Máquinas, Equipamentos e Aparelhos para Transporte e Elevação de Cargas
574	3314709	Manutenção e Reparação de Máquinas de Escrever, Calcular e de Outros Equipamentos Não-Eletrônicos para Escritório
575	3314710	Manutenção e Reparação de Máquinas e Equipamentos para Uso Geral Não Especificados Anteriormente
576	3314711	Manutenção e Reparação de Máquinas e Equipamentos para Agricultura e Pecuária
577	3314712	Manutenção e Reparação de Tratores Agrícolas
578	3314713	Manutenção e Reparação de Máquinas-Ferramenta
579	3314714	Manutenção e Reparação de Máquinas e Equipamentos para A Prospecção e Extração de Petróleo
580	3314715	Manutenção e Reparação de Máquinas e Equipamentos para Uso Na Extração Mineral, Exceto Na Extração de Petróleo
581	3314716	Manutenção e Reparação de Tratores, Exceto Agrícolas
582	3314717	Manutenção e Reparação de Máquinas e Equipamentos de Terraplenagem, Pavimentação e Construção, Exceto Tratores
583	3314718	Manutenção e Reparação de Máquinas para A Indústria Metalúrgica, Exceto Máquinas-Ferramenta
584	3314719	Manutenção e Reparação de Máquinas e Equipamentos para As Indústrias de Alimentos, Bebidas e Fumo
585	3314720	Manutenção e Reparação de Máquinas e Equipamentos para A Indústria Têxtil, do Vestuário, do Couro e Calçados
586	3314721	Manutenção e Reparação de Máquinas e Aparelhos para A Indústria de Celulose, Papel e Papelão e Artefatos
587	3314722	Manutenção e Reparação de Máquinas e Aparelhos para A Indústria do Plástico
588	3314799	Manutenção e Reparação de Outras Máquinas e Equipamentos para Usos Industriais Não Especificados Anteriormente
589	3315500	Manutenção e Reparação de Veículos Ferroviários
590	3316301	Manutenção e Reparação de Aeronaves, Exceto A Manutenção Na Pista
591	3316302	Manutenção de Aeronaves Na Pista
592	3317101	Manutenção e Reparação de Embarcações e Estruturas Flutuantes
593	3317102	Manutenção e Reparação de Embarcações para Esporte e Lazer
594	3319800	Manutenção e Reparação de Equipamentos e Produtos Não Especificados Anteriormente
595	3321000	Instalação de Máquinas e Equipamentos Industriais
596	3329501	Serviços de Montagem de Móveis de Qualquer Material
597	3329599	Instalação de Outros Equipamentos Não Especificados Anteriormente
598	3511500	Geração de Energia Elétrica
599	3511501	Geração de Energia Elétrica
600	3511502	Atividades de Coordenação e Controle da Operação da Geração e Transmissão de Energia Elétrica
601	3512300	Transmissão de Energia Elétrica
602	3513100	Comércio Atacadista de Energia Elétrica
603	3514000	Distribuição de Energia Elétrica
604	3520401	Produção de Gás; Processamento de Gás Natural
605	3520402	Distribuição de Combustíveis Gasosos por Redes Urbanas
606	3530100	Produção e Distribuição de Vapor, Água Quente e Ar Condicionado
607	3600601	Captação, Tratamento e Distribuição de Água
608	3600602	Distribuição de Água por Caminhões
609	3701100	Gestão de Redes de Esgoto
610	3702900	Atividades Relacionadas A Esgoto, Exceto A Gestão de Redes
611	3811400	Coleta de Resíduos Não-Perigosos
612	3812200	Coleta de Resíduos Perigosos
613	3821100	Tratamento e Disposição de Resíduos Não-Perigosos
614	3822000	Tratamento e Disposição de Resíduos Perigosos
615	3831901	Recuperação de Sucatas de Alumínio
616	3831999	Recuperação de Materiais Metálicos, Exceto Alumínio
617	3832700	Recuperação de Materiais Plásticos
618	3839401	Usinas de Compostagem
619	3839499	Recuperação de Materiais Não Especificados Anteriormente
620	3900500	Descontaminação e Outros Serviços de Gestão de Resíduos
621	4110700	Incorporação de Empreendimentos Imobiliários
622	4120400	Construção de Edifícios
623	4211101	Construção de Rodovias e Ferrovias
624	4211102	Pintura para Sinalização em Pistas Rodoviárias e Aeroportos
625	4212000	Construção de Obras de Arte Especiais
626	4213800	Obras de Urbanização - Ruas, Praças e Calçadas
627	4221901	Construção de Barragens e Represas para Geração de Energia Elétrica
628	4221902	Construção de Estações e Redes de Distribuição de Energia Elétrica
629	4221903	Manutenção de Redes de Distribuição de Energia Elétrica
630	4221904	Construção de Estações e Redes de Telecomunicações
631	4221905	Manutenção de Estações e Redes de Telecomunicações
632	4222701	Construção de Redes de Abastecimento de Água, Coleta de Esgoto e Construções Correlatas, Exceto Obras de Irrigação
633	4222702	Obras de Irrigação
634	4223500	Construção de Redes de Transportes por Dutos, Exceto para Água e Esgoto
635	4291000	Obras Portuárias, Marítimas e Fluviais
636	4292801	Montagem de Estruturas Metálicas
637	4292802	Obras de Montagem Industrial
638	4299501	Construção de Instalações Esportivas e Recreativas
639	4299599	Outras Obras de Engenharia Civil Não Especificadas Anteriormente
640	4311801	Demolição de Edifícios e Outras Estruturas
641	4311802	Preparação de Canteiro e Limpeza de Terreno
642	4312600	Perfurações e Sondagens
643	4313400	Obras de Terraplenagem
644	4319300	Serviços de Preparação do Terreno Não Especificados Anteriormente
645	4321500	Instalação e Manutenção Elétrica
646	4322301	Instalações Hidráulicas, Sanitárias e de Gás
647	4322302	Instalação e Manutenção de Sistemas Centrais de Ar Condicionado, de Ventilação e Refrigeração
648	4322303	Instalações de Sistema de Prevenção Contra Incêndio
649	4329101	Instalação de Painéis Publicitários
650	4329102	Instalação de Equipamentos para Orientação À Navegação Marítima Fluvial e Lacustre
651	4329103	Instalação, Manutenção e Reparação de Elevadores, Escadas e Esteiras Rolantes
652	4329104	Montagem e Instalação de Sistemas e Equipamentos de Iluminação e Sinalização em Vias Públicas, Portos e Aeroportos
653	4329105	Tratamentos Térmicos, Acústicos Ou de Vibração
654	4329199	Outras Obras de Instalações em Construções Não Especificadas Anteriormente
655	4330401	Impermeabilização em Obras de Engenharia Civil
656	4330402	Instalação de Portas, Janelas, Tetos, Divisórias e Armários Embutidos de Qualquer Material
657	4330403	Obras de Acabamento em Gesso e Estuque
658	4330404	Serviços de Pintura de Edifícios em Geral
659	4330405	Aplicação de Revestimentos e de Resinas em Interiores e Exteriores
660	4330499	Outras Obras de Acabamento da Construção
661	4391600	Obras de Fundações
662	4399101	Administração de Obras
663	4399102	Montagem e Desmontagem de Andaimes e Outras Estruturas Temporárias
664	4399103	Obras de Alvenaria
665	4399104	Serviços de Operação e Fornecimento de Equipamentos para Transporte e Elevação de Cargas e Pessoas para Uso em Obras
666	4399105	Perfuração e Construção de Poços de Água
667	4399199	Serviços Especializados para Construção Não Especificados Anteriormente
668	4511101	Comércio A Varejo de Automóveis, Camionetas e Utilitários Novos
669	4511102	Comércio A Varejo de Automóveis, Camionetas e Utilitários Usados
670	4511103	Comércio por Atacado de Automóveis, Camionetas e Utilitários Novos e Usados
671	4511104	Comércio por Atacado de Caminhões Novos e Usados
672	4511105	Comércio por Atacado de Reboques e Semi-Reboques Novos e Usados
673	4511106	Comércio por Atacado de Ônibus e Microônibus Novos e Usados
674	4512901	Representantes Comerciais e Agentes do Comércio de Veículos Automotores
675	4512902	Comércio Sob Consignação de Veículos Automotores
676	4520001	Serviços de Manutenção e Reparação Mecânica de Veículos Automotores
677	4520002	Serviços de Lanternagem Ou Funilaria e Pintura de Veículos Automotores
678	4520003	Serviços de Manutenção e Reparação Elétrica de Veículos Automotores
679	4520004	Serviços de Alinhamento e Balanceamento de Veículos Automotores
680	4520005	Serviços de Lavagem, Lubrificação e Polimento de Veículos Automotores
681	4520006	Serviços de Borracharia para Veículos Automotores
682	4520007	Serviços de Instalação, Manutenção e Reparação de Acessórios para Veículos Automotores
683	4520008	Serviços de Capotaria
684	4530701	Comércio por Atacado de Peças e Acessórios Novos para Veículos Automotores
685	4530702	Comércio por Atacado de Pneumáticos e Câmaras-de-Ar
686	4530703	Comércio A Varejo de Peças e Acessórios Novos para Veículos Automotores
687	4530704	Comércio A Varejo de Peças e Acessórios Usados para Veículos Automotores
688	4530705	Comércio A Varejo de Pneumáticos e Câmaras-de-Ar
689	4530706	Representantes Comerciais e Agentes do Comércio de Peças e Acessórios Novos e Usados para Veículos Automotores
690	4541201	Comércio por Atacado de Motocicletas e Motonetas
691	4541202	Comércio por Atacado de Peças e Acessórios para Motocicletas e Motonetas
692	4541203	Comércio A Varejo de Motocicletas e Motonetas Novas
693	4541204	Comércio A Varejo de Motocicletas e Motonetas Usadas
694	4541205	Comércio A Varejo de Peças e Acessórios para Motocicletas e Motonetas
695	4541206	Comércio A Varejo de Peças e Acessórios Novos para  Motocicletas e Motonetas
696	4541207	Comércio A Varejo de Peças e Acessórios Usados para Motocicletas e Motonetas
697	4542101	Representantes Comerciais e Agentes do Comércio de Motocicletas e Motonetas, Peças e Acessórios
698	4542102	Comércio Sob Consignação de Motocicletas e Motonetas
699	4543900	Manutenção e Reparação de Motocicletas e Motonetas
700	4611700	Representantes Comerciais e Agentes do Comércio de Matérias-Primas Agrícolas e Animais Vivos
701	4612500	Representantes Comerciais e Agentes do Comércio de Combustíveis, Minerais, Produtos Siderúrgicos e Químicos
702	4613300	Representantes Comerciais e Agentes do Comércio de Madeira, Material de Construção e Ferragens
703	4614100	Representantes Comerciais e Agentes do Comércio de Máquinas, Equipamentos, Embarcações e Aeronaves
704	4615000	Representantes Comerciais e Agentes do Comércio de Eletrodomésticos, Móveis e Artigos de Uso Doméstico
705	4616800	Representantes Comerciais e Agentes do Comércio de Têxteis, Vestuário, Calçados e Artigos de Viagem
706	4617600	Representantes Comerciais e Agentes do Comércio de Produtos Alimentícios, Bebidas e Fumo
707	4618401	Representantes Comerciais e Agentes do Comércio de Medicamentos, Cosméticos e Produtos de Perfumaria
708	4618402	Representantes Comerciais e Agentes do Comércio de Instrumentos e Materiais Odonto-Médico-Hospitalares
709	4618403	Representantes Comerciais e Agentes do Comércio de Jornais, Revistas e Outras Publicações
710	4618499	Outros Representantes Comerciais e Agentes do Comércio Especializado em Produtos Não Especificados Anteriormente
711	4619200	Representantes Comerciais e Agentes do Comércio de Mercadorias em Geral Não Especializado
712	4621400	Comércio Atacadista de Café em Grão
713	4622200	Comércio Atacadista de Soja
714	4623101	Comércio Atacadista de Animais Vivos
715	4623102	Comércio Atacadista de Couros, Lãs, Peles e Outros Subprodutos Não-Comestíveis de Origem Animal
716	4623103	Comércio Atacadista de Algodão
717	4623104	Comércio Atacadista de Fumo em Folha Não Beneficiado
718	4623105	Comércio Atacadista de Cacau
719	4623106	Comércio Atacadista de Sementes, Flores, Plantas e Gramas
720	4623107	Comércio Atacadista de Sisal
721	4623108	Comércio Atacadista de Matérias-Primas Agrícolas com Atividade de Fracionamento e Acondicionamento Associada
722	4623109	Comércio Atacadista de Alimentos para Animais
723	4623199	Comércio Atacadista de Matérias-Primas Agrícolas Não Especificadas Anteriormente
724	4631100	Comércio Atacadista de Leite e Laticínios
725	4632001	Comércio Atacadista de Cereais e Leguminosas Beneficiados
726	4632002	Comércio Atacadista de Farinhas, Amidos e Féculas
727	4632003	Comércio Atacadista de Cereais e Leguminosas Beneficiados, Farinhas, Amidos e Féculas, com Atividade de Fracionamento e Acondicionamento Associada
728	4633801	Comércio Atacadista de Frutas, Verduras, Raízes, Tubérculos, Hortaliças e Legumes Frescos
729	4633802	Comércio Atacadista de Aves Vivas e Ovos
730	4633803	Comércio Atacadista de Coelhos e Outros Pequenos Animais Vivos para Alimentação
731	4634601	Comércio Atacadista de Carnes Bovinas e Suínas e Derivados
732	4634602	Comércio Atacadista de Aves Abatidas e Derivados
733	4634603	Comércio Atacadista de Pescados e Frutos do Mar
734	4634699	Comércio Atacadista de Carnes e Derivados de Outros Animais
735	4635401	Comércio Atacadista de Água Mineral
736	4635402	Comércio Atacadista de Cerveja, Chope e Refrigerante
737	4635403	Comércio Atacadista de Bebidas com Atividade de Fracionamento e Acondicionamento Associada
738	4635499	Comércio Atacadista de Bebidas Não Especificadas Anteriormente
739	4636201	Comércio Atacadista de Fumo Beneficiado
740	4636202	Comércio Atacadista de Cigarros, Cigarrilhas e Charutos
741	4637101	Comércio Atacadista de Café Torrado, Moído e Solúvel
742	4637102	Comércio Atacadista de Açúcar
743	4637103	Comércio Atacadista de Óleos e Gorduras
744	4637104	Comércio Atacadista de Pães, Bolos, Biscoitos e Similares
745	4637105	Comércio Atacadista de Massas Alimentícias
746	4637106	Comércio Atacadista de Sorvetes
747	4637107	Comércio Atacadista de Chocolates, Confeitos, Balas, Bombons e Semelhantes
748	4637199	Comércio Atacadista Especializado em Outros Produtos Alimentícios Não Especificados Anteriormente
749	4639701	Comércio Atacadista de Produtos Alimentícios em Geral
750	4639702	Comércio Atacadista de Produtos Alimentícios em Geral, com Atividade de Fracionamento e Acondicionamento Associada
751	4641901	Comércio Atacadista de Tecidos
752	4641902	Comércio Atacadista de Artigos de Cama, Mesa e Banho
753	4641903	Comércio Atacadista de Artigos de Armarinho
754	4642701	Comércio Atacadista de Artigos do Vestuário e Acessórios, Exceto Profissionais e de Segurança
755	4642702	Comércio Atacadista de Roupas e Acessórios para Uso Profissional e de Segurança do Trabalho
756	4643501	Comércio Atacadista de Calçados
757	4643502	Comércio Atacadista de Bolsas, Malas e Artigos de Viagem
758	4644301	Comércio Atacadista de Medicamentos e Drogas de Uso Humano
759	4644302	Comércio Atacadista de Medicamentos e Drogas de Uso Veterinário
760	4645101	Comércio Atacadista de Instrumentos e Materiais para Uso Médico, Cirúrgico, Hospitalar e de Laboratórios
761	4645102	Comércio Atacadista de Próteses e Artigos de Ortopedia
762	4645103	Comércio Atacadista de Produtos Odontológicos
763	4646001	Comércio Atacadista de Cosméticos e Produtos de Perfumaria
764	4646002	Comércio Atacadista de Produtos de Higiene Pessoal
765	4647801	Comércio Atacadista de Artigos de Escritório e de Papelaria
766	4647802	Comércio Atacadista de Livros, Jornais e Outras Publicações
767	4649401	Comércio Atacadista de Equipamentos Elétricos de Uso Pessoal e Doméstico
768	4649402	Comércio Atacadista de Aparelhos Eletrônicos de Uso Pessoal e Doméstico
769	4649403	Comércio Atacadista de Bicicletas, Triciclos e Outros Veículos Recreativos
770	4649404	Comércio Atacadista de Móveis e Artigos de Colchoaria
771	4649405	Comércio Atacadista de Artigos de Tapeçaria; Persianas e Cortinas
772	4649406	Comércio Atacadista de Lustres, Luminárias e Abajures
773	4649407	Comércio Atacadista de Filmes, Cds, Dvds, Fitas e Discos
774	4649408	Comércio Atacadista de Produtos de Higiene, Limpeza e Conservação Domiciliar
775	7912100	Operadores Turísticos
776	4649409	Comércio Atacadista de Produtos de Higiene, Limpeza e Conservação Domiciliar, com Atividade de Fracionamento e Acondicionamento Associada
777	4649410	Comércio Atacadista de Jóias, Relógios e Bijuterias, Inclusive Pedras Preciosas e Semipreciosas Lapidadas
778	4649499	Comércio Atacadista de Outros Equipamentos e Artigos de Uso Pessoal e Doméstico Não Especificados Anteriormente
779	4651601	Comércio Atacadista de Equipamentos de Informática
780	4651602	Comércio Atacadista de Suprimentos para Informática
781	4652400	Comércio Atacadista de Componentes Eletrônicos e Equipamentos de Telefonia e Comunicação
782	4661300	Comércio Atacadista de Máquinas, Aparelhos e Equipamentos para Uso Agropecuário; Partes e Peças
783	4662100	Comércio Atacadista de Máquinas, Equipamentos para Terraplenagem, Mineração e Construção; Partes e Peças
784	4663000	Comércio Atacadista de Máquinas e Equipamentos para Uso Industrial; Partes e Peças
785	4664800	Comércio Atacadista de Máquinas, Aparelhos e Equipamentos para Uso Odonto-Médico-Hospitalar; Partes e Peças
786	4665600	Comércio Atacadista de Máquinas e Equipamentos para Uso Comercial; Partes e Peças
787	4669901	Comércio Atacadista de Bombas e Compressores; Partes e Peças
788	4669999	Comércio Atacadista de Outras Máquinas e Equipamentos Não Especificados Anteriormente; Partes e Peças
789	4671100	Comércio Atacadista de Madeira e Produtos Derivados
790	4672900	Comércio Atacadista de Ferragens e Ferramentas
791	4673700	Comércio Atacadista de Material Elétrico
792	4674500	Comércio Atacadista de Cimento
793	4679601	Comércio Atacadista de Tintas, Vernizes e Similares
794	4679602	Comércio Atacadista de Mármores e Granitos
795	4679603	Comércio Atacadista de Vidros, Espelhos, Vitrais e Molduras
796	4679604	Comércio Atacadista Especializado de Materiais de Construção Não Especificados Anteriormente
797	4679699	Comércio Atacadista de Materiais de Construção em Geral
798	4681801	Comércio Atacadista de Álcool Carburante, Biodiesel, Gasolina e Demais Derivados de Petróleo, Exceto Lubrificantes, Não Realizado por Transportador Re
799	4681802	Comércio Atacadista de Combustíveis Realizado por Transportador Retalhista (T.R.R.)
800	4681803	Comércio Atacadista de Combustíveis de Origem Vegetal, Exceto Álcool Carburante
801	4681804	Comércio Atacadista de Combustíveis de Origem Mineral em Bruto
802	4681805	Comércio Atacadista de Lubrificantes
803	4682600	Comércio Atacadista de Gás Liqüefeito de Petróleo (Glp)
804	4683400	Comércio Atacadista de Defensivos Agrícolas, Adubos, Fertilizantes e Corretivos do Solo
805	4684201	Comércio Atacadista de Resinas e Elastômeros
806	4684202	Comércio Atacadista de Solventes
807	4684299	Comércio Atacadista de Outros Produtos Químicos e Petroquímicos Não Especificados Anteriormente
808	4685100	Comércio Atacadista de Produtos Siderúrgicos e Metalúrgicos, Exceto para Construção
809	4686901	Comércio Atacadista de Papel e Papelão em Bruto
810	4686902	Comércio Atacadista de Embalagens
811	4687701	Comércio Atacadista de Resíduos de Papel e Papelão
812	4687702	Comércio Atacadista de Resíduos e Sucatas Não-Metálicos, Exceto de Papel e Papelão
813	4687703	Comércio Atacadista de Resíduos e Sucatas Metálicos
814	4689301	Comércio Atacadista de Produtos da Extração Mineral, Exceto Combustíveis
815	4689302	Comércio Atacadista de Fios e Fibras Beneficiados
816	4689399	Comércio Atacadista Especializado em Outros Produtos Intermediários Não Especificados Anteriormente
817	4691500	Comércio Atacadista de Mercadorias em Geral, com Predominância de Produtos Alimentícios
818	4692300	Comércio Atacadista de Mercadorias em Geral, com Predominância de Insumos Agropecuários
819	4693100	Comércio Atacadista de Mercadorias em Geral, Sem Predominância de Alimentos Ou de Insumos Agropecuários
820	4711301	Comércio Varejista de Mercadorias em Geral, com Predominância de Produtos Alimentícios - Hipermercados
821	4711302	Comércio Varejista de Mercadorias em Geral, com Predominância de Produtos Alimentícios - Supermercados
822	4712100	Comércio Varejista de Mercadorias em Geral, com Predominância de Produtos Alimentícios - Minimercados, Mercearias e Armazéns
823	4713001	Lojas de Departamentos Ou Magazines
824	4713002	Lojas de Variedades, Exceto Lojas de Departamentos Ou Magazines
825	4713003	Lojas Duty Free de Aeroportos Internacionais
826	4713004	Lojas de Departamentos Ou Magazines, Exceto Lojas Francas (Duty Free)
827	4713005	Lojas Francas (Duty Free) de Aeroportos, Portos e em Fronteiras Terrestres
828	4721101	Padaria e Confeitaria com Predominância de Produção Própria
829	4721102	Padaria e Confeitaria com Predominância de Revenda
830	4721103	Comércio Varejista de Laticínios e Frios
831	4721104	Comércio Varejista de Doces, Balas, Bombons e Semelhantes
832	4722901	Comércio Varejista de Carnes - Açougues
833	4722902	Peixaria
834	4723700	Comércio Varejista de Bebidas
835	4724500	Comércio Varejista de Hortifrutigranjeiros
836	4729601	Tabacaria
837	4729602	Comércio Varejista de Mercadorias em Lojas de Conveniência
838	4729699	Comércio Varejista de Produtos Alimentícios em Geral Ou Especializado em Produtos Alimentícios Não Especificados Anteriormente
839	4731800	Comércio Varejista de Combustíveis para Veículos Automotores
840	4732600	Comércio Varejista de Lubrificantes
841	4741500	Comércio Varejista de Tintas e Materiais para Pintura
842	4742300	Comércio Varejista de Material Elétrico
843	4743100	Comércio Varejista de Vidros
844	4744001	Comércio Varejista de Ferragens e Ferramentas
845	4744002	Comércio Varejista de Madeira e Artefatos
846	4744003	Comércio Varejista de Materiais Hidráulicos
847	4744004	Comércio Varejista de Cal, Areia, Pedra Britada, Tijolos e Telhas
848	4744005	Comércio Varejista de Materiais de Construção Não Especificados Anteriormente
849	4744006	Comércio Varejista de Pedras para Revestimento
850	4744099	Comércio Varejista de Materiais de Construção em Geral
851	4751200	Comércio Varejista Especializado de Equipamentos e Suprimentos de Informática
852	4751201	Comércio Varejista Especializado de Equipamentos e Suprimentos de Informática
853	4751202	Recarga de Cartuchos para Equipamentos de Informática
854	4752100	Comércio Varejista Especializado de Equipamentos de Telefonia e Comunicação
855	4753900	Comércio Varejista Especializado de Eletrodomésticos e Equipamentos de Áudio e Vídeo
856	4754701	Comércio Varejista de Móveis
857	4754702	Comércio Varejista de Artigos de Colchoaria
858	4754703	Comércio Varejista de Artigos de Iluminação
859	4755501	Comércio Varejista de Tecidos
860	4755502	Comercio Varejista de Artigos de Armarinho
861	4755503	Comercio Varejista de Artigos de Cama, Mesa e Banho
862	4756300	Comércio Varejista Especializado de Instrumentos Musicais e Acessórios
863	4757100	Comércio Varejista Especializado de Peças e Acessórios para Aparelhos Eletroeletrônicos para Uso Doméstico, Exceto Informática e Comunicação
864	4759801	Comércio Varejista de Artigos de Tapeçaria, Cortinas e Persianas
865	4759899	Comércio Varejista de Outros Artigos de Uso Pessoal e Doméstico Não Especificados Anteriormente
866	4761001	Comércio Varejista de Livros
867	4761002	Comércio Varejista de Jornais e Revistas
868	4761003	Comércio Varejista de Artigos de Papelaria
869	4762800	Comércio Varejista de Discos, Cds, Dvds e Fitas
870	4763601	Comércio Varejista de Brinquedos e Artigos Recreativos
871	4763602	Comércio Varejista de Artigos Esportivos
872	4763603	Comércio Varejista de Bicicletas e Triciclos; Peças e Acessórios
873	4763604	Comércio Varejista de Artigos de Caça, Pesca e Camping
874	4763605	Comércio Varejista de Embarcações e Outros Veículos Recreativos; Peças e Acessórios
875	4771701	Comércio Varejista de Produtos Farmacêuticos, Sem Manipulação de Fórmulas
876	4771702	Comércio Varejista de Produtos Farmacêuticos, com Manipulação de Fórmulas
877	4771703	Comércio Varejista de Produtos Farmacêuticos Homeopáticos
878	4771704	Comércio Varejista de Medicamentos Veterinários
879	4772500	Comércio Varejista de Cosméticos, Produtos de Perfumaria e de Higiene Pessoal
880	4773300	Comércio Varejista de Artigos Médicos e Ortopédicos
881	4774100	Comércio Varejista de Artigos de Óptica
882	4781400	Comércio Varejista de Artigos do Vestuário e Acessórios
883	4782201	Comércio Varejista de Calçados
884	4782202	Comércio Varejista de Artigos de Viagem
885	4783101	Comércio Varejista de Artigos de Joalheria
886	4783102	Comércio Varejista de Artigos de Relojoaria
887	4784900	Comércio Varejista de Gás Liqüefeito de Petróleo (Glp)
888	4785701	Comércio Varejista de Antigüidades
889	4785799	Comércio Varejista de Outros Artigos Usados
890	4789001	Comércio Varejista de Suvenires, Bijuterias e Artesanatos
891	4789002	Comércio Varejista de Plantas e Flores Naturais
892	4789003	Comércio Varejista de Objetos de Arte
893	4789004	Comércio Varejista de Animais Vivos e de Artigos e Alimentos para Animais de Estimação
894	4789005	Comércio Varejista de Produtos Saneantes Domissanitários
895	4789006	Comércio Varejista de Fogos de Artifício e Artigos Pirotécnicos
896	4789007	Comércio Varejista de Equipamentos para Escritório
897	4789008	Comércio Varejista de Artigos Fotográficos e para Filmagem
898	4789009	Comércio Varejista de Armas e Munições
899	4789099	Comércio Varejista de Outros Produtos Não Especificados Anteriormente
900	4911600	Transporte Ferroviário de Carga
901	4912401	Transporte Ferroviário de Passageiros Intermunicipal e Interestadual
902	4912402	Transporte Ferroviário de Passageiros Municipal e em Região Metropolitana
904	4921301	Transporte Rodoviário Coletivo de Passageiros, com Itinerário Fixo, Municipal
905	4921302	Transporte Rodoviário Coletivo de Passageiros, com Itinerário Fixo, Intermunicipal em Região Metropolitana
906	4922101	Transporte Rodoviário Coletivo de Passageiros, com Itinerário Fixo, Intermunicipal, Exceto em Região Metropolitana
907	4922102	Transporte Rodoviário Coletivo de Passageiros, com Itinerário Fixo, Interestadual
908	4922103	Transporte Rodoviário Coletivo de Passageiros, com Itinerário Fixo, Internacional
909	4923001	Serviço de Táxi
910	4923002	Serviço de Transporte de Passageiros - Locação de Automóveis com Motorista
911	4924800	Transporte Escolar
912	4929901	Transporte Rodoviário Coletivo de Passageiros, Sob Regime de Fretamento, Municipal
913	4929902	Transporte Rodoviário Coletivo de Passageiros, Sob Regime de Fretamento, Intermunicipal, Interestadual e Internacional
914	4929903	Organização de Excursões em Veículos Rodoviários Próprios, Municipal
915	4929904	Organização de Excursões em Veículos Rodoviários Próprios, Intermunicipal, Interestadual e Internacional
916	4929999	Outros Transportes Rodoviários de Passageiros Não Especificados Anteriormente
917	4930201	Transporte Rodoviário de Carga, Exceto Produtos Perigosos e Mudanças, Municipal.
918	6612605	Agentes de Investimentos em Aplicações Financeiras
919	4930202	Transporte Rodoviário de Carga, Exceto Produtos Perigosos e Mudanças, Intermunicipal, Interestadual e Internacional
920	4930203	Transporte Rodoviário de Produtos Perigosos
921	4930204	Transporte Rodoviário de Mudanças
922	4940000	Transporte Dutoviário
923	4950700	Trens Turísticos, Teleféricos e Similares
924	5011401	Transporte Marítimo de Cabotagem - Carga
925	5011402	Transporte Marítimo de Cabotagem - Passageiros
926	5012201	Transporte Marítimo de Longo Curso - Carga
927	5012202	Transporte Marítimo de Longo Curso - Passageiros
928	5021101	Transporte por Navegação Interior de Carga, Municipal, Exceto Travessia
929	5021102	Transporte por Navegação Interior de Carga, Intermunicipal, Interestadual e Internacional, Exceto Travessia
930	5022001	Transporte por Navegação Interior de Passageiros em Linhas Regulares, Municipal, Exceto Travessia
931	5022002	Transporte por Navegação Interior de Passageiros em Linhas Regulares, Intermunicipal, Interestadual e Internacional, Exceto Travessia
932	5030101	Navegação de Apoio Marítimo
933	5030102	Navegação de Apoio Portuário
934	5030103	Serviço de Rebocadores e Empurradores
935	5091201	Transporte por Navegação de Travessia, Municipal
936	5091202	Transporte por Navegação de Travessia Intermunicipal, Interestadual e Internacional
937	5099801	Transporte Aquaviário para Passeios Turísticos
938	5099899	Outros Transportes Aquaviários Não Especificados Anteriormente
939	5111100	Transporte Aéreo de Passageiros Regular
940	5112901	Serviço de Táxi Aéreo e Locação de Aeronaves com Tripulação
941	5112999	Outros Serviços de Transporte Aéreo de Passageiros Não-Regular
942	5120000	Transporte Aéreo de Carga
943	5130700	Transporte Espacial
944	5211701	Armazéns Gerais - Emissão de Warrant
945	5211702	Guarda-Móveis
946	5211799	Depósitos de Mercadorias para Terceiros, Exceto Armazéns Gerais e Guarda-Móveis
947	5212500	Carga e Descarga
948	5221400	Concessionárias de Rodovias, Pontes, Túneis e Serviços Relacionados
949	5222200	Terminais Rodoviários e Ferroviários
950	5223100	Estacionamento de Veículos
951	5229001	Serviços de Apoio Ao Transporte por Táxi, Inclusive Centrais de Chamada
952	5229002	Serviços de Reboque de Veículos
953	5229099	Outras Atividades Auxiliares dos Transportes Terrestres Não Especificadas Anteriormente
954	5231101	Administração da Infra-Estrutura Portuária
955	5231102	Atividades do Operador Portuário
956	5231103	Gestão de Terminais Aquaviários
957	5232000	Atividades de Agenciamento Marítimo
958	5239700	Atividades Auxiliares dos Transportes Aquaviários Não Especificadas Anteriormente
959	5239701	Serviços de Praticagem
960	5239799	Atividades Auxiliares dos Transportes Aquaviários Não Especificadas Anteriormente
961	5240101	Operação dos Aeroportos e Campos de Aterrissagem
962	5240199	Atividades Auxiliares dos Transportes Aéreos, Exceto Operação dos Aeroportos e Campos de Aterrissagem
963	5250801	Comissaria de Despachos
964	5250802	Atividades de Despachantes Aduaneiros
965	5250803	Agenciamento de Cargas, Exceto para O Transporte Marítimo
966	5250804	Organização Logística do Transporte de Carga
967	5250805	Operador de Transporte Multimodal - Otm
968	5310501	Atividades do Correio Nacional
969	5310502	Atividades de Franqueadas do Correio Nacional
970	5320201	Serviços de Malote Não Realizados Pelo Correio Nacional
971	5320202	Serviços de Entrega Rápida
972	5510801	Hotéis
973	5510802	Apart-Hotéis
974	5510803	Motéis
975	5590601	Albergues, Exceto Assistenciais
976	5590602	Campings
977	5590603	Pensões (Alojamento)
978	5590699	Outros Alojamentos Não Especificados Anteriormente
979	5611201	Restaurantes e Similares
980	5611202	Bares e Outros Estabelecimentos Especializados em Servir Bebidas
981	5611203	Lanchonetes, Casas de Chá, de Sucos e Similares
982	5611204	Bares e Outros Estabelecimentos Especializados em Servir Bebidas, Sem Entretenimento
983	5611205	Bares e Outros Estabelecimentos Especializados em Servir Bebidas, com Entretenimento
984	5612100	Serviços Ambulantes de Alimentação
985	5620101	Fornecimento de Alimentos Preparados Preponderantemente para Empresas
986	5620102	Serviços de Alimentação para Eventos e Recepções - Bufê
987	5620103	Cantinas - Serviços de Alimentação Privativos
988	5620104	Fornecimento de Alimentos Preparados Preponderantemente para Consumo Domiciliar
989	5811500	Edição de Livros
990	5812300	Edição de Jornais
991	5812301	Edição de Jornais Diários
992	5812302	Edição de Jornais Não Diários
993	5813100	Edição de Revistas
994	5819100	Edição de Cadastros, Listas e de Outros Produtos Gráficos
995	5821200	Edição Integrada À Impressão de Livros
996	5822100	Edição Integrada À Impressão de Jornais
997	5822101	Edição Integrada À Impressão de Jornais Diários
998	5822102	Edição Integrada À Impressão de Jornais Não Diários
999	5823900	Edição Integrada À Impressão de Revistas
1000	5829800	Edição Integrada À Impressão de Cadastros, Listas e de Outros Produtos Gráficos
1001	5911101	Estúdios Cinematográficos
1002	5911102	Produção de Filmes para Publicidade
1003	5911199	Atividades de Produção Cinematográfica, de Vídeos e de Programas de Televisão Não Especificadas Anteriormente
1004	5912001	Serviços de Dublagem
1005	5912002	Serviços de Mixagem Sonora em Produção Audiovisual
1006	5912099	Atividades de Pós-Produção Cinematográfica, de Vídeos e de Programas de Televisão Não Especificadas Anteriormente
1007	5913800	Distribuição Cinematográfica, de Vídeo e de Programas de Televisão
1008	5914600	Atividades de Exibição Cinematográfica
1009	5920100	Atividades de Gravação de Som e de Edição de Música
1010	6010100	Atividades de Rádio
1011	6021700	Atividades de Televisão Aberta
1012	6022501	Programadoras
1013	6022502	Atividades Relacionadas À Televisão por Assinatura, Exceto Programadoras
1014	6110801	Serviços de Telefonia Fixa Comutada - Stfc
1015	6110802	Serviços de Redes de Transportes de Telecomunicações - Srtt
1016	6110803	Serviços de Comunicação Multimídia - Scm
1017	6110899	Serviços de Telecomunicações por Fio Não Especificados Anteriormente
1018	6120501	Telefonia Móvel Celular
1019	6120502	Serviço Móvel Especializado - Sme
1020	6120599	Serviços de Telecomunicações Sem Fio Não Especificados Anteriormente
1021	6130200	Telecomunicações por Satélite
1022	6141800	Operadoras de Televisão por Assinatura por Cabo
1023	6142600	Operadoras de Televisão por Assinatura por Microondas
1024	6143400	Operadoras de Televisão por Assinatura por Satélite
1025	6190601	Provedores de Acesso Às Redes de Comunicações
1026	6190602	Provedores de Voz Sobre Protocolo Internet - Voip
1027	6190699	Outras Atividades de Telecomunicações Não Especificadas Anteriormente
1028	6201500	Desenvolvimento de Programas de Computador Sob Encomenda
1029	6201501	Desenvolvimento de Programas de Computador Sob Encomenda
1030	6201502	Web Design
1031	6202300	Desenvolvimento e Licenciamento de Programas de Computador Customizáveis
1032	6203100	Desenvolvimento e Licenciamento de Programas de Computador Não-Customizáveis
1033	6204000	Consultoria em Tecnologia da Informação
1034	6209100	Suporte Técnico, Manutenção e Outros Serviços em Tecnologia da Informação
1035	6311900	Tratamento de Dados, Provedores de Serviços de Aplicação e Serviços de Hospedagem Na Internet
1036	6319400	Portais, Provedores de Conteúdo e Outros Serviços de Informação Na Internet
1037	6391700	Agências de Notícias
1038	6399200	Outras Atividades de Prestação de Serviços de Informação Não Especificadas Anteriormente
1039	6410700	Banco Central
1040	6421200	Bancos Comerciais
1041	6422100	Bancos Múltiplos, com Carteira Comercial
1042	6423900	Caixas Econômicas
1043	6424701	Bancos Cooperativos
1044	6424702	Cooperativas Centrais de Crédito
1045	6424703	Cooperativas de Crédito Mútuo
1046	6424704	Cooperativas de Crédito Rural
1047	6431000	Bancos Múltiplos, Sem Carteira Comercial
1048	6432800	Bancos de Investimento
1049	6433600	Bancos de Desenvolvimento
1050	6434400	Agências de Fomento
1051	6435201	Sociedades de Crédito Imobiliário
1052	6435202	Associações de Poupança e Empréstimo
1053	6435203	Companhias Hipotecárias
1054	6436100	Sociedades de Crédito, Financiamento e Investimento - Financeiras
1055	6437900	Sociedades de Crédito Ao Microempreendedor
1056	6438701	Bancos de Câmbio
1057	6438799	Outras Instituições de Intermediação Não-Monetária Não Especificadas Anteriormente
1058	6440900	Arrendamento Mercantil
1059	6450600	Sociedades de Capitalização
1060	6461100	Holdings de Instituições Financeiras
1061	6462000	Holdings de Instituições Não-Financeiras
1062	6463800	Outras Sociedades de Participação, Exceto Holdings
1063	6470101	Fundos de Investimento, Exceto Previdenciários e Imobiliários
1064	6470102	Fundos de Investimento Previdenciários
1065	6470103	Fundos de Investimento Imobiliários
1066	6491300	Sociedades de Fomento Mercantil - Factoring
1067	6492100	Securitização de Créditos
1068	6493000	Administração de Consórcios para Aquisição de Bens e Direitos
1069	6499901	Clubes de Investimento
1070	6499902	Sociedades de Investimento
1071	6499903	Fundo Garantidor de Crédito
1072	6499904	Caixas de Financiamento de Corporações
1073	6499905	Concessão de Crédito Pelas Oscip
1074	6499999	Outras Atividades de Serviços Financeiros Não Especificadas Anteriormente
1075	6511101	Sociedade Seguradora de Seguros Vida
1076	6511102	Planos de Auxílio-Funeral
1077	6512000	Sociedade Seguradora de Seguros Não Vida
1078	6520100	Sociedade Seguradora de Seguros Saúde
1079	6530800	Resseguros
1080	6541300	Previdência Complementar Fechada
1081	6542100	Previdência Complementar Aberta
1082	6550200	Planos de Saúde
1083	6611801	Bolsa de Valores
1084	6611802	Bolsa de Mercadorias
1085	6611803	Bolsa de Mercadorias e Futuros
1086	6611804	Administração de Mercados de Balcão Organizados
1087	6612601	Corretoras de Títulos e Valores Mobiliários
1088	6612602	Distribuidoras de Títulos e Valores Mobiliários
1089	6612603	Corretoras de Câmbio
1090	6612604	Corretoras de Contratos de Mercadorias
1091	6613400	Administração de Cartões de Crédito
1092	6619301	Serviços de Liquidação e Custódia
1093	6619302	Correspondentes de Instituições Financeiras
1094	6619303	Representações de Bancos Estrangeiros
1095	6619304	Caixas Eletrônicos
1096	6619305	Operadoras de Cartões de Débito
1097	6619399	Outras Atividades Auxiliares dos Serviços Financeiros Não Especificadas Anteriormente
1098	6621501	Peritos e Avaliadores de Seguros
1099	6621502	Auditoria e Consultoria Atuarial
1100	6622300	Corretores e Agentes de Seguros, de Planos de Previdência Complementar e de Saúde
1101	6629100	Atividades Auxiliares dos Seguros, da Previdência Complementar e dos Planos de Saúde Não Especificadas Anteriormente
1102	6630400	Atividades de Administração de Fundos por Contrato Ou Comissão
1103	6810201	Compra e Venda de Imóveis Próprios
1104	6810202	Aluguel de Imóveis Próprios
1105	6810203	Loteamento de Imóveis Próprios
1106	6821801	Corretagem Na Compra e Venda e Avaliação de Imóveis
1107	6821802	Corretagem No Aluguel de Imóveis
1108	6822600	Gestão e Administração da Propriedade Imobiliária
1109	6911701	Serviços Advocatícios
1110	6911702	Atividades Auxiliares da Justiça
1111	6911703	Agente de Propriedade Industrial
1112	6912500	Cartórios
1113	6920601	Atividades de Contabilidade
1114	6920602	Atividades de Consultoria e Auditoria Contábil e Tributária
1115	7020400	Atividades de Consultoria em Gestão Empresarial, Exceto Consultoria Técnica Específica
1116	7111100	Serviços de Arquitetura
1117	7112000	Serviços de Engenharia
1118	7119701	Serviços de Cartografia, Topografia e Geodésia
1119	7119702	Atividades de Estudos Geológicos
1120	7119703	Serviços de Desenho Técnico Relacionados À Arquitetura e Engenharia
1121	7119704	Serviços de Perícia Técnica Relacionados À Segurança do Trabalho
1122	7119799	Atividades Técnicas Relacionadas À Engenharia e Arquitetura Não Especificadas Anteriormente
1123	7120100	Testes e Análises Técnicas
1124	7210000	Pesquisa e Desenvolvimento Experimental em Ciências Físicas e Naturais
1125	7220700	Pesquisa e Desenvolvimento Experimental em Ciências Sociais e Humanas
1126	7311400	Agências de Publicidade
1127	7312200	Agenciamento de Espaços para Publicidade, Exceto em Veículos de Comunicação
1128	7319001	Criação de Estandes para Feiras e Exposições
1129	7319002	Promoção de Vendas
1130	7319003	Marketing Direto
1131	7319004	Consultoria em Publicidade
1132	7319099	Outras Atividades de Publicidade Não Especificadas Anteriormente
1133	7320300	Pesquisas de Mercado e de Opinião Pública
1134	7410201	Design
1135	7410202	Design de Interiores
1136	7410203	Design de Produto
1137	7410299	Atividades de Design Não Especificadas Anteriormente
1138	7420001	Atividades de Produção de Fotografias, Exceto Aérea e Submarina
1139	7420002	Atividades de Produção de Fotografias Aéreas e Submarinas
1140	7420003	Laboratórios Fotográficos
1141	7420004	Filmagem de Festas e Eventos
1142	7420005	Serviços de Microfilmagem
1143	7490101	Serviços de Tradução, Interpretação e Similares
1144	7490102	Escafandria e Mergulho
1145	7490103	Serviços de Agronomia e de Consultoria Às Atividades Agrícolas e Pecuárias
1146	7490104	Atividades de Intermediação e Agenciamento de Serviços e Negócios em Geral, Exceto Imobiliários
1147	7490105	Agenciamento de Profissionais para Atividades Esportivas, Culturais e Artísticas
1148	7490199	Outras Atividades Profissionais, Científicas e Técnicas Não Especificadas Anteriormente
1149	7500100	Atividades Veterinárias
1150	7711000	Locação de Automóveis Sem Condutor
1151	7719501	Locação de Embarcações Sem Tripulação, Exceto para Fins Recreativos
1152	7719502	Locação de Aeronaves Sem Tripulação
1153	7719599	Locação de Outros Meios de Transporte Não Especificados Anteriormente, Sem Condutor
1154	7721700	Aluguel de Equipamentos Recreativos e Esportivos
1155	7722500	Aluguel de Fitas de Vídeo, Dvds e Similares
1156	7723300	Aluguel de Objetos do Vestuário, Jóias e Acessórios
1157	7729201	Aluguel de Aparelhos de Jogos Eletrônicos
1158	7729202	Aluguel de Móveis, Utensílios e Aparelhos de Uso Doméstico e Pessoal; Instrumentos Musicais
1159	7729203	Aluguel de Material Médico
1160	7729299	Aluguel de Outros Objetos Pessoais e Domésticos Não Especificados Anteriormente
1161	7731400	Aluguel de Máquinas e Equipamentos Agrícolas Sem Operador
1162	7732201	Aluguel de Máquinas e Equipamentos para Construção Sem Operador, Exceto Andaimes
1163	7732202	Aluguel de Andaimes
1164	7733100	Aluguel de Máquinas e Equipamentos para Escritórios
1165	7739001	Aluguel de Máquinas e Equipamentos para Extração de Minérios e Petróleo, Sem Operador
1166	7739002	Aluguel de Equipamentos Científicos, Médicos e Hospitalares, Sem Operador
1167	7739003	Aluguel de Palcos, Coberturas e Outras Estruturas de Uso Temporário, Exceto Andaimes
1168	7739099	Aluguel de Outras Máquinas e Equipamentos Comerciais e Industriais Não Especificados Anteriormente, Sem Operador
1169	7740300	Gestão de Ativos Intangíveis Não-Financeiros
1170	7810800	Seleção e Agenciamento de Mão-de-Obra
1171	7820500	Locação de Mão-de-Obra Temporária
1172	7830200	Fornecimento e Gestão de Recursos Humanos para Terceiros
1173	7990200	Serviços de Reservas e Outros Serviços de Turismo Não Especificados Anteriormente
1174	8011101	Atividades de Vigilância e Segurança Privada
1175	8011102	Serviços de Adestramento de Cães de Guarda
1176	8012900	Atividades de Transporte de Valores
1177	8020000	Atividades de Monitoramento de Sistemas de Segurança
1178	8020001	Atividades de Monitoramento de Sistemas de Segurança Eletrônico
1179	8020002	Outras Atividades de Serviços de Segurança
1180	8030700	Atividades de Investigação Particular
1181	8111700	Serviços Combinados para Apoio A Edifícios, Exceto Condomínios Prediais
1182	8112500	Condomínios Prediais
1183	8121400	Limpeza em Prédios e em Domicílios
1184	8122200	Imunização e Controle de Pragas Urbanas
1185	8129000	Atividades de Limpeza Não Especificadas Anteriormente
1186	8130300	Atividades Paisagísticas
1187	8211300	Serviços Combinados de Escritório e Apoio Administrativo
1188	8219901	Fotocópias
1189	8219999	Preparação de Documentos e Serviços Especializados de Apoio Administrativo Não Especificados Anteriormente
1190	8220200	Atividades de Teleatendimento
1191	8230001	Serviços de Organização de Feiras, Congressos, Exposições e Festas
1192	8230002	Casas de Festas e Eventos
1193	8291100	Atividades de Cobranças e Informações Cadastrais
1194	8292000	Envasamento e Empacotamento Sob Contrato
1195	8299701	Medição de Consumo de Energia Elétrica, Gás e Água
1196	8299702	Emissão de Vales-Alimentação, Vales-Transporte e Similares
1197	8299703	Serviços de Gravação de Carimbos, Exceto Confecção
1198	8299704	Leiloeiros Independentes
1199	8299705	Serviços de Levantamento de Fundos Sob Contrato
1200	8299706	Casas Lotéricas
1201	8299707	Salas de Acesso À Internet
1202	8299799	Outras Atividades de Serviços Prestados Principalmente Às Empresas Não Especificadas Anteriormente
1203	8411600	Administração Pública em Geral
1204	8412400	Regulação das Atividades de Saúde, Educação, Serviços Culturais e Outros Serviços Sociais
1205	8413200	Regulação das Atividades Econômicas
1206	8421300	Relações Exteriores
1208	8423000	Justiça
1209	8424800	Segurança e Ordem Pública
1210	8425600	Defesa Civil
1211	8430200	Seguridade Social Obrigatória
1212	8511200	Educação Infantil - Creche
1213	8512100	Educação Infantil - Pré-Escola
1214	8513900	Ensino Fundamental
1215	8520100	Ensino Médio
1216	8531700	Educação Superior - Graduação
1217	8532500	Educação Superior - Graduação e Pós-Graduação
1218	8533300	Educação Superior - Pós-Graduação e Extensão
1219	8541400	Educação Profissional de Nível Técnico
1220	8542200	Educação Profissional de Nível Tecnológico
1221	8550301	Administração de Caixas Escolares
1222	8550302	Atividades de Apoio À Educação, Exceto Caixas Escolares
1223	8591100	Ensino de Esportes
1224	8592901	Ensino de Dança
1225	8592902	Ensino de Artes Cênicas, Exceto Dança
1226	8592903	Ensino de Música
1227	8592999	Ensino de Arte e Cultura Não Especificado Anteriormente
1228	8593700	Ensino de Idiomas
1229	8599601	Formação de Condutores
1230	8599602	Cursos de Pilotagem
1231	8599603	Treinamento em Informática
1232	8599604	Treinamento em Desenvolvimento Profissional e Gerencial
1233	8599605	Cursos Preparatórios para Concursos
1234	8599699	Outras Atividades de Ensino Não Especificadas Anteriormente
1235	8610101	Atividades de Atendimento Hospitalar, Exceto Pronto-Socorro e Unidades para Atendimento A Urgências
1236	8610102	Atividades de Atendimento em Pronto-Socorro e Unidades Hospitalares para Atendimento A Urgências
1237	8621601	Uti Móvel
1238	8621602	Serviços Móveis de Atendimento A Urgências, Exceto por Uti Móvel
1239	8622400	Serviços de Remoção de Pacientes, Exceto Os Serviços Móveis de Atendimento A Urgências
1240	8630501	Atividade Médica Ambulatorial com Recursos para Realização de Procedimentos Cirúrgicos
1241	8630502	Atividade Médica Ambulatorial com Recursos para Realização de Exames Complementares
1242	8630503	Atividade Médica Ambulatorial Restrita A Consultas
1243	8630504	Atividade Odontológica
1244	8630505	Atividade Odontológica Sem Recursos para Realização de Procedimentos Cirúrgicos
1245	8630506	Serviços de Vacinação e Imunização Humana
1246	8630507	Atividades de Reprodução Humana Assistida
1247	8630599	Atividades de Atenção Ambulatorial Não Especificadas Anteriormente
1248	8640201	Laboratórios de Anatomia Patológica e Citológica
1249	8640202	Laboratórios Clínicos
1250	8640203	Serviços de Diálise e Nefrologia
1251	8640204	Serviços de Tomografia
1252	8640205	Serviços de Diagnóstico por Imagem com Uso de Radiação Ionizante, Exceto Tomografia
1253	8640206	Serviços de Ressonância Magnética
1254	8640207	Serviços de Diagnóstico por Imagem Sem Uso de Radiação Ionizante, Exceto Ressonância Magnética
1255	8640208	Serviços de Diagnóstico por Registro Gráfico - Ecg, Eeg e Outros Exames Análogos
1256	8640209	Serviços de Diagnóstico por Métodos Ópticos - Endoscopia e Outros Exames Análogos
1257	8640210	Serviços de Quimioterapia
1258	8640211	Serviços de Radioterapia
1259	8640212	Serviços de Hemoterapia
1260	8640213	Serviços de Litotripcia
1261	8640214	Serviços de Bancos de Células e Tecidos Humanos
1262	8640299	Atividades de Serviços de Complementação Diagnóstica e Terapêutica Não Especificadas Anteriormente
1263	8650001	Atividades de Enfermagem
1264	8650002	Atividades de Profissionais da Nutrição
1265	8650003	Atividades de Psicologia e Psicanálise
1266	8650004	Atividades de Fisioterapia
1267	8650005	Atividades de Terapia Ocupacional
1268	8650006	Atividades de Fonoaudiologia
1269	8650007	Atividades de Terapia de Nutrição Enteral e Parenteral
1270	8650099	Atividades de Profissionais da Área de Saúde Não Especificadas Anteriormente
1271	8660700	Atividades de Apoio À Gestão de Saúde
1272	8690901	Atividades de Práticas Integrativas e Complementares em Saúde Humana
1273	8690902	Atividades de Banco de Leite Humano
1274	8690903	Atividades de Acupuntura
1275	8690904	Atividades de Podologia
1276	8690999	Outras Atividades de Atenção À Saúde Humana Não Especificadas Anteriormente
1277	8711501	Clínicas e Residências Geriátricas
1278	8711502	Instituições de Longa Permanência para Idosos
1279	8711503	Atividades de Assistência A Deficientes Físicos, Imunodeprimidos e Convalescentes
1280	8711504	Centros de Apoio A Pacientes com Câncer e com Aids
1281	8711505	Condomínios Residenciais para Idosos e Deficientes Físicos
1282	8712300	Atividades de Fornecimento de Infra-Estrutura de Apoio e Assistência A Paciente No Domicílio
1283	8720401	Atividades de Centros de Assistência Psicossocial
1284	8720499	Atividades de Assistência Psicossocial e À Saúde A Portadores de Distúrbios Psíquicos, Deficiência Mental e Dependência Química e Grupos Similares Não
1285	8730101	Orfanatos
1286	8730102	Albergues Assistenciais
1287	8730199	Atividades de Assistência Social Prestadas em Residências Coletivas e Particulares Não Especificadas Anteriormente
1288	8800600	Serviços de Assistência Social Sem Alojamento
1289	9001901	Produção Teatral
1290	9001902	Produção Musical
1291	9001903	Produção de Espetáculos de Dança
1292	9001904	Produção de Espetáculos Circenses, de Marionetes e Similares
1293	9001905	Produção de Espetáculos de Rodeios, Vaquejadas e Similares
1294	9001906	Atividades de Sonorização e de Iluminação
1295	9001999	Artes Cênicas, Espetáculos e Atividades Complementares Não Especificadas Anteriormente
1296	9002701	Atividades de Artistas Plásticos, Jornalistas Independentes e Escritores
1297	9002702	Restauração de Obras-de-Arte
1298	9003500	Gestão de Espaços para Artes Cênicas, Espetáculos e Outras Atividades Artísticas
1299	9101500	Atividades de Bibliotecas e Arquivos
1300	9102301	Atividades de Museus e de Exploração de Lugares e Prédios Históricos e Atrações Similares
1301	9102302	Restauração e Conservação de Lugares e Prédios Históricos
1302	9103100	Atividades de Jardins Botânicos, Zoológicos, Parques Nacionais, Reservas Ecológicas e Áreas de Proteção Ambiental
1303	9200301	Casas de Bingo
1304	9200302	Exploração de Apostas em Corridas de Cavalos
1305	9200399	Exploração de Jogos de Azar e Apostas Não Especificados Anteriormente
1306	9311500	Gestão de Instalações de Esportes
1307	9312300	Clubes Sociais, Esportivos e Similares
1308	9313100	Atividades de Condicionamento Físico
1309	9319101	Produção e Promoção de Eventos Esportivos
1310	9319199	Outras Atividades Esportivas Não Especificadas Anteriormente
1311	9321200	Parques de Diversão e Parques Temáticos
1312	9329801	Discotecas, Danceterias, Salões de Dança e Similares
1313	9329802	Exploração de Boliches
1314	9329803	Exploração de Jogos de Sinuca, Bilhar e Similares
1315	9329804	Exploração de Jogos Eletrônicos Recreativos
1316	9329899	Outras Atividades de Recreação e Lazer Não Especificadas Anteriormente
1317	9411100	Atividades de Organizações Associativas Patronais e Empresariais
1318	9412000	Atividades de Organizações Associativas Profissionais
1319	9412001	Atividades de Fiscalização Profissional
1320	9412099	Outras Atividades Associativas Profissionais
1321	9420100	Atividades de Organizações Sindicais
1322	9430800	Atividades de Associações de Defesa de Direitos Sociais
1323	9491000	Atividades de Organizações Religiosas Ou Filosóficas
1324	9492800	Atividades de Organizações Políticas
1325	9493600	Atividades de Organizações Associativas Ligadas À Cultura e À Arte
1326	9499500	Atividades Associativas Não Especificadas Anteriormente
1327	9511800	Reparação e Manutenção de Computadores e de Equipamentos Periféricos
1328	9512600	Reparação e Manutenção de Equipamentos de Comunicação
1329	9521500	Reparação e Manutenção de Equipamentos Eletroeletrônicos de Uso Pessoal e Doméstico
1330	9529101	Reparação de Calçados, Bolsas e Artigos de Viagem
1331	9529102	Chaveiros
1332	9529103	Reparação de Relógios
1333	9529104	Reparação de Bicicletas, Triciclos e Outros Veículos Não-Motorizados
1334	9529105	Reparação de Artigos do Mobiliário
1335	9529106	Reparação de Jóias
1336	9529199	Reparação e Manutenção de Outros Objetos e Equipamentos Pessoais e Domésticos Não Especificados Anteriormente
1337	9601701	Lavanderias
1338	9601702	Tinturarias
1339	9601703	Toalheiros
1340	9602501	Cabeleireiros, Manicure e Pedicure
1341	9602502	Atividades de Estética e Outros Serviços de Cuidados com A Beleza
1342	9603301	Gestão e Manutenção de Cemitérios
1344	9603303	Serviços de Sepultamento
1345	9603304	Serviços de Funerárias
1346	9603305	Serviços de Somatoconservação
1347	9603399	Atividades Funerárias e Serviços Relacionados Não Especificados Anteriormente
1348	9609201	Clinicas de Estética e Similares
1349	9609202	Agências Matrimoniais
1350	9609203	Alojamento, Higiene e Embelezamento de Animais
1351	9609204	Exploração de Máquinas de Serviços Pessoais Acionadas por Moeda
1352	9609205	Atividades de Sauna e Banhos
1353	9609206	Serviços de Tatuagem e Colocação de Piercing
1354	9609207	Alojamento de Animais Domésticos
1355	9609208	Higiene e Embelezamento de Animais Domésticos
1356	9609299	Outras Atividades de Serviços Pessoais Não Especificadas Anteriormente
1357	9700500	Serviços Domésticos
1358	9900800	Organismos Internacionais e Outras Instituições Extraterritoriais
1359	8888888	Atividade Econônica Não Informada
\.


--
-- Data for Name: contrato; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.contrato (id_contrato, id_processo_licitatorio, numero_contrato, descricao_objetivo, data_assinatura, data_vencimento, valor_contrato, valor_garantia, id_contrato_superior) FROM stdin;
\.


--
-- Data for Name: convenio; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.convenio (id_convenio, descricao_objeto, data_assinatura, data_fim_vigencia, valor_convenio) FROM stdin;
\.


--
-- Data for Name: cotacao_contrato; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.cotacao_contrato (id_cotacao, id_contrato) FROM stdin;
\.


--
-- Data for Name: empenho; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.empenho (id_empenho, num_empenho, valor_empenho, descricao, data_empenho, prestacao_contas, regularizacao_orcamentaria, id_processo_licitatorio, id_empenho_superior, id_pessoa) FROM stdin;
\.


--
-- Data for Name: ente; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.ente (id_ente, id_municipio, ente) FROM stdin;
\.


--
-- Data for Name: estabelecimento; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.estabelecimento (id_estabelecimento, cnpj, cnpj_ordem, cnpj_dv, nome_fantasia, id_situacao_cadastral, id_motivo_situacao_cadastral, cnae_principal, tipo_logradouro, logradouro, numero, complemento, bairro, cep, ddd_1, telefone_1, ddd_2, telefone_2, ddd_fax, fax, email, situacao_especial, id_municipio, data_situacao, data_situacao_especial, data_inicio_atividade) FROM stdin;
\.


--
-- Data for Name: estabelecimento_cnae_secundario; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.estabelecimento_cnae_secundario (cnae, id_estabelecimento) FROM stdin;
\.


--
-- Data for Name: estatistica_item_bp; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.estatistica_item_bp (id_estatistica_item, tipo_estatistica, valor_estatistica, id_banco_de_precos) FROM stdin;
\.


--
-- Data for Name: execucao_metodo_objeto_analise; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.execucao_metodo_objeto_analise (id_execucao_metodo, id_objeto_analise) FROM stdin;
\.


--
-- Data for Name: grafico_bp; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.grafico_bp (id_grafico_bp, tipo_grafico, conteudo, texto, id_banco_de_precos) FROM stdin;
\.


--
-- Data for Name: hipertipologia_alerta; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.hipertipologia_alerta (id_hipertipologia_alerta, nome, descricao, id_megatipologia_alerta) FROM stdin;
17	Empresa contratada com punição vigente pela administração  	Empresa contratada com punição vigente pela administração  	3
18	Empresa majora valor de contrato mediante aditivos com valor incongruente	Empresa majora valor de contrato mediante aditivos com valor incongruente	3
19	Empresa com vínculo político	Empresa com vínculo político	3
20	Empresa com vínculo com organização criminosa	Empresa com vínculo com organização criminosa	3
1	Empresas compartilham características	Empresas compartilham características	1
2	Empresas combinam de uma sempre perder para outra ganhar ou alternam vitórias	Empresas combinam de uma sempre perder para outra ganhar ou alternam vitórias	1
3	Empresas apresentam propostas com proporcionalidade de valor/preço	Empresas apresentam propostas com proporcionalidade de valor/preço	1
4	Empresas apresentam propostas idênticas em unidades gestoras diferentes 	Empresas apresentam propostas idênticas em unidades gestoras diferentes 	1
5	Sócio com indícios de baixa renda (bolsa família)	Sócio com indícios de baixa renda (bolsa família)	2
6	Sócio com indícios de baixa renda (remuneração)	Sócio com indícios de baixa renda (remuneração)	2
7	Sócio é servidor público	Sócio é servidor público	2
8	Sócio é familiar de servidor público	Sócio é familiar de servidor público	2
9	Sócio é político	Sócio é político	2
21	Discrepâncias entre valor previsto e contratado	Discrepâncias entre valor previsto e contratado	4
22	Competitividade entre empresas licitantes	Competitividade entre empresas licitantes	4
23	Notícias de fraudes	Notícias de fraudes	4
24	Processos do SIG	Processos do SIG	4
10	Sócio é familiar de político	Sócio é familiar de político	2
11	Sócio de empresa contratada pela administração também é sócio de outra empresa que tem como sócio um político	Sócio de empresa contratada pela administração também é sócio de outra empresa que tem como sócio um político	2
12	Sócio de empresa já punida também é sócio de empresa contratada pela administração 	Sócio de empresa já punida também é sócio de empresa contratada pela administração 	2
13	Sócio é suspeito - pessoa falecida, com indício de documento falso ou possível crime	Sócio é suspeito - pessoa falecida, com indício de documento falso ou possível crime	2
14	Porte da empresa incongruente com licitações em que a empresa participa	Porte da empresa incongruente com licitações em que a empresa participa	3
15	Empresa recém constituída	Empresa recém constituída	3
16	Múltiplos CNAEs incongruentes entre si	Múltiplos CNAEs incongruentes entre si	3
\.


--
-- Data for Name: inidonea; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.inidonea (id_inidonea, data_publicacao, data_validade, id_pessoa) FROM stdin;
\.


--
-- Data for Name: item_licitacao; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.item_licitacao (id_item_licitacao, numero_sequencial_item, descricao_item_licitacao, data_homologacao, qtd_item_licitacao, descricao_unidade_medida, id_processo_licitatorio, valor_estimado_item) FROM stdin;
\.


--
-- Data for Name: item_nfe; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.item_nfe (id_item_nfe, id_nfe, id_item, situacao_nfe, data_emissao, cod_mun_emitente, cod_mun_destinatario, cfop_produto, ncm_produto, gtin_produto, descricao_produto, quantidade_comercial, unidade_comercial, valor_unitario_comercial, id_item_licitacao, valor_desconto, valor_frete, valor_seguro, valor_outras_despesas, valor_total_comercial, valor_total_liquido, valor_unitario_liquido, tipo_item_nfe) FROM stdin;
\.


--
-- Data for Name: item_nfe_classificacao_produto_servico; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.item_nfe_classificacao_produto_servico (id_classificacao_produto_servico, id_item_nfe, id_item_nfe_classificacao_produto_servico) FROM stdin;
\.


--
-- Data for Name: item_nfe_grupo_bp; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.item_nfe_grupo_bp (id_grupo_bp, id_item_nfe, id_item_nfe_grupo_bp) FROM stdin;
\.


--
-- Data for Name: items_removidos_bp; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.items_removidos_bp (id_items_removidos_bp, id_banco_de_precos, id_nfe, id_grupo_bp, id_pessoa, data_remocao) FROM stdin;
80	\N	\N	1853	4992521959	2025-12-01 11:35:53.690496+00
87	\N	\N	1008	7426468909	2025-12-01 13:42:36.517545+00
88	\N	\N	3587	7426468909	2025-12-01 13:42:39.720172+00
90	\N	\N	4667	7426468909	2025-12-01 14:31:43.789571+00
91	\N	\N	4189	7426468909	2025-12-01 14:35:29.795031+00
84	\N	\N	4532	2606670051	2025-12-01 13:26:27.398962+00
104	\N	\N	2162	7426468909	2025-12-01 21:38:00.119827+00
105	\N	\N	4741	7426468909	2025-12-01 21:38:00.225728+00
106	\N	\N	2582	7426468909	2025-12-01 21:38:09.664628+00
107	\N	\N	2588	7426468909	2025-12-01 21:38:09.759573+00
108	\N	\N	5167	7426468909	2025-12-01 21:38:09.863843+00
48	\N	\N	3674	7426468909	2025-11-30 02:10:44.05989+00
49	\N	\N	1095	7426468909	2025-11-30 02:10:56.981283+00
50	\N	\N	3790	7426468909	2025-11-30 02:11:15.917846+00
109	\N	\N	5519	7426468909	2025-12-01 21:38:09.972109+00
110	\N	\N	5488	7426468909	2025-12-01 21:38:10.057515+00
111	\N	\N	5486	7426468909	2025-12-01 21:38:10.168632+00
55	\N	\N	4873	7426468909	2025-11-30 02:59:30.738181+00
116	\N	\N	2294	7426468909	2025-12-03 18:56:57.941886+00
117	\N	\N	3615	7426468909	2025-12-03 19:40:36.930902+00
118	\N	\N	5166	80056540906	2025-12-03 19:41:45.859359+00
119	\N	\N	1037	80056540906	2025-12-11 18:06:26.004855+00
120	\N	\N	4741	80056540906	2025-12-11 21:36:05.178464+00
\.


--
-- Data for Name: liquidacao; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.liquidacao (id_liquidacao, data_liquidacao, valor_liquidacao, id_empenho, nota_liquidacao, id_pessoa) FROM stdin;
\.


--
-- Data for Name: megatipologia_alerta; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.megatipologia_alerta (id_megatipologia_alerta, nome, descricao) FROM stdin;
1	Relação entre empresas participantes de uma mesma licitação	Relação entre empresas participantes de uma mesma licitação
2	Características do(s) sócio(s) de uma empresa	Características do(s) sócio(s) de uma empresa
3	Características de uma empresa	Características de uma empresa
4	Características da licitação	Características da licitação
\.


--
-- Data for Name: metodo_analise; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.metodo_analise (id_metodo_analise, nome, versao, template_longo, template_curto, instrucoes_execucao, metodologia, tipo_instrucao, id_tipologia_alerta) FROM stdin;
\.


--
-- Data for Name: metodo_de_agrupamento_bp; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.metodo_de_agrupamento_bp (id_metodo_de_agrupamento_bp, nome, data_criacao, id_classificacao_produto_servico) FROM stdin;
\.


--
-- Data for Name: modalidade_licitacao; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.modalidade_licitacao (id_modalidade_licitacao, descricao) FROM stdin;
1	Convite
2	Tomada de Preços
3	Concorrência
4	Concorrência Presencial
5	Concorrência Eletrônica
6	Leilão
7	Leilão Presencial
8	Leilão Eletrônico
9	Concurso
10	Pregão Presencial
11	Pregão Eletrônico
12	Pregão
13	Dispensa de Licitação
14	Inexigibilidade de Licitação
15	Regime Diferenciado de Contratação
16	Procedimento Licitatório Lei 13.303/06
17	Chamada Pública
18	Pré-qualificação
19	Credenciamento
20	Manifestação de Interesse
21	Diálogo Competitivo
22	Contrato
99	Outras
\.


--
-- Data for Name: motivo_situacao_cadastral; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.motivo_situacao_cadastral (id_motivo_situacao_cadastral, descricao) FROM stdin;
0	Sem Motivo
1	Extinção por Encerramento Liquidação Voluntária
2	Incorporação
3	Fusão
4	Cisão Total
5	Encerramento da Falência
6	Encerramento da Liquidação
7	Elevação a Matriz
8	Transpasse
9	Não Início de Atividade
10	Extinção pelo Encerramento da Liquidação Judicial
11	Anulação por Multiplicidade
12	Anulação Online de Ofício
13	Omissa Contumaz
14	Omissa Não Localizada
15	Inexistência de Fato
16	Anulação por Vícios
17	Baixa Iniciada em Análise
18	Interrupção Temporária das Atividades
21	Pedido de Baixa Indeferida
24	Por Emissão Certidão Negativa
28	Transferência Filial Condição Matriz
31	Extinção-Unificação da Filial
33	Transferência do Órgão Local à Condição de Filial do Órgão Regional
34	Anulação de Inscrição Indevida
35	Empresa Estrangeira Aguardando Documentação
36	Prática Irregular de Operação de Comércio Exterior
37	Baixa de Produtor Rural
38	Baixa Deferida pela RFB Aguardando Análise do Convenente
39	Baixa Deferida pela RFB e Indeferida pelo Convenente
40	Baixa Indeferida pela RFB e Aguardando Análise do Convenente
41	Baixa Indeferida pela RFB e Deferida pelo Convenente
42	Baixa Deferida pela RFB e SEFIN, Aguardando Análise SEFAZ
43	Baixa Deferida pela RFB, Aguardando Análise da SEFAZ e Indeferida pela SEFIN
44	Baixa Deferida pela RFB e SEFAZ, Aguardando Análise SEFIN
45	Baixa Deferida pela RFB, Aguardando Análise da SEFIN e Indeferida pela SEFAZ
46	Baixa Deferida pela RFB e SEFAZ e Indeferida pela SEFIN
47	Baixa Deferida pela RFB e SEFIN e Indeferida pela SEFAZ
48	Baixa Indeferida pela RFB, Aguardando Análise SEFAZ e Deferida pela SEFIN
49	Baixa Indeferida pela RFB, Aguardando Análise da SEFAZ e Indeferida pela SEFIN
50	Baixa Indeferida pela RFB, Deferida pela SEFAZ e Aguardando Análise da SEFIN
51	Baixa Indeferida pela RFB e SEFAZ, Aguardando Análise da SEFIN
52	Baixa Indeferida pela RFB, Deferida pela SEFAZ e Indeferida pela SEFIN
53	Baixa Indeferida pela RFB e SEFAZ e Deferida pela SEFIN
54	Extinção - Tratamento Diferenciado Dado às ME e EPP (Lei Complementar Número 123/2006)
55	Deferido pelo Convenente, Aguardando Análise da RFB
60	Artigo 30, VI, da IN 748/2007
61	Índice Interpos. Fraudulenta
62	Falta de Pluralidade de Sócios
63	Omissão de Declarações
64	Localização Desconhecida
66	Inaptidão
67	Registro Cancelado
70	Anulação por Não Confirmado Ato de Registro do MEI na Junta Comercial
71	Inaptidão (Lei 11.941/2009 Art.54)
72	Determinação Judicial
73	Comissão Contumaz
74	Inconsistência Cadastral
75	Óbito do MEI - Titular Falecido
80	Baixa Registrada na Junta, Indeferida na RFB
81	Solicitação da Administração Tributária Estadual/Municipal
82	Suspenso Perante a Comissão de Valores Mobiliários - CVM
93	CNPJ - Titular Baixado
\.


--
-- Data for Name: movimentacao_empenho; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.movimentacao_empenho (id_movimentacao_empenho, id_empenho) FROM stdin;
\.


--
-- Data for Name: municipio; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.municipio (id_municipio, nome_municipio, sigla_uf, nome_uf) FROM stdin;
91	Praia Grande	SC	Santa Catarina
124	Tangará	SC	Santa Catarina
155	Iraceminha	SC	Santa Catarina
165	Romelândia	SC	Santa Catarina
175	São Lourenço Do Oeste	SC	Santa Catarina
199	Nova Itaberaba	SC	Santa Catarina
237	Lajeado Grande	SC	Santa Catarina
1	Joinville	SC	Santa Catarina
171	Bom Retiro	SC	Santa Catarina
176	Lindóia do Sul	SC	Santa Catarina
181	Mondaí	SC	Santa Catarina
186	Abelardo Luz	SC	Santa Catarina
191	Xaxim	SC	Santa Catarina
196	Barra Velha	SC	Santa Catarina
201	Vitor Meireles	SC	Santa Catarina
206	Ipuaçu	SC	Santa Catarina
211	Cordilheira Alta	SC	Santa Catarina
216	Santa Rosa de Lima	SC	Santa Catarina
221	Morro da Fumaça	SC	Santa Catarina
231	Itaiópolis	SC	Santa Catarina
236	Rio Negrinho	SC	Santa Catarina
241	Salete	SC	Santa Catarina
246	Treviso	SC	Santa Catarina
251	Pedras Grandes	SC	Santa Catarina
256	Morro Grande	SC	Santa Catarina
261	São Miguel do Oeste	SC	Santa Catarina
266	Camboriú	SC	Santa Catarina
271	Princesa	SC	Santa Catarina
276	Bom Jesus	SC	Santa Catarina
281	Treze de Maio	SC	Santa Catarina
286	Presidente Nereu	SC	Santa Catarina
291	Laguna	SC	Santa Catarina
226	Pinheiro Preto	SC	Santa Catarina
172	Guatambú	SC	Santa Catarina
177	Petrolândia	SC	Santa Catarina
182	Santa Rosa do Sul	SC	Santa Catarina
187	São Bernardino	SC	Santa Catarina
192	Imbituba	SC	Santa Catarina
197	Imbuia	SC	Santa Catarina
202	Balneário Barra do Sul	SC	Santa Catarina
212	Agronômica	SC	Santa Catarina
217	Cerro Negro	SC	Santa Catarina
222	Timbó	SC	Santa Catarina
227	Formosa do Sul	SC	Santa Catarina
232	Frei Rogério	SC	Santa Catarina
242	Balneário Arroio do Silva	SC	Santa Catarina
247	Maracajá	SC	Santa Catarina
252	Passo de Torres	SC	Santa Catarina
257	Jupiá	SC	Santa Catarina
262	Bandeirante	SC	Santa Catarina
272	Capão Alto	SC	Santa Catarina
277	Irineópolis	SC	Santa Catarina
282	Maravilha	SC	Santa Catarina
287	Rodeio	SC	Santa Catarina
292	Rio do Oeste	SC	Santa Catarina
207	Guaramirim	SC	Santa Catarina
178	Gaspar	SC	Santa Catarina
183	Piratuba	SC	Santa Catarina
188	Flor do Sertão	SC	Santa Catarina
193	Santiago do Sul	SC	Santa Catarina
198	Cocal do Sul	SC	Santa Catarina
203	Ibiam	SC	Santa Catarina
208	Passos Maia	SC	Santa Catarina
213	Bocaina do Sul	SC	Santa Catarina
218	Bom Jardim da Serra	SC	Santa Catarina
223	Itapema	SC	Santa Catarina
228	Anitápolis	SC	Santa Catarina
233	Calmon	SC	Santa Catarina
238	Armazém	SC	Santa Catarina
243	Nova Veneza	SC	Santa Catarina
248	Mirim Doce	SC	Santa Catarina
253	Caxambu do Sul	SC	Santa Catarina
258	São Miguel da Boa Vista	SC	Santa Catarina
263	Celso Ramos	SC	Santa Catarina
273	Urupema	SC	Santa Catarina
283	Vidal Ramos	SC	Santa Catarina
288	Capivari de Baixo	SC	Santa Catarina
293	Tunápolis	SC	Santa Catarina
267	Ituporanga	SC	Santa Catarina
173	Vargeão	SC	Santa Catarina
278	Schroeder	SC	Santa Catarina
174	São João do Oeste	SC	Santa Catarina
179	Riqueza	SC	Santa Catarina
184	Vargem Bonita	SC	Santa Catarina
189	Pomerode	SC	Santa Catarina
194	Ouro	SC	Santa Catarina
204	Zortéa	SC	Santa Catarina
209	Caibi	SC	Santa Catarina
214	Ponte Serrada	SC	Santa Catarina
219	Dionísio Cerqueira	SC	Santa Catarina
224	Itapiranga	SC	Santa Catarina
229	Palma Sola	SC	Santa Catarina
234	Jaborá	SC	Santa Catarina
239	União do Oeste	SC	Santa Catarina
244	Governador Celso Ramos	SC	Santa Catarina
249	Porto Belo	SC	Santa Catarina
254	Tigrinhos	SC	Santa Catarina
259	Brunópolis	SC	Santa Catarina
264	Videira	SC	Santa Catarina
269	São Francisco do Sul	SC	Santa Catarina
279	Lebon Régis	SC	Santa Catarina
284	Modelo	SC	Santa Catarina
289	Ilhota	SC	Santa Catarina
294	Balneário Rincão	SC	Santa Catarina
3	Marema	SC	Santa Catarina
4	Braço do Norte	SC	Santa Catarina
5	Florianópolis	SC	Santa Catarina
6	Jaguaruna	SC	Santa Catarina
7	Palhoça	SC	Santa Catarina
8	Palmeira	SC	Santa Catarina
9	São Cristóvão do Sul	SC	Santa Catarina
10	Blumenau	SC	Santa Catarina
11	Canoinhas	SC	Santa Catarina
13	Criciúma	SC	Santa Catarina
14	Saltinho	SC	Santa Catarina
16	São José do Cerrito	SC	Santa Catarina
17	Urubici	SC	Santa Catarina
18	Serra Alta	SC	Santa Catarina
19	Campo Belo do Sul	SC	Santa Catarina
20	Irati	SC	Santa Catarina
21	Itajaí	SC	Santa Catarina
22	Taió	SC	Santa Catarina
23	Mafra	SC	Santa Catarina
24	Macieira	SC	Santa Catarina
25	Bela Vista do Toldo	SC	Santa Catarina
26	Caçador	SC	Santa Catarina
27	Paraíso	SC	Santa Catarina
28	São José	SC	Santa Catarina
29	Jaraguá do Sul	SC	Santa Catarina
30	Rio do Sul	SC	Santa Catarina
31	São Bonifácio	SC	Santa Catarina
32	Garopaba	SC	Santa Catarina
33	Gravatal	SC	Santa Catarina
34	Chapecó	SC	Santa Catarina
35	Imaruí	SC	Santa Catarina
36	Major Vieira	SC	Santa Catarina
37	Santa Cecília	SC	Santa Catarina
38	Lages	SC	Santa Catarina
39	Santa Terezinha	SC	Santa Catarina
40	Tijucas	SC	Santa Catarina
41	São Bento do Sul	SC	Santa Catarina
42	Rio Rufino	SC	Santa Catarina
43	Balneário Camboriú	SC	Santa Catarina
44	Saudades	SC	Santa Catarina
45	Tubarão	SC	Santa Catarina
46	Itapoá	SC	Santa Catarina
47	Concórdia	SC	Santa Catarina
48	Brusque	SC	Santa Catarina
49	Xanxerê	SC	Santa Catarina
50	Penha	SC	Santa Catarina
51	Botuverá	SC	Santa Catarina
52	Grão-Pará	SC	Santa Catarina
53	Ermo	SC	Santa Catarina
54	Itá	SC	Santa Catarina
55	Lontras	SC	Santa Catarina
56	Belmonte	SC	Santa Catarina
58	Peritiba	SC	Santa Catarina
59	Benedito Novo	SC	Santa Catarina
60	Coronel Freitas	SC	Santa Catarina
61	Águas Frias	SC	Santa Catarina
62	Cunha Porã	SC	Santa Catarina
63	Sombrio	SC	Santa Catarina
65	Guarujá do Sul	SC	Santa Catarina
66	Presidente Getúlio	SC	Santa Catarina
67	Santa Helena	SC	Santa Catarina
68	Catanduvas	SC	Santa Catarina
69	Massaranduba	SC	Santa Catarina
70	Paulo Lopes	SC	Santa Catarina
71	Braço do Trombudo	SC	Santa Catarina
72	Iomerê	SC	Santa Catarina
73	Araquari	SC	Santa Catarina
74	Campo Erê	SC	Santa Catarina
75	Apiúna	SC	Santa Catarina
76	Águas de Chapecó	SC	Santa Catarina
77	José Boiteux	SC	Santa Catarina
78	Ponte Alta do Norte	SC	Santa Catarina
79	Chapadão do Lageado	SC	Santa Catarina
80	Agrolândia	SC	Santa Catarina
81	Entre Rios	SC	Santa Catarina
82	Antônio Carlos	SC	Santa Catarina
83	Ponte Alta	SC	Santa Catarina
84	Timbé do Sul	SC	Santa Catarina
85	Arroio Trinta	SC	Santa Catarina
86	Orleans	SC	Santa Catarina
87	Correia Pinto	SC	Santa Catarina
88	Rio das Antas	SC	Santa Catarina
89	São Ludgero	SC	Santa Catarina
90	Capinzal	SC	Santa Catarina
92	São João do Itaperiú	SC	Santa Catarina
93	Xavantina	SC	Santa Catarina
94	Atalanta	SC	Santa Catarina
95	Ascurra	SC	Santa Catarina
96	Indaial	SC	Santa Catarina
97	Coronel Martins	SC	Santa Catarina
98	Balneário Gaivota	SC	Santa Catarina
99	Rancho Queimado	SC	Santa Catarina
100	São Joaquim	SC	Santa Catarina
101	Iporã do Oeste	SC	Santa Catarina
102	Ipumirim	SC	Santa Catarina
103	Canelinha	SC	Santa Catarina
104	Sul Brasil	SC	Santa Catarina
105	Matos Costa	SC	Santa Catarina
106	Turvo	SC	Santa Catarina
107	Trombudo Central	SC	Santa Catarina
108	Faxinal dos Guedes	SC	Santa Catarina
109	Treze Tílias	SC	Santa Catarina
110	São Carlos	SC	Santa Catarina
111	Bombinhas	SC	Santa Catarina
112	Seara	SC	Santa Catarina
114	Monte Carlo	SC	Santa Catarina
115	Pouso Redondo	SC	Santa Catarina
116	Planalto Alegre	SC	Santa Catarina
117	Nova Erechim	SC	Santa Catarina
118	Ipira	SC	Santa Catarina
119	Águas Mornas	SC	Santa Catarina
120	Descanso	SC	Santa Catarina
121	Balneário Piçarras	SC	Santa Catarina
122	Doutor Pedrinho	SC	Santa Catarina
123	Rio do Campo	SC	Santa Catarina
125	Bom Jesus do Oeste	SC	Santa Catarina
126	Curitibanos	SC	Santa Catarina
127	São João Batista	SC	Santa Catarina
128	Quilombo	SC	Santa Catarina
129	Santo Amaro da Imperatriz	SC	Santa Catarina
130	Alto Bela Vista	SC	Santa Catarina
131	Campo Alegre	SC	Santa Catarina
132	Três Barras	SC	Santa Catarina
133	Ibirama	SC	Santa Catarina
134	São José do Cedro	SC	Santa Catarina
135	São Pedro de Alcântara	SC	Santa Catarina
136	Nova Trento	SC	Santa Catarina
137	São João do Sul	SC	Santa Catarina
138	Paial	SC	Santa Catarina
139	Fraiburgo	SC	Santa Catarina
140	Água Doce	SC	Santa Catarina
141	Major Gercino	SC	Santa Catarina
142	Forquilhinha	SC	Santa Catarina
143	Barra Bonita	SC	Santa Catarina
144	Vargem	SC	Santa Catarina
145	Anita Garibaldi	SC	Santa Catarina
146	Leoberto Leal	SC	Santa Catarina
147	Aurora	SC	Santa Catarina
148	Palmitos	SC	Santa Catarina
149	Ibicaré	SC	Santa Catarina
150	Herval d'Oeste	SC	Santa Catarina
151	Lacerdópolis	SC	Santa Catarina
152	Joaçaba	SC	Santa Catarina
153	Sangão	SC	Santa Catarina
154	Angelina	SC	Santa Catarina
156	Lauro Müller	SC	Santa Catarina
157	Luzerna	SC	Santa Catarina
158	Erval Velho	SC	Santa Catarina
159	Arabutã	SC	Santa Catarina
160	Santa Terezinha do Progresso	SC	Santa Catarina
162	Jacinto Machado	SC	Santa Catarina
163	Arvoredo	SC	Santa Catarina
164	Dona Emma	SC	Santa Catarina
166	Ouro Verde	SC	Santa Catarina
167	Salto Veloso	SC	Santa Catarina
168	Monte Castelo	SC	Santa Catarina
169	Alfredo Wagner	SC	Santa Catarina
170	Irani	SC	Santa Catarina
57	Novo Horizonte	SC	Santa Catarina
161	Rio dos Cedros	SC	Santa Catarina
180	São Domingos	SC	Santa Catarina
185	Papanduva	SC	Santa Catarina
190	Rio Fortuna	SC	Santa Catarina
195	Pinhalzinho	SC	Santa Catarina
200	Galvão	SC	Santa Catarina
205	Laurentino	SC	Santa Catarina
210	Painel	SC	Santa Catarina
215	Jardinópolis	SC	Santa Catarina
220	Porto União	SC	Santa Catarina
225	Timbó Grande	SC	Santa Catarina
230	Urussanga	SC	Santa Catarina
235	Navegantes	SC	Santa Catarina
240	Anchieta	SC	Santa Catarina
245	Guaraciaba	SC	Santa Catarina
250	Cunhataí	SC	Santa Catarina
255	Abdon Batista	SC	Santa Catarina
260	Guabiruba	SC	Santa Catarina
265	Garuva	SC	Santa Catarina
270	Meleiro	SC	Santa Catarina
275	Presidente Castello Branco	SC	Santa Catarina
280	São Martinho	SC	Santa Catarina
285	Luiz Alves	SC	Santa Catarina
295	Pescaria Brava	SC	Santa Catarina
64	Içara	SC	Santa Catarina
290	Corupá	SC	Santa Catarina
113	Campos Novos	SC	Santa Catarina
268	Siderópolis	SC	Santa Catarina
2	Biguaçu	SC	Santa Catarina
12	Araranguá	SC	Santa Catarina
15	Otacílio Costa	SC	Santa Catarina
274	Witmarsum	SC	Santa Catarina
\.


--
-- Data for Name: natureza_juridica; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.natureza_juridica (id_natureza_juridica, descricao, orgao_publico) FROM stdin;
1015	Órgão Público do Poder Executivo Federal	t
1023	Órgão Público do Poder Executivo Estadual ou do Distrito Federal	t
1031	Órgão Público do Poder Executivo Municipal	t
1040	Órgão Público do Poder Legislativo Federal	t
1058	Órgão Público do Poder Legislativo Estadual ou do Distrito Federal	t
1066	Órgão Público do Poder Legislativo Municipal	t
1074	Órgão Público do Poder Judiciário Federal	t
1082	Órgão Público do Poder Judiciário Estadual	t
1350	Entidade Pública sob Regime Especial	t
0	Natureza Jurídica Não Informada	f
1163	Órgão Público Autônomo Federal	t
1171	Órgão Público Autônomo Estadual ou do Distrito Federal	t
1180	Órgão Público Autônomo Municipal	t
1228	Consórcio Público de Direito Privado	t
1252	Fundação Pública de Direito Privado Federal	t
1260	Fundação Pública de Direito Privado Estadual ou do Distrito Federal	t
1279	Fundação Pública de Direito Privado Municipal	t
2011	Empresa Pública	t
1139	Fundação Pública de Direito Público Federal	t
1147	Fundação Pública de Direito Público Estadual ou do Distrito Federal	t
1155	Fundação Pública de Direito Público Municipal	t
1210	Consórcio Público de Direito Público (Associação Pública)	t
3271	Órgão de Direção Local de Partido Político	f
3280	Comitê Financeiro de Partido Político	f
3298	Frente Plebiscitária ou Referendária	f
3301	Organização Social (OS)	f
3999	Associação Privada	f
4014	Empresa Individual Imobiliária	f
4090	Candidato a Cargo Político Eletivo	f
4120	Produtor Rural (Pessoa Física)	f
5010	Organização Internacional	f
5029	Representação Diplomática Estrangeira	f
1104	Autarquia Federal	f
1112	Autarquia Estadual ou do Distrito Federal	f
1120	Autarquia Municipal	f
1198	Comissão Polinacional	f
1236	Estado ou Distrito Federal	f
1287	Fundo Público da Administração Indireta Federal	t
1295	Fundo Público da Administração Indireta Estadual ou do Distrito Federal	t
1309	Fundo Público da Administração Indireta Municipal	t
1317	Fundo Público da Administração Direta Federal	t
1325	Fundo Público da Administração Direta Estadual ou do Distrito Federal	t
1333	Fundo Público da Administração Direta Municipal	t
1244	Município	f
1341	União	f
2038	Sociedade de Economia Mista	f
2046	Sociedade Anônima Aberta	f
2054	Sociedade Anônima Fechada	f
2062	Sociedade Empresária Limitada	f
2070	Sociedade Empresária em Nome Coletivo	f
2089	Sociedade Empresária em Comandita Simples	f
2097	Sociedade Empresária em Comandita por Ações	f
2100	Sociedade Mercantil de Capital e Indústria	f
2127	Sociedade em Conta de Participação	f
2143	Cooperativa	f
2151	Consórcio de Sociedades	f
2160	Grupo de Sociedades	f
2178	Estabelecimento, no Brasil, de Sociedade Estrangeira	f
2194	Estabelecimento, no Brasil, de Empresa Binacional Argentino-Brasileira	f
2216	Empresa Domiciliada no Exterior	f
2224	Clube/Fundo de Investimento	f
2232	Sociedade Simples Pura	f
2240	Sociedade Simples Limitada	f
2259	Sociedade Simples em Nome Coletivo	f
2267	Sociedade Simples em Comandita Simples	f
2275	Empresa Binacional	f
2283	Consórcio de Empregadores	f
2291	Consórcio Simples	f
2305	Empresa Individual de Responsabilidade Limitada (de Natureza Empresária)	f
2313	Empresa Individual de Responsabilidade Limitada (de Natureza Simples)	f
2321	Sociedade Unipessoal de Advocacia	f
2330	Cooperativas de Consumo	f
2348	Empresa Simples de Inovação	f
3034	Serviço Notarial e Registral (Cartório)	f
3069	Fundação Privada	f
3077	Serviço Social Autônomo	f
3085	Condomínio Edilício	f
3107	Comissão de Conciliação Prévia	f
3115	Entidade de Mediação e Arbitragem	f
3131	Entidade Sindical	f
3204	Estabelecimento, no Brasil, de Fundação ou Associação Estrangeiras	f
3212	Fundação ou Associação Domiciliada no Exterior	f
3220	Organização Religiosa	f
3239	Comunidade Indígena	f
3247	Fundo Privado	f
3255	Órgão de Direção Nacional de Partido Político	f
3263	Órgão de Direção Regional de Partido Político	f
5037	Outras Instituições Extraterritoriais	f
3328	Plano de Benefícios de Previdência Complementar Fechada	f
2135	Empresário (Individual)	\N
\.


--
-- Data for Name: nfe; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.nfe (id_nfe, situacao_nfe, forma_pgto, num_serie_nfe, num_doc_nfe, data_emissao, data_saida, tipo_operacao, cnpj_emitente, cpf_emitente, ie_emitente, ie_st_emitente, im_emitente, cnae_emitente, crt_emitente, nome_emitente, nome_fant_emitente, fone_emitente, logradouro_emitente, numero_emitente, cpl_emitente, bairro_emitente, cod_mun_emitente, nome_mun_emitente, uf_emitente, cod_pais_emitente, nome_pais_emitente, cep_emitente, cnpj_destinatario, nome_destinatario, ie_destinatario, insc_suframa_destinatario, logradouro_destinatario, numero_destinatario, cpl_destinatario, bairro_destinatario, cod_mun_destinatario, nome_mun_destinatario, uf_destinatario, cod_pais_destinatario, nome_pais_destinatario, cep_destinatario, cpf_destinatario, chave_acesso, id_pagamento_empenho, id_estabelecimento, id_processo_licitatorio) FROM stdin;
\.


--
-- Data for Name: noticia; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.noticia (id_noticia, titulo, link, numero_edital, id_modalidade_licitacao, objeto, data_publicacao, nome_portal, texto, chamada, id_processo_licitatorio) FROM stdin;
\.


--
-- Data for Name: noticia_municipio; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.noticia_municipio (id_noticia, id_municipio, id_noticia_municipio) FROM stdin;
\.


--
-- Data for Name: objeto_analise; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.objeto_analise (id_objeto_analise, nome_objeto, id_unidade_gestora, id_ente, id_item_nfe, id_documento, id_item_licitacao, id_pessoa, id_processo_licitatorio) FROM stdin;
\.


--
-- Data for Name: pagamento_empenho; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pagamento_empenho (id_pagamento_empenho, data_pagamento, valor_pagamento, nro_ordem_bancaria, data_exigibilidade, data_publicacao_justificativa, data_validade, cod_banco, cod_agencia, numero_conta_bancaria_pagadora, id_liquidacao, id_empenho) FROM stdin;
\.


--
-- Data for Name: pessoa; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pessoa (id_pessoa, nome, estrangeiro) FROM stdin;
\.


--
-- Data for Name: pessoa_fisica; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pessoa_fisica (cpf, id_situacao_cadastral, faixa_etaria, data_nascimento, id_pessoa) FROM stdin;
\.


--
-- Data for Name: pessoa_fisica_estabelecimento; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pessoa_fisica_estabelecimento (id_estabelecimento, cargo, cpf) FROM stdin;
\.


--
-- Data for Name: pessoa_fisica_nfe; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pessoa_fisica_nfe (id_nfe, cpf) FROM stdin;
\.


--
-- Data for Name: pessoa_juridica; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pessoa_juridica (cnpj, razao_social, id_natureza_juridica, capital_social, porte_empresa, id_pessoa, orgao_publico) FROM stdin;
\.


--
-- Data for Name: pessoa_municipio; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pessoa_municipio (id_pessoa, id_municipio) FROM stdin;
\.


--
-- Data for Name: pessoa_pessoa_juridica; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.pessoa_pessoa_juridica (participacao, tipo_sociedade, responsavel, classificacao, cnpj, id_pessoa) FROM stdin;
\.


--
-- Data for Name: processo_licitatorio_pessoa; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.processo_licitatorio_pessoa (id_processo_licitatorio, id_pessoa, cnpj_consorcio, data_validade_proposta, participante_cotacao) FROM stdin;
\.


--
-- Data for Name: sig; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sig (id_sig, numero_processo_sig, data_abertura, data_fechamento, promotor, fraude_investigada, status) FROM stdin;
\.


--
-- Data for Name: sig_documento; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sig_documento (id_documento, id_sig) FROM stdin;
\.


--
-- Data for Name: sig_processo_licitatorio; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sig_processo_licitatorio (id_sig, id_processo_licitatorio) FROM stdin;
\.


--
-- Data for Name: situacao_cadastral; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.situacao_cadastral (id_situacao_cadastral, descricao) FROM stdin;
1	Nula
2	Ativa
3	Suspensa
4	Inapta
8	Baixada
\.


--
-- Data for Name: tipo_cotacao; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tipo_cotacao (id_tipo_cotacao, descricao) FROM stdin;
1	Por Item
2	Por Lote
3	Preço Global
\.


--
-- Data for Name: tipo_documento; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tipo_documento (id_tipo_documento, descricao) FROM stdin;
1	Aviso de Contratação Direta
2	Edital
3	Minuta do Contrato
4	Termo de Referência
5	Anteprojeto
6	Projeto Básico
7	Estudo Técnico Preliminar
8	Projeto Executivo
9	Mapa de Riscos
10	DFD
11	Ata de Registro de Preço
12	Contrato
13	Termo de Rescisão
14	Termo Aditivo
15	Termo de Apostilamento
16	Outros Documentos do Processo
17	Nota de Empenho
18	Relatório Final de Contrato
19	Minuta de Ata de Registro de Preços
20	Ato que autoriza a Contratação Direta
21	Ata de Solicitações
22	Extrato de Contrato
23	Termo de Homologação e Adjudicação
24	Aviso de Inexigibilidade
25	Retificação de Edital
26	Termo de Credenciamento
27	Termo de Anulação
28	Inexigibilidade de Licitação
29	Ata de Sessão Pública
30	Retificação de Aviso de Licitação
31	Ata de Licitação Fracassada
32	Termo de Homologação
33	Termo de Ratificação
34	Termo de Formalização
35	Aviso de Dispensa
36	Dispensa de Licitação
37	Termo de Adjudicação
38	Aviso de Licitação
39	Processo SIG
\.


--
-- Data for Name: tipo_especificacao_ug; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tipo_especificacao_ug (id_tipo_especificacao_ug, descricao) FROM stdin;
1	Prefeitura Municipal
2	Câmara Municipal
3	Fundo Municipal de Saúde
4	Fundo Municipal de Assistência Social
5	Fundo Municipal da Infância e Adolescência/Criança e Adolescência
6	Fundo Municipal de Educação
7	Fundo/Fundação/Autarquia Municipal de Previdência
8	Fundo/Fundação/Autarquia de Assistência ao Servidor Municipal
9	Fundação/Autarquia Municipal Hospitalar
10	Fundo/Fundação/Autarquia Municipal de Cultura
11	Fundo Municipal de Agricultura/Desenvolvimento Rural/Agropecuário
12	Fundo/Fundação Municipal de Esportes/Desporto
13	Fundo/Fundação Municipal do Meio Ambiente
14	Fundação Municipal de Vigilância
15	Fundo/Fundação Municipal de Turismo
16	Fundo Municipal de Melhoria da Polícia Militar/Polícia Civil/Corpo de Bombeiros
17	Fundo Municipal de Habitação/Rotativo Habitacional
18	Fundo/Fundação/Autarquia Municipal de Saneamento/Água e Esgoto
19	Fundo/Fundação/Autarquia Municipal de Trânsito
20	Fundo/Fundação/Autarquia Municipal de Planejamento Urbano
21	Empresa Pública Municipal
22	Sociedade de Economia Mista Municipal
23	Outras Unidades que Não se Enquadrem em Nenhuma das Mencionadas Anteriormente
\.


--
-- Data for Name: tipo_licitacao; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tipo_licitacao (id_tipo_licitacao, descricao) FROM stdin;
3	Técnica e Preço
4	Maior Lance ou Oferta
8	Não se Aplica
9	Maior Oferta de Preço
10	Menor Valor da Tarifa
12	Menor Valor da Tarifa e Maior Oferta pela Outorga
13	Menor Valor da Tarifa e Melhor Oferta de Pagamento pela Outorga
14	Maior Oferta pela Outorga e Melhor Oferta de Pagamento
15	Melhor Proposta Técnica, com Preço Fixado no Edital
18	Melhor Oferta de Pagamento pela Outorga
19	Melhor Destinação de Bens Alienados
16	Melhor Proposta (Combinação Menor Valor da Tarifa com o de Melhor Técnica)
17	Melhor Proposta (Combinação de Maior Oferta pela Outorga com o de Melhor Técnica)
1	Menor Preço
5	Maior Desconto
2	Melhor Técnica
6	Melhor Conteúdo Artístico
7	Maior Retorno Econômico
11	Maior Oferta
20	Não Especificado
\.


--
-- Data for Name: tipo_objeto_licitacao; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tipo_objeto_licitacao (id_tipo_objeto_licitacao, descricao) FROM stdin;
1	Materiais e Serviços
2	Obras e Serviços de Engenharia
3	Concessões e Permissões
6	Outros
7	Aquisição de Bens
8	Contratação de Serviços
4	Alienação de Bens
5	Concessão e Permissão de Uso de Bem Público
\.


--
-- Data for Name: tipo_ug; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tipo_ug (id_tipo_ug, descricao) FROM stdin;
0	Administração Direta
1	Autarquia
2	Fundação
3	Fundo
4	Empresa
5	Tribunal de Justiça
6	Assembleia Legislativa
7	Ministério Público
8	Tribunal de Contas
9	Câmara de Vereadores
10	Empresa Estatal Dependente
11	Consórcio Público
12	Associação de Municípios
13	Outros Órgãos Federais
14	Unidade Central
15	Consolidada
\.


--
-- Data for Name: tipologia_alerta; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tipologia_alerta (id_tipologia_alerta, id_hipertipologia_alerta, nome, descricao) FROM stdin;
27	8	Sócio da empresa é familiar consanguíneo de primeiro grau de servidor público de órgão estadual	Sócio da empresa é familiar consanguíneo de primeiro grau de servidor público de órgão estadual
28	8	Sócio da empresa é familiar consanguíneo de primeiro grau de servidor público de órgão municipal	Sócio da empresa é familiar consanguíneo de primeiro grau de servidor público de órgão municipal
43	11	Sócio da empresa contratada por órgão público é sócio de outra empresa que possui como sócio político que já foi eleito para cargo eletivo no mesmo município da unidade gestora que celebrou o contrato	Sócio da empresa contratada por órgão público é sócio de outra empresa que possui como sócio político que já foi eleito para cargo eletivo no mesmo município da unidade gestora que celebrou o contrato
58	13	Sócio constante no BNMP	Sócio constante no BNMP
13	4	Empresa apresenta propostas idênticas acima de patamar definido	Empresa apresenta propostas idênticas acima de patamar definido
14	5	Sócio atualmente no quadro societário é beneficiário de bolsa família	Sócio atualmente no quadro societário é beneficiário de bolsa família
15	5	Sócio atualmente no quadro societário já foi beneficiário de bolsa família no passado	Sócio atualmente no quadro societário já foi beneficiário de bolsa família no passado
18	6	Sócio atualmente no quadro societário que é concomitantemente empregado de outra empresa recebendo até 1,5 salário mínimo	Sócio atualmente no quadro societário que é concomitantemente empregado de outra empresa recebendo até 1,5 salário mínimo
56	13	Sócio de empresa é pessoa já falecida	Sócio de empresa é pessoa já falecida
67	15	Empresa apresentou proposta antes da data de sua constituição	Empresa apresentou proposta antes da data de sua constituição
83	18	Licitação em modalidade competitiva em que a empresa foi a única licitante	Licitação em modalidade competitiva em que a empresa foi a única licitante
6	1	Empresas licitantes estão sediados no mesmo endereço	Empresas licitantes estão sediados no mesmo endereço
8	2	Empresa licitante é vencedora contumaz	Empresa licitante é vencedora contumaz
9	2	Empresa licitante é perdedora contumaz	Empresa licitante é perdedora contumaz
10	2	Empresa licitante é vencedora contra empresa perdedora contumaz	Empresa licitante é vencedora contra empresa perdedora contumaz
11	2	Alternância de vitórias entre empresas licitantes	Alternância de vitórias entre empresas licitantes
37	9	Sócio da empresa é fornecedor de campanha política	Sócio da empresa é fornecedor de campanha política
57	13	Sócio de empresa é pessoa que não consta na base de dados de pessoas físicas da RFB (risco de utilização de documento falso)	Sócio de empresa é pessoa que não consta na base de dados de pessoas físicas da RFB (risco de utilização de documento falso)
65	15	Data da constituição da empresa muito próxima da data de pagamento ou emissão NFe pelo órgão público	Data da constituição da empresa muito próxima da data de pagamento ou emissão NFe pelo órgão público
38	10	Sócio da empresa é familiar consanguíneo de primeiro grau de indivíduo que já foi eleito para cargo eletivo	Sócio da empresa é familiar consanguíneo de primeiro grau de indivíduo que já foi eleito para cargo eletivo
85	19	Empresa fez doação para campanha política	Empresa fez doação para campanha política
86	19	Empresa fornecedora de campanha política	Empresa fornecedora de campanha política
87	19	Empresa recebe ou recebeu emenda parlamentar	Empresa recebe ou recebeu emenda parlamentar
88	20	Empresa envolvida com o crime organizado	Empresa envolvida com o crime organizado
20	6	Sócio atualmente no quadro é concomitantemente empregado de outra empresa recebendo menos de 3 salários mínimos e mais de 1,5 salário mínimo	Sócio atualmente no quadro é concomitantemente empregado de outra empresa recebendo menos de 3 salários mínimos e mais de 1,5 salário mínimo
44	11	Sócio da empresa contratada por órgão público é sócio de outra empresa que possui como sócio político que já foi candidato (derrotado) em eleição para cargo eletivo	Sócio da empresa contratada por órgão público é sócio de outra empresa que possui como sócio político que já foi candidato (derrotado) em eleição para cargo eletivo
45	11	Sócio da empresa contratada por órgão público é sócio de outra empresa que possui como sócio político que já foi candidato (derrotado) no mesmo município da unidade gestora que celebrou o contrato em eleição para cargo eletivo	Sócio da empresa contratada por órgão público é sócio de outra empresa que possui como sócio político que já foi candidato (derrotado) no mesmo município da unidade gestora que celebrou o contrato em eleição para cargo eletivo
46	12	Sócio atual já foi ou é sócio de outra empresa punida com inscrição no CEIS/CGU	Sócio atual já foi ou é sócio de outra empresa punida com inscrição no CEIS/CGU
63	15	Data da constituição da empresa muito próxima da data da proposta com órgão público	Data da constituição da empresa muito próxima da data da proposta com órgão público
64	15	Data da constituição da empresa muito próxima da data do contrato com órgão público	Data da constituição da empresa muito próxima da data do contrato com órgão público
68	16	Empresa com até 10 CNAEs sendo ao menos dois de divisões diferentes (primeiros dois dígitos, os quais remetem a 21 setores econômicos distintos)	Empresa com até 10 CNAEs sendo ao menos dois de divisões diferentes (primeiros dois dígitos, os quais remetem a 21 setores econômicos distintos)
69	16	Empresa com mais de 10 CNAEs e menos de 21 CNAEs sendo dois de divisões diferentes (primeiros dois dígitos, os quais remetem a 21 setores econômicos distintos)	Empresa com mais de 10 CNAEs e menos de 21 CNAEs sendo dois de divisões diferentes (primeiros dois dígitos, os quais remetem a 21 setores econômicos distintos)
70	16	Empresa com mais de 10 CNAEs e menos de 21 CNAEs sendo três de divisões diferentes (primeiros dois dígitos, os quais remetem a 21 setores econômicos distintos)	Empresa com mais de 10 CNAEs e menos de 21 CNAEs sendo três de divisões diferentes (primeiros dois dígitos, os quais remetem a 21 setores econômicos distintos)
81	18	Majoração contratual por meio de aditivos incongruentes	Majoração contratual por meio de aditivos incongruentes
82	18	Taxa de vitórias em licitações incongruente	Taxa de vitórias em licitações incongruente
55	12	Sócio que já saiu da sociedade já foi ou é sócio de outra empresa punida com inscrição na lista suja de trabalho escravo/MTE	Sócio que já saiu da sociedade já foi ou é sócio de outra empresa punida com inscrição na lista suja de trabalho escravo/MTE
40	10	Sócio da empresa é familiar consanguíneo de primeiro grau de indivíduo que já foi candidato em eleição (derrotado)	Sócio da empresa é familiar consanguíneo de primeiro grau de indivíduo que já foi candidato em eleição (derrotado)
41	10	Sócio da empresa é familiar consanguíneo de primeiro grau de indivíduo que já foi candidato em eleição (derrotado) para cargo eletivo no mesmo município da unidade gestora que celebrou o contrato	Sócio da empresa é familiar consanguíneo de primeiro grau de indivíduo que já foi candidato em eleição (derrotado) para cargo eletivo no mesmo município da unidade gestora que celebrou o contrato
21	6	Sócio que já saiu da sociedade foi concomitantemente empregado de outra empresa recebendo menos de 3 salários mínimos e mais de 1,5 salário mínimo	Sócio que já saiu da sociedade foi concomitantemente empregado de outra empresa recebendo menos de 3 salários mínimos e mais de 1,5 salário mínimo
22	7	Sócio da empresa é servidor público em nível federal, estadual ou municipal	Sócio da empresa é servidor público em nível federal, estadual ou municipal
23	7	Sócio da empresa foi servidor público em nível federal, estadual ou municipal	Sócio da empresa foi servidor público em nível federal, estadual ou municipal
24	7	Sócio da empresa é servidor público trabalhando na mesma unidade gestora que celebrou o contrato	Sócio da empresa é servidor público trabalhando na mesma unidade gestora que celebrou o contrato
25	7	Sócio da empresa foi servidor público trabalhando na mesma unidade gestora que celebrou o contrato	Sócio da empresa foi servidor público trabalhando na mesma unidade gestora que celebrou o contrato
26	8	Sócio da empresa é familiar consanguíneo de primeiro grau de servidor público de órgão federal	Sócio da empresa é familiar consanguíneo de primeiro grau de servidor público de órgão federal
7	1	Empresas licitantes possem mesmo telefone, e-mail ou grupo econômico	Empresas licitantes possem mesmo telefone, e-mail ou grupo econômico
1	1	Empresa licitante com sócio em comum com outra empresa licitante	Empresa licitante com sócio em comum com outra empresa licitante
2	1	Empresa licitantes com ex-sócio em comum com outra empresa licitante	Empresa licitantes com ex-sócio em comum com outra empresa licitante
3	1	Familiares consanguíneos de primeiro grau em comum entre sócios de empresas licitantes	Familiares consanguíneos de primeiro grau em comum entre sócios de empresas licitantes
4	1	Sócio de uma empresa licitante é empregado de outra empresa licitante	Sócio de uma empresa licitante é empregado de outra empresa licitante
5	1	Empresas licitantes com contador em comum	Empresas licitantes com contador em comum
93	24	A licitação está sendo investigada com registro no SIG	A licitação está sendo investigada com registro no SIG
39	10	Sócio da empresa é familiar consanguíneo de primeiro grau de indivíduo que já foi eleito em eleição para cargo eletivo no mesmo município da unidade gestora que celebrou o contrato	Sócio da empresa é familiar consanguíneo de primeiro grau de indivíduo que já foi eleito em eleição para cargo eletivo no mesmo município da unidade gestora que celebrou o contrato
29	8	Sócio da empresa é familiar consanguíneo de primeiro grau de servidor público que trabalha no mesmo estado do órgão que celebrou o contrato	Sócio da empresa é familiar consanguíneo de primeiro grau de servidor público que trabalha no mesmo estado do órgão que celebrou o contrato
19	6	Sócio que já saiu da sociedade foi concomitantemente empregado de outra empresa recebendo até 1,5 salário mínimo	Sócio que já saiu da sociedade foi concomitantemente empregado de outra empresa recebendo até 1,5 salário mínimo
12	3	Empresa apresenta propostas simétricas acima de patamar definido	Empresa apresenta propostas simétricas acima de patamar definido
16	5	Sócio que já saiu da sociedade era beneficiário de bolsa família na época em que integrava o quadro societário	Sócio que já saiu da sociedade era beneficiário de bolsa família na época em que integrava o quadro societário
17	5	Sócio da empresa é familiar consanguíneo de primeiro grau de indivíduo beneficiário de bolsa família	Sócio da empresa é familiar consanguíneo de primeiro grau de indivíduo beneficiário de bolsa família
30	8	Sócio da empresa é familiar consanguíneo de primeiro grau de servidor público que trabalha no mesmo município do órgão que celebrou o contrato	Sócio da empresa é familiar consanguíneo de primeiro grau de servidor público que trabalha no mesmo município do órgão que celebrou o contrato
31	8	Sócio da empresa é familiar consanguíneo de primeiro grau de servidor público que trabalha na mesma unidade gestora que celebrou o contrato	Sócio da empresa é familiar consanguíneo de primeiro grau de servidor público que trabalha na mesma unidade gestora que celebrou o contrato
32	9	Sócio da empresa já foi eleito para cargo eletivo	Sócio da empresa já foi eleito para cargo eletivo
33	9	Sócio da empresa já foi eleito em eleição para cargo eletivo no mesmo município da unidade gestora que celebrou o contrato	Sócio da empresa já foi eleito em eleição para cargo eletivo no mesmo município da unidade gestora que celebrou o contrato
34	9	Sócio da empresa já foi candidato em eleição (derrotado)	Sócio da empresa já foi candidato em eleição (derrotado)
35	9	Sócio da empresa já foi candidato em eleição (derrotado) para cargo eletivo no mesmo município da unidade gestora que celebrou o contrato	Sócio da empresa já foi candidato em eleição (derrotado) para cargo eletivo no mesmo município da unidade gestora que celebrou o contrato
36	9	Sócio da empresa fez doação para campanha política	Sócio da empresa fez doação para campanha política
84	18	Licitação em modalidade convite vencida pela empresa em que menos de 3 participantes apresentaram propostas	Licitação em modalidade convite vencida pela empresa em que menos de 3 participantes apresentaram propostas
92	23	O município onde ocorre a licitação possui notícias de fraudes em licitações	O município onde ocorre a licitação possui notícias de fraudes em licitações
52	12	Sócio atual já foi ou é sócio de outra empresa punida com inscrição no CADICON	Sócio atual já foi ou é sócio de outra empresa punida com inscrição no CADICON
61	14	Empresa é ME ou EPP e recebeu valores em contratos públicos acima do limite do enquadramento de porte	Empresa é ME ou EPP e recebeu valores em contratos públicos acima do limite do enquadramento de porte
54	12	Sócio atual já foi ou é sócio de outra empresa punida com inscrição na lista suja de trabalho escravo/MTE	Sócio atual já foi ou é sócio de outra empresa punida com inscrição na lista suja de trabalho escravo/MTE
42	11	Sócio da empresa contratada por órgão público é sócio de outra empresa que possui como sócio político que já foi eleito para cargo eletivo	Sócio da empresa contratada por órgão público é sócio de outra empresa que possui como sócio político que já foi eleito para cargo eletivo
48	12	Sócio atual já foi ou é sócio de outra empresa punida com inscrição no CNCAI/CNJ	Sócio atual já foi ou é sócio de outra empresa punida com inscrição no CNCAI/CNJ
49	12	Sócio que já saiu da sociedade já foi ou é sócio de outra empresa punida com inscrição no CNCAI/CNJ	Sócio que já saiu da sociedade já foi ou é sócio de outra empresa punida com inscrição no CNCAI/CNJ
50	12	Sócio atual já foi ou é sócio de outra empresa punida com inscrição no CEPIM/CGU	Sócio atual já foi ou é sócio de outra empresa punida com inscrição no CEPIM/CGU
51	12	Sócio que já saiu da sociedade já foi ou é sócio de outra empresa punida com inscrição no CEPIM/CGU	Sócio que já saiu da sociedade já foi ou é sócio de outra empresa punida com inscrição no CEPIM/CGU
53	12	Sócio que já saiu da sociedade já foi ou é sócio de outra empresa punida com inscrição cadicon	Sócio que já saiu da sociedade já foi ou é sócio de outra empresa punida com inscrição CADICON
59	14	Número de funcionários da empresa não compatível com o valor total das licitações em que a empresa participa	Número de funcionários da empresa não compatível com o valor total das licitações em que a empresa participa
60	14	Capital social da empresa não compatível com o valor total das licitações em que a empresa participa	Capital social da empresa não compatível com o valor total das licitações em que a empresa participa
47	12	Sócio que já saiu da sociedade já foi ou é sócio de outra empresa punida com inscrição no CEIS/CGU  	Sócio que já saiu da sociedade já foi ou é sócio de outra empresa punida com inscrição no CEIS/CGU  
62	15	Data da constituição da empresa muito próxima da data de abertura do certame	Data da constituição da empresa muito próxima da data de abertura do certame
66	15	Empresa contratada antes da data de sua constituição	Empresa contratada antes da data de sua constituição
89	21	Diferença entre valor previsto e valor contratado acima do normal	Diferença entre valor previsto e valor contratado acima do normal
90	22	A licitação possui baixa competitividade	A licitação possui baixa competitividade
91	23	A licitação possui notícias de fraudes em licitações	A licitação possui notícias de fraudes em licitações
71	16	Empresa com mais de 10 CNAEs e menos de 21 CNAEs sendo ao menos quatro de divisões diferentes (primeiros dois dígitos, os quais remetem a 21 setores econômicos distintos)	Empresa com mais de 10 CNAEs e menos de 21 CNAEs sendo ao menos quatro de divisões diferentes (primeiros dois dígitos, os quais remetem a 21 setores econômicos distintos)
72	16	Empresa com mais de 21 CNAEs e menos de 35 CNAEs sendo dois de divisões diferentes (primeiros dois dígitos, os quais remetem a 21 setores econômicos distintos)	Empresa com mais de 21 CNAEs e menos de 35 CNAEs sendo dois de divisões diferentes (primeiros dois dígitos, os quais remetem a 21 setores econômicos distintos)
73	16	Empresa com mais de 21 CNAEs e menos de 35 CNAEs sendo três divisões diferentes (primeiros dois dígitos, os quais remetem a 21 setores econômicos distintos)	Empresa com mais de 21 CNAEs e menos de 35 CNAEs sendo três divisões diferentes (primeiros dois dígitos, os quais remetem a 21 setores econômicos distintos)
74	16	Empresa com mais de 21 CNAEs e menos de 35 CNAEs sendo ao menos quatro de divisões diferentes (primeiros dois dígitos, os quais remetem a 21 setores econômicos distintos)	Empresa com mais de 21 CNAEs e menos de 35 CNAEs sendo ao menos quatro de divisões diferentes (primeiros dois dígitos, os quais remetem a 21 setores econômicos distintos)
75	16	Empresa com mais de 10 CNAEs e menos de 35 CNAEs sendo ao menos quatro de divisões diferentes (primeiros dois dígitos, os quais remetem a 21 setores econômicos distintos)	Empresa com mais de 10 CNAEs e menos de 35 CNAEs sendo ao menos quatro de divisões diferentes (primeiros dois dígitos, os quais remetem a 21 setores econômicos distintos)
76	17	Empresa foi contratada com punição vigente de inscrição no CEIS/CGU	Empresa foi contratada com punição vigente de inscrição no CEIS/CGU
77	17	Empresa foi contratada com punição vigente de inscrição no CNCAI/CNJ	Empresa foi contratada com punição vigente de inscrição no CNCAI/CNJ
78	17	Empresa foi contratada com punição vigente de inscrição no CEPIM/CGU	Empresa foi contratada com punição vigente de inscrição no CEPIM/CGU
80	18	Contratações diretas incongruentes (licitante sendo recontratado pelo mesmo por uma ou várias vezes seguidas)	Contratações diretas incongruentes (licitante sendo recontratado pelo mesmo por uma ou várias vezes seguidas)
79	17	Empresa foi contratada com punição vigente de inscrição na lista suja de trabalho escravo/MTE	Empresa foi contratada com punição vigente de inscrição na lista suja de trabalho escravo/MTE
\.


--
-- Data for Name: unidade_gestora; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.unidade_gestora (id_unidade_gestora, nome_ug, cep, cnpj, id_ente, id_tipo_ug, id_tipo_especificacao_ug) FROM stdin;
\.


--
-- Data for Name: unidade_orcamentaria; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.unidade_orcamentaria (id_unidade_orcamentaria, nome_unidade_orcamentaria) FROM stdin;
1	Departamento da Pesca
2	Departamento de Agricultura
3	Secretaria de Administração e Finanças
4	Departamento Desenvolvimento Social
5	Departamento de Esportes
6	Departamento Economico
7	Departamento de Obras
9	Departamento de Turismo
10	Encargos Gerais
11	Fundo Municipal de Saude
12	Camara de Vereadores
13	Fundo Municipal de Habitação
14	Ensino Regular
15	Departamento do MEIo Ambiente
8	FIA
\.


--
-- Data for Name: usuario_alerta_ignorado; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.usuario_alerta_ignorado (cpf, id_alerta) FROM stdin;
\.


--
-- Data for Name: usuario_processo_licitatorio; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.usuario_processo_licitatorio (cpf, id_processo_licitatorio) FROM stdin;
\.


--
-- Name: log_user_id_seq; Type: SEQUENCE SET; Schema: audit; Owner: -
--

SELECT pg_catalog.setval('audit.log_user_id_seq', 1, false);


--
-- Name: alerta_id_alerta_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.alerta_id_alerta_seq', 19, true);


--
-- Name: analise_agente_id_analise_agente_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.analise_agente_id_analise_agente_seq', 1, false);


--
-- Name: banco_de_precos_id_banco_de_precos_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.banco_de_precos_id_banco_de_precos_seq', 1, false);


--
-- Name: classificacao_produto_servico_id_classificacao_produto_serv_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.classificacao_produto_servico_id_classificacao_produto_serv_seq', 1, false);


--
-- Name: cnae_id_cnae_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cnae_id_cnae_seq', 1359, true);


--
-- Name: contrato_id_contrato_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.contrato_id_contrato_seq', 1, false);


--
-- Name: convenio_id_convenio_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.convenio_id_convenio_seq', 1, false);


--
-- Name: cotacao_id_cotacao_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.cotacao_id_cotacao_seq', 1, false);


--
-- Name: documento_id_documento_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.documento_id_documento_seq', 23, true);


--
-- Name: empenho_id_empenho_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.empenho_id_empenho_seq', 1, false);


--
-- Name: ente_id_ente_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.ente_id_ente_seq', 1, false);


--
-- Name: estabelecimento_id_estabelecimento_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.estabelecimento_id_estabelecimento_seq', 1, false);


--
-- Name: estatistica_item_bp_id_estatistica_item_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.estatistica_item_bp_id_estatistica_item_seq', 1, false);


--
-- Name: execucao_metodo_id_execucao_metodo_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.execucao_metodo_id_execucao_metodo_seq', 19, true);


--
-- Name: grafico_bp_id_grafico_bp_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.grafico_bp_id_grafico_bp_seq', 1, false);


--
-- Name: grupo_bp_id_grupo_bp_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.grupo_bp_id_grupo_bp_seq', 1, false);


--
-- Name: hipertipologia_alerta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.hipertipologia_alerta_id_seq', 24, true);


--
-- Name: inidonea_id_inidonea_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.inidonea_id_inidonea_seq', 1, false);


--
-- Name: item_licitacao_id_item_licitacao_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.item_licitacao_id_item_licitacao_seq', 1, false);


--
-- Name: item_nfe_classificacao_produt_id_item_nfe_classificacao_pro_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.item_nfe_classificacao_produt_id_item_nfe_classificacao_pro_seq', 1, false);


--
-- Name: item_nfe_id_item_nfe_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.item_nfe_id_item_nfe_seq', 1, false);


--
-- Name: items_removidos_bp_id_items_removidos_bp_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.items_removidos_bp_id_items_removidos_bp_seq', 120, true);


--
-- Name: liquidacao_id_liquidacao_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.liquidacao_id_liquidacao_seq', 1, false);


--
-- Name: megatipologia_alerta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.megatipologia_alerta_id_seq', 4, true);


--
-- Name: metodo_analise_id_metodo_analise_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.metodo_analise_id_metodo_analise_seq', 8, true);


--
-- Name: metodo_de_agrupamento_bp_id_metodo_de_agrupamento_bp_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.metodo_de_agrupamento_bp_id_metodo_de_agrupamento_bp_seq', 1, true);


--
-- Name: movimentacao_empenho_id_movimentacao_empenho_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.movimentacao_empenho_id_movimentacao_empenho_seq', 1, false);


--
-- Name: municipio_id_municipio_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.municipio_id_municipio_seq', 1, false);


--
-- Name: nfe_id_nfe_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.nfe_id_nfe_seq', 1, false);


--
-- Name: noticia_id_noticia_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.noticia_id_noticia_seq', 1, true);


--
-- Name: noticia_municipio_id_noticia_municipio_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.noticia_municipio_id_noticia_municipio_seq', 1, false);


--
-- Name: objeto_analise_id_objeto_analise_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.objeto_analise_id_objeto_analise_seq', 20, true);


--
-- Name: pagamento_empenho_id_pagamento_empenho_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.pagamento_empenho_id_pagamento_empenho_seq', 1, false);


--
-- Name: pessoa_id_pessoa_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.pessoa_id_pessoa_seq', 100198883, true);


--
-- Name: pessoa_juridica_id_pessoa_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.pessoa_juridica_id_pessoa_seq', 1, false);


--
-- Name: processo_licitatorio_id_processo_licitatorio_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.processo_licitatorio_id_processo_licitatorio_seq', 1, false);


--
-- Name: situacao_cadastral_id_situacao_cadastral_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.situacao_cadastral_id_situacao_cadastral_seq', 1, false);


--
-- Name: tipo_documento_id_tipo_documento_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tipo_documento_id_tipo_documento_seq', 38, true);


--
-- Name: tipo_especificacao_ug_id_tipo_especificacao_ug_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tipo_especificacao_ug_id_tipo_especificacao_ug_seq', 1, false);


--
-- Name: tipo_licitacao_id_tipo_licitacao_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tipo_licitacao_id_tipo_licitacao_seq', 1, false);


--
-- Name: tipo_ug_id_tipo_ug_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tipo_ug_id_tipo_ug_seq', 1, false);


--
-- Name: tipologia_alerta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.tipologia_alerta_id_seq', 93, true);


--
-- Name: unidade_gestora_id_unidade_gestora_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.unidade_gestora_id_unidade_gestora_seq', 1, false);


--
-- Name: unidade_orcamentaria_id_unidade_orcamentaria_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.unidade_orcamentaria_id_unidade_orcamentaria_seq', 1, false);


--
-- Name: processo_licitatorio pk_processo_licitatorio; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processo_licitatorio
    ADD CONSTRAINT pk_processo_licitatorio PRIMARY KEY (id_processo_licitatorio);


--
-- Name: view_processo_licitatorio_filtro; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.view_processo_licitatorio_filtro AS
 SELECT min(pl.id_processo_licitatorio) AS id_procedimento_licitatorio,
    pl.numero_processo_licitatorio,
    pl.numero_edital,
    pl.descricao_objeto,
    NULL::text AS processos_sig,
    pl.valor_total_previsto,
    sum(c.valor_contrato) AS valor_contrato,
    (sum(c.valor_contrato) - pl.valor_total_previsto) AS diferenca,
    ml.descricao AS modalidade,
    tl.descricao AS tipo_licitacao,
    pl.situacao,
    et.ente,
    ug.nome_ug,
    pl.data_abertura_certame,
    max(c.data_vencimento) AS data_vencimento,
    COALESCE(( SELECT string_agg(DISTINCT (al.nivel)::text, ', '::text ORDER BY (al.nivel)::text) AS string_agg
           FROM (((public.objeto_analise obj
             JOIN public.execucao_metodo_objeto_analise da ON ((da.id_objeto_analise = obj.id_objeto_analise)))
             JOIN public.execucao_metodo em ON ((em.id_execucao_metodo = da.id_execucao_metodo)))
             JOIN public.alerta al ON ((em.id_execucao_metodo = al.id_execucao_metodo)))
          WHERE (obj.id_processo_licitatorio = pl.id_processo_licitatorio)), '0'::text) AS niveis_alerta,
    td.descricao AS tipo_documento,
    nfe.id_nfe
   FROM ((((((((public.processo_licitatorio pl
     LEFT JOIN public.contrato c ON ((c.id_processo_licitatorio = pl.id_processo_licitatorio)))
     LEFT JOIN public.modalidade_licitacao ml ON ((ml.id_modalidade_licitacao = pl.id_modalidade_licitacao)))
     LEFT JOIN public.tipo_licitacao tl ON ((tl.id_tipo_licitacao = pl.id_tipo_licitacao)))
     JOIN public.unidade_gestora ug ON ((ug.id_unidade_gestora = pl.id_unidade_gestora)))
     JOIN public.ente et ON ((ug.id_ente = et.id_ente)))
     LEFT JOIN public.documento d ON ((d.id_processo_licitatorio = pl.id_processo_licitatorio)))
     LEFT JOIN public.tipo_documento td ON ((td.id_tipo_documento = d.id_tipo_documento)))
     LEFT JOIN public.nfe nfe ON ((nfe.id_processo_licitatorio = pl.id_processo_licitatorio)))
  GROUP BY pl.id_processo_licitatorio, pl.numero_edital, pl.descricao_objeto, pl.valor_total_previsto, pl.data_abertura_certame, ml.descricao, tl.descricao, pl.situacao, et.ente, ug.nome_ug, td.descricao, nfe.id_nfe
  WITH NO DATA;


--
-- Name: log_user log_user_pkey; Type: CONSTRAINT; Schema: audit; Owner: -
--

ALTER TABLE ONLY audit.log_user
    ADD CONSTRAINT log_user_pkey PRIMARY KEY (id);


--
-- Name: users pk_users; Type: CONSTRAINT; Schema: audit; Owner: -
--

ALTER TABLE ONLY audit.users
    ADD CONSTRAINT pk_users PRIMARY KEY (cpf);


--
-- Name: hipertipologia_alerta hipertipologia_alerta_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hipertipologia_alerta
    ADD CONSTRAINT hipertipologia_alerta_pkey PRIMARY KEY (id_hipertipologia_alerta);


--
-- Name: items_removidos_bp items_removidos_bp_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.items_removidos_bp
    ADD CONSTRAINT items_removidos_bp_pkey PRIMARY KEY (id_items_removidos_bp);


--
-- Name: megatipologia_alerta megatipologia_alerta_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.megatipologia_alerta
    ADD CONSTRAINT megatipologia_alerta_pkey PRIMARY KEY (id_megatipologia_alerta);


--
-- Name: modalidade_licitacao modalidade_licitacao_new_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.modalidade_licitacao
    ADD CONSTRAINT modalidade_licitacao_new_pkey PRIMARY KEY (id_modalidade_licitacao);


--
-- Name: alerta pk_alerta; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerta
    ADD CONSTRAINT pk_alerta PRIMARY KEY (id_alerta);


--
-- Name: analise_agente pk_analise_agente; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analise_agente
    ADD CONSTRAINT pk_analise_agente PRIMARY KEY (id_analise_agente);


--
-- Name: banco_de_precos pk_banco_de_precos; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.banco_de_precos
    ADD CONSTRAINT pk_banco_de_precos PRIMARY KEY (id_banco_de_precos);


--
-- Name: classificacao_produto_servico pk_classificacao_produto_servico; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classificacao_produto_servico
    ADD CONSTRAINT pk_classificacao_produto_servico PRIMARY KEY (id_classificacao_produto_servico);


--
-- Name: cnae pk_cnae_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cnae
    ADD CONSTRAINT pk_cnae_pkey PRIMARY KEY (id_cnae);


--
-- Name: contrato pk_contrato; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato
    ADD CONSTRAINT pk_contrato PRIMARY KEY (id_contrato);


--
-- Name: convenio pk_convenio; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.convenio
    ADD CONSTRAINT pk_convenio PRIMARY KEY (id_convenio);


--
-- Name: convenio_ente pk_convenio_ente; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.convenio_ente
    ADD CONSTRAINT pk_convenio_ente PRIMARY KEY (id_convenio, id_ente);


--
-- Name: cotacao pk_cotacao; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cotacao
    ADD CONSTRAINT pk_cotacao PRIMARY KEY (id_cotacao);


--
-- Name: cotacao_contrato pk_cotacao_contrato; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cotacao_contrato
    ADD CONSTRAINT pk_cotacao_contrato PRIMARY KEY (id_cotacao, id_contrato);


--
-- Name: documento pk_documento; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento
    ADD CONSTRAINT pk_documento PRIMARY KEY (id_documento);


--
-- Name: empenho pk_empenho; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empenho
    ADD CONSTRAINT pk_empenho PRIMARY KEY (id_empenho);


--
-- Name: ente pk_ente; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ente
    ADD CONSTRAINT pk_ente PRIMARY KEY (id_ente);


--
-- Name: estabelecimento pk_estabelecimento; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estabelecimento
    ADD CONSTRAINT pk_estabelecimento PRIMARY KEY (id_estabelecimento);


--
-- Name: estabelecimento_cnae_secundario pk_estabelecimento_cnae_secundario; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estabelecimento_cnae_secundario
    ADD CONSTRAINT pk_estabelecimento_cnae_secundario PRIMARY KEY (id_estabelecimento, cnae);


--
-- Name: estatistica_item_bp pk_estatistica_item_bp; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estatistica_item_bp
    ADD CONSTRAINT pk_estatistica_item_bp PRIMARY KEY (id_estatistica_item);


--
-- Name: execucao_metodo pk_execucao_metodo; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.execucao_metodo
    ADD CONSTRAINT pk_execucao_metodo PRIMARY KEY (id_execucao_metodo);


--
-- Name: execucao_metodo_objeto_analise pk_execucao_metodo_objeto_analise; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.execucao_metodo_objeto_analise
    ADD CONSTRAINT pk_execucao_metodo_objeto_analise PRIMARY KEY (id_execucao_metodo, id_objeto_analise);


--
-- Name: grafico_bp pk_grafico_bp; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.grafico_bp
    ADD CONSTRAINT pk_grafico_bp PRIMARY KEY (id_grafico_bp);


--
-- Name: grupo_bp pk_grupo_bp; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.grupo_bp
    ADD CONSTRAINT pk_grupo_bp PRIMARY KEY (id_grupo_bp);


--
-- Name: inidonea pk_inidonea; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inidonea
    ADD CONSTRAINT pk_inidonea PRIMARY KEY (id_inidonea);


--
-- Name: item_licitacao pk_item_licitacao; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_licitacao
    ADD CONSTRAINT pk_item_licitacao PRIMARY KEY (id_item_licitacao);


--
-- Name: item_nfe pk_item_nfe; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_nfe
    ADD CONSTRAINT pk_item_nfe PRIMARY KEY (id_item_nfe);


--
-- Name: item_nfe_classificacao_produto_servico pk_item_nfe_classificacao_produto_servico; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_nfe_classificacao_produto_servico
    ADD CONSTRAINT pk_item_nfe_classificacao_produto_servico PRIMARY KEY (id_item_nfe_classificacao_produto_servico);


--
-- Name: item_nfe_grupo_bp pk_item_nfe_grupo_bp; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_nfe_grupo_bp
    ADD CONSTRAINT pk_item_nfe_grupo_bp PRIMARY KEY (id_grupo_bp, id_item_nfe);


--
-- Name: liquidacao pk_liquidacao; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidacao
    ADD CONSTRAINT pk_liquidacao PRIMARY KEY (id_liquidacao);


--
-- Name: metodo_analise pk_metodo_analise; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metodo_analise
    ADD CONSTRAINT pk_metodo_analise PRIMARY KEY (id_metodo_analise);


--
-- Name: metodo_de_agrupamento_bp pk_metodo_de_agrupamento_bp; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metodo_de_agrupamento_bp
    ADD CONSTRAINT pk_metodo_de_agrupamento_bp PRIMARY KEY (id_metodo_de_agrupamento_bp);


--
-- Name: motivo_situacao_cadastral pk_motivo_situacao_cadastral; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.motivo_situacao_cadastral
    ADD CONSTRAINT pk_motivo_situacao_cadastral PRIMARY KEY (id_motivo_situacao_cadastral);


--
-- Name: movimentacao_empenho pk_movimentacao_empenho; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimentacao_empenho
    ADD CONSTRAINT pk_movimentacao_empenho PRIMARY KEY (id_movimentacao_empenho);


--
-- Name: municipio pk_municipio; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.municipio
    ADD CONSTRAINT pk_municipio PRIMARY KEY (id_municipio);


--
-- Name: natureza_juridica pk_natureza_juridica; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.natureza_juridica
    ADD CONSTRAINT pk_natureza_juridica PRIMARY KEY (id_natureza_juridica);


--
-- Name: nfe pk_nfe; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nfe
    ADD CONSTRAINT pk_nfe PRIMARY KEY (id_nfe);


--
-- Name: noticia pk_noticia; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.noticia
    ADD CONSTRAINT pk_noticia PRIMARY KEY (id_noticia);


--
-- Name: noticia_municipio pk_noticia_municipio; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.noticia_municipio
    ADD CONSTRAINT pk_noticia_municipio PRIMARY KEY (id_noticia_municipio);


--
-- Name: objeto_analise pk_objeto_analise; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.objeto_analise
    ADD CONSTRAINT pk_objeto_analise PRIMARY KEY (id_objeto_analise);


--
-- Name: pagamento_empenho pk_pagamento_empenho; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pagamento_empenho
    ADD CONSTRAINT pk_pagamento_empenho PRIMARY KEY (id_pagamento_empenho);


--
-- Name: pessoa pk_pessoa; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pessoa
    ADD CONSTRAINT pk_pessoa PRIMARY KEY (id_pessoa);


--
-- Name: pessoa_fisica pk_pessoa_fisica; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pessoa_fisica
    ADD CONSTRAINT pk_pessoa_fisica PRIMARY KEY (cpf);


--
-- Name: pessoa_juridica pk_pessoa_juridica; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pessoa_juridica
    ADD CONSTRAINT pk_pessoa_juridica PRIMARY KEY (cnpj);


--
-- Name: pessoa_pessoa_juridica pk_pessoa_pessoa_juridica; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pessoa_pessoa_juridica
    ADD CONSTRAINT pk_pessoa_pessoa_juridica PRIMARY KEY (id_pessoa, cnpj);


--
-- Name: situacao_cadastral pk_situacao_cadastral; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.situacao_cadastral
    ADD CONSTRAINT pk_situacao_cadastral PRIMARY KEY (id_situacao_cadastral);


--
-- Name: tipo_cotacao pk_tipo_cotacao; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_cotacao
    ADD CONSTRAINT pk_tipo_cotacao PRIMARY KEY (id_tipo_cotacao);


--
-- Name: tipo_documento pk_tipo_documento; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_documento
    ADD CONSTRAINT pk_tipo_documento PRIMARY KEY (id_tipo_documento);


--
-- Name: tipo_especificacao_ug pk_tipo_especificacao_ug; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_especificacao_ug
    ADD CONSTRAINT pk_tipo_especificacao_ug PRIMARY KEY (id_tipo_especificacao_ug);


--
-- Name: tipo_licitacao pk_tipo_licitacao; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_licitacao
    ADD CONSTRAINT pk_tipo_licitacao PRIMARY KEY (id_tipo_licitacao);


--
-- Name: tipo_objeto_licitacao pk_tipo_objeto_licitacao; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_objeto_licitacao
    ADD CONSTRAINT pk_tipo_objeto_licitacao PRIMARY KEY (id_tipo_objeto_licitacao);


--
-- Name: tipo_ug pk_tipo_ug; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_ug
    ADD CONSTRAINT pk_tipo_ug PRIMARY KEY (id_tipo_ug);


--
-- Name: unidade_gestora pk_unidade_gestora; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.unidade_gestora
    ADD CONSTRAINT pk_unidade_gestora PRIMARY KEY (id_unidade_gestora);


--
-- Name: unidade_orcamentaria pk_unidade_orcamentaria; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.unidade_orcamentaria
    ADD CONSTRAINT pk_unidade_orcamentaria PRIMARY KEY (id_unidade_orcamentaria);


--
-- Name: usuario_alerta_ignorado pk_usuario_alerta_ignorado; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_alerta_ignorado
    ADD CONSTRAINT pk_usuario_alerta_ignorado PRIMARY KEY (cpf, id_alerta);


--
-- Name: usuario_processo_licitatorio pk_usuario_processo_licitatorio; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_processo_licitatorio
    ADD CONSTRAINT pk_usuario_processo_licitatorio PRIMARY KEY (cpf, id_processo_licitatorio);


--
-- Name: sig_documento sig_documento_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sig_documento
    ADD CONSTRAINT sig_documento_pkey PRIMARY KEY (id_documento);


--
-- Name: sig sig_numero_processo_sig_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sig
    ADD CONSTRAINT sig_numero_processo_sig_key UNIQUE (numero_processo_sig);


--
-- Name: sig sig_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sig
    ADD CONSTRAINT sig_pkey PRIMARY KEY (id_sig);


--
-- Name: sig_processo_licitatorio sig_processo_licitatorio_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sig_processo_licitatorio
    ADD CONSTRAINT sig_processo_licitatorio_pkey PRIMARY KEY (id_sig, id_processo_licitatorio);


--
-- Name: tipologia_alerta tipologia_alerta_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipologia_alerta
    ADD CONSTRAINT tipologia_alerta_pkey PRIMARY KEY (id_tipologia_alerta);


--
-- Name: cnae uq_cnae; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cnae
    ADD CONSTRAINT uq_cnae UNIQUE (cnae);


--
-- Name: idx_cnpj_estabelecimento; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cnpj_estabelecimento ON public.estabelecimento USING btree (cnpj);


--
-- Name: idx_estabelecimento_cnpj; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_estabelecimento_cnpj ON public.estabelecimento USING btree (cnpj);


--
-- Name: idx_estabelecimento_id_municipio_null; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_estabelecimento_id_municipio_null ON public.estabelecimento USING btree (id_municipio) WHERE (id_municipio IS NULL);


--
-- Name: idx_estabelecimento_motivo_situcao_cadastral; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_estabelecimento_motivo_situcao_cadastral ON public.estabelecimento USING btree (id_motivo_situacao_cadastral);


--
-- Name: idx_unique_remocao_banco_preco; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_unique_remocao_banco_preco ON public.items_removidos_bp USING btree (id_pessoa, id_grupo_bp, id_banco_de_precos) WHERE (id_nfe IS NULL);


--
-- Name: idx_unique_remocao_nfe; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_unique_remocao_nfe ON public.items_removidos_bp USING btree (id_pessoa, id_grupo_bp, id_nfe) WHERE (id_banco_de_precos IS NULL);


--
-- Name: municipio trava_total_municipio; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trava_total_municipio BEFORE INSERT OR DELETE OR UPDATE OR TRUNCATE ON public.municipio FOR EACH STATEMENT EXECUTE FUNCTION public.impedir_alteracao();


--
-- Name: log_user log_user_cpf_user_fkey; Type: FK CONSTRAINT; Schema: audit; Owner: -
--

ALTER TABLE ONLY audit.log_user
    ADD CONSTRAINT log_user_cpf_user_fkey FOREIGN KEY (cpf_user) REFERENCES audit.users(cpf);


--
-- Name: execucao_metodo_objeto_analise fk__objeto_analise_execucao_metodo_objeto_analise; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.execucao_metodo_objeto_analise
    ADD CONSTRAINT fk__objeto_analise_execucao_metodo_objeto_analise FOREIGN KEY (id_objeto_analise) REFERENCES public.objeto_analise(id_objeto_analise);


--
-- Name: banco_de_precos fk_alerta_banco_de_precos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.banco_de_precos
    ADD CONSTRAINT fk_alerta_banco_de_precos FOREIGN KEY (id_alerta) REFERENCES public.alerta(id_alerta);


--
-- Name: usuario_alerta_ignorado fk_alerta_usuario_alerta_ignorado; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_alerta_ignorado
    ADD CONSTRAINT fk_alerta_usuario_alerta_ignorado FOREIGN KEY (id_alerta) REFERENCES public.alerta(id_alerta);


--
-- Name: estatistica_item_bp fk_banco_de_precos_estatistica_item_bp; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estatistica_item_bp
    ADD CONSTRAINT fk_banco_de_precos_estatistica_item_bp FOREIGN KEY (id_banco_de_precos) REFERENCES public.banco_de_precos(id_banco_de_precos);


--
-- Name: grafico_bp fk_banco_de_precos_grafico_bp; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.grafico_bp
    ADD CONSTRAINT fk_banco_de_precos_grafico_bp FOREIGN KEY (id_banco_de_precos) REFERENCES public.banco_de_precos(id_banco_de_precos);


--
-- Name: classificacao_produto_servico fk_classificacao_produto_servico_classificacao_produto_servico; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classificacao_produto_servico
    ADD CONSTRAINT fk_classificacao_produto_servico_classificacao_produto_servico FOREIGN KEY (id_classificacao_produto_servico_pai) REFERENCES public.classificacao_produto_servico(id_classificacao_produto_servico);


--
-- Name: item_nfe_classificacao_produto_servico fk_classificacao_produto_servico_item_nfe_classificacao_produto; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_nfe_classificacao_produto_servico
    ADD CONSTRAINT fk_classificacao_produto_servico_item_nfe_classificacao_produto FOREIGN KEY (id_classificacao_produto_servico) REFERENCES public.classificacao_produto_servico(id_classificacao_produto_servico);


--
-- Name: metodo_de_agrupamento_bp fk_classificacao_produto_servico_metodo_de_agrupamento_bp; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metodo_de_agrupamento_bp
    ADD CONSTRAINT fk_classificacao_produto_servico_metodo_de_agrupamento_bp FOREIGN KEY (id_classificacao_produto_servico) REFERENCES public.classificacao_produto_servico(id_classificacao_produto_servico);


--
-- Name: estabelecimento fk_cnae_estabelecimento; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estabelecimento
    ADD CONSTRAINT fk_cnae_estabelecimento FOREIGN KEY (cnae_principal) REFERENCES public.cnae(cnae);


--
-- Name: estabelecimento_cnae_secundario fk_cnae_estabelecimento_cnae_secundario; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estabelecimento_cnae_secundario
    ADD CONSTRAINT fk_cnae_estabelecimento_cnae_secundario FOREIGN KEY (cnae) REFERENCES public.cnae(cnae);


--
-- Name: nfe fk_cnae_nfe; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nfe
    ADD CONSTRAINT fk_cnae_nfe FOREIGN KEY (cnae_emitente) REFERENCES public.cnae(cnae);


--
-- Name: cotacao_contrato fk_contrato_cotacao_contrato; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cotacao_contrato
    ADD CONSTRAINT fk_contrato_cotacao_contrato FOREIGN KEY (id_contrato) REFERENCES public.contrato(id_contrato);


--
-- Name: contrato fk_contrato_superior_contrato; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato
    ADD CONSTRAINT fk_contrato_superior_contrato FOREIGN KEY (id_contrato_superior) REFERENCES public.contrato(id_contrato);


--
-- Name: convenio_ente fk_convenio_convenio_ente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.convenio_ente
    ADD CONSTRAINT fk_convenio_convenio_ente FOREIGN KEY (id_convenio) REFERENCES public.convenio(id_convenio);


--
-- Name: participante_convenio fk_convenio_participante_convenio; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.participante_convenio
    ADD CONSTRAINT fk_convenio_participante_convenio FOREIGN KEY (id_convenio) REFERENCES public.convenio(id_convenio);


--
-- Name: cotacao_contrato fk_cotacao_cotacao_contrato; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cotacao_contrato
    ADD CONSTRAINT fk_cotacao_cotacao_contrato FOREIGN KEY (id_cotacao) REFERENCES public.cotacao(id_cotacao);


--
-- Name: objeto_analise fk_documento_objeto_analise; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.objeto_analise
    ADD CONSTRAINT fk_documento_objeto_analise FOREIGN KEY (id_documento) REFERENCES public.documento(id_documento);


--
-- Name: liquidacao fk_empenho_liquidacao; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidacao
    ADD CONSTRAINT fk_empenho_liquidacao FOREIGN KEY (id_empenho) REFERENCES public.empenho(id_empenho);


--
-- Name: movimentacao_empenho fk_empenho_movimentacao_empenho; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimentacao_empenho
    ADD CONSTRAINT fk_empenho_movimentacao_empenho FOREIGN KEY (id_empenho) REFERENCES public.empenho(id_empenho);


--
-- Name: empenho fk_empenho_superior; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empenho
    ADD CONSTRAINT fk_empenho_superior FOREIGN KEY (id_empenho_superior) REFERENCES public.empenho(id_empenho);


--
-- Name: convenio_ente fk_ente_convenio_ente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.convenio_ente
    ADD CONSTRAINT fk_ente_convenio_ente FOREIGN KEY (id_ente) REFERENCES public.ente(id_ente);


--
-- Name: objeto_analise fk_ente_fonte_alerta; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.objeto_analise
    ADD CONSTRAINT fk_ente_fonte_alerta FOREIGN KEY (id_ente) REFERENCES public.ente(id_ente);


--
-- Name: unidade_gestora fk_ente_unidade_gestora; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.unidade_gestora
    ADD CONSTRAINT fk_ente_unidade_gestora FOREIGN KEY (id_ente) REFERENCES public.ente(id_ente);


--
-- Name: alerta fk_execucao_metodo_alerta; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerta
    ADD CONSTRAINT fk_execucao_metodo_alerta FOREIGN KEY (id_execucao_metodo) REFERENCES public.execucao_metodo(id_execucao_metodo);


--
-- Name: execucao_metodo_objeto_analise fk_execucao_metodo_execucao_metodo_objeto_analise; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.execucao_metodo_objeto_analise
    ADD CONSTRAINT fk_execucao_metodo_execucao_metodo_objeto_analise FOREIGN KEY (id_execucao_metodo) REFERENCES public.execucao_metodo(id_execucao_metodo);


--
-- Name: banco_de_precos fk_grupo_bp_banco_de_precos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.banco_de_precos
    ADD CONSTRAINT fk_grupo_bp_banco_de_precos FOREIGN KEY (id_grupo_bp) REFERENCES public.grupo_bp(id_grupo_bp);


--
-- Name: item_nfe_grupo_bp fk_grupo_bp_item_nfe_grupo_bp; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_nfe_grupo_bp
    ADD CONSTRAINT fk_grupo_bp_item_nfe_grupo_bp FOREIGN KEY (id_grupo_bp) REFERENCES public.grupo_bp(id_grupo_bp);


--
-- Name: hipertipologia_alerta fk_hipertipologia_megatipologia; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hipertipologia_alerta
    ADD CONSTRAINT fk_hipertipologia_megatipologia FOREIGN KEY (id_megatipologia_alerta) REFERENCES public.megatipologia_alerta(id_megatipologia_alerta);


--
-- Name: documento fk_id_tipo_documento_documento; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento
    ADD CONSTRAINT fk_id_tipo_documento_documento FOREIGN KEY (id_tipo_documento) REFERENCES public.tipo_documento(id_tipo_documento);


--
-- Name: cotacao fk_item_licitacao_cotacao; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cotacao
    ADD CONSTRAINT fk_item_licitacao_cotacao FOREIGN KEY (id_item_licitacao) REFERENCES public.item_licitacao(id_item_licitacao);


--
-- Name: item_nfe fk_item_licitacao_item_nfe; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_nfe
    ADD CONSTRAINT fk_item_licitacao_item_nfe FOREIGN KEY (id_item_licitacao) REFERENCES public.item_licitacao(id_item_licitacao);


--
-- Name: objeto_analise fk_item_licitacao_objeto_analise; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.objeto_analise
    ADD CONSTRAINT fk_item_licitacao_objeto_analise FOREIGN KEY (id_item_licitacao) REFERENCES public.item_licitacao(id_item_licitacao);


--
-- Name: banco_de_precos fk_item_nfe_banco_de_precos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.banco_de_precos
    ADD CONSTRAINT fk_item_nfe_banco_de_precos FOREIGN KEY (id_item_nfe) REFERENCES public.item_nfe(id_item_nfe);


--
-- Name: item_nfe_classificacao_produto_servico fk_item_nfe_item_nfe_classificacao_produto_servico; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_nfe_classificacao_produto_servico
    ADD CONSTRAINT fk_item_nfe_item_nfe_classificacao_produto_servico FOREIGN KEY (id_item_nfe) REFERENCES public.item_nfe(id_item_nfe);


--
-- Name: item_nfe_grupo_bp fk_item_nfe_item_nfe_grupo_bp; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_nfe_grupo_bp
    ADD CONSTRAINT fk_item_nfe_item_nfe_grupo_bp FOREIGN KEY (id_item_nfe) REFERENCES public.item_nfe(id_item_nfe);


--
-- Name: objeto_analise fk_item_nfe_objeto_analise; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.objeto_analise
    ADD CONSTRAINT fk_item_nfe_objeto_analise FOREIGN KEY (id_item_nfe) REFERENCES public.item_nfe(id_item_nfe);


--
-- Name: pagamento_empenho fk_liquidacao_pagamento_empenho; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pagamento_empenho
    ADD CONSTRAINT fk_liquidacao_pagamento_empenho FOREIGN KEY (id_liquidacao) REFERENCES public.liquidacao(id_liquidacao);


--
-- Name: pagamento_empenho fk_empenho_pagamento_empenho; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pagamento_empenho
    ADD CONSTRAINT fk_empenho_pagamento_empenho FOREIGN KEY (id_empenho) REFERENCES public.empenho(id_empenho);


--
-- Name: execucao_metodo fk_metodo_analise_execucao_metodo; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.execucao_metodo
    ADD CONSTRAINT fk_metodo_analise_execucao_metodo FOREIGN KEY (id_metodo_analise) REFERENCES public.metodo_analise(id_metodo_analise);


--
-- Name: grupo_bp fk_metodo_de_agrupamento_bp_grupo_bp; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.grupo_bp
    ADD CONSTRAINT fk_metodo_de_agrupamento_bp_grupo_bp FOREIGN KEY (id_metodo_de_agrupamento_bp) REFERENCES public.metodo_de_agrupamento_bp(id_metodo_de_agrupamento_bp);


--
-- Name: metodo_analise fk_metodoanalise_tipologia; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metodo_analise
    ADD CONSTRAINT fk_metodoanalise_tipologia FOREIGN KEY (id_tipologia_alerta) REFERENCES public.tipologia_alerta(id_tipologia_alerta);


--
-- Name: noticia fk_modalidade_licitacao_noticia; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.noticia
    ADD CONSTRAINT fk_modalidade_licitacao_noticia FOREIGN KEY (id_modalidade_licitacao) REFERENCES public.modalidade_licitacao(id_modalidade_licitacao);


--
-- Name: processo_licitatorio fk_modalidade_licitacao_processo_licitatorio; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processo_licitatorio
    ADD CONSTRAINT fk_modalidade_licitacao_processo_licitatorio FOREIGN KEY (id_modalidade_licitacao) REFERENCES public.modalidade_licitacao(id_modalidade_licitacao);


--
-- Name: estabelecimento fk_motivo_situacao_cadastral_estabelecimento; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estabelecimento
    ADD CONSTRAINT fk_motivo_situacao_cadastral_estabelecimento FOREIGN KEY (id_motivo_situacao_cadastral) REFERENCES public.motivo_situacao_cadastral(id_motivo_situacao_cadastral);


--
-- Name: ente fk_municipio_ente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ente
    ADD CONSTRAINT fk_municipio_ente FOREIGN KEY (id_municipio) REFERENCES public.municipio(id_municipio);


--
-- Name: estabelecimento fk_municipio_estabelecimento; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estabelecimento
    ADD CONSTRAINT fk_municipio_estabelecimento FOREIGN KEY (id_municipio) REFERENCES public.municipio(id_municipio);


--
-- Name: noticia_municipio fk_municipio_noticia_municipio; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.noticia_municipio
    ADD CONSTRAINT fk_municipio_noticia_municipio FOREIGN KEY (id_municipio) REFERENCES public.municipio(id_municipio);


--
-- Name: pessoa_municipio fk_municipio_pessoa_municipio; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pessoa_municipio
    ADD CONSTRAINT fk_municipio_pessoa_municipio FOREIGN KEY (id_municipio) REFERENCES public.municipio(id_municipio);


--
-- Name: pessoa_juridica fk_natureza_juridica_pessoa_juridica; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pessoa_juridica
    ADD CONSTRAINT fk_natureza_juridica_pessoa_juridica FOREIGN KEY (id_natureza_juridica) REFERENCES public.natureza_juridica(id_natureza_juridica);


--
-- Name: item_nfe fk_nfe_item_nfe; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_nfe
    ADD CONSTRAINT fk_nfe_item_nfe FOREIGN KEY (id_nfe) REFERENCES public.nfe(id_nfe);


--
-- Name: pessoa_fisica_nfe fk_nfe_pessoa_fisica_nfe; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pessoa_fisica_nfe
    ADD CONSTRAINT fk_nfe_pessoa_fisica_nfe FOREIGN KEY (id_nfe) REFERENCES public.nfe(id_nfe);


--
-- Name: noticia_municipio fk_noticia_noticia_municipio; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.noticia_municipio
    ADD CONSTRAINT fk_noticia_noticia_municipio FOREIGN KEY (id_noticia) REFERENCES public.noticia(id_noticia);


--
-- Name: nfe fk_pagamento_empenho_nfe; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nfe
    ADD CONSTRAINT fk_pagamento_empenho_nfe FOREIGN KEY (id_pagamento_empenho) REFERENCES public.pagamento_empenho(id_pagamento_empenho);


--
-- Name: cotacao fk_pessoa_cotacao; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cotacao
    ADD CONSTRAINT fk_pessoa_cotacao FOREIGN KEY (id_pessoa) REFERENCES public.pessoa(id_pessoa);


--
-- Name: empenho fk_pessoa_empenho; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empenho
    ADD CONSTRAINT fk_pessoa_empenho FOREIGN KEY (id_pessoa) REFERENCES public.pessoa(id_pessoa);


--
-- Name: pessoa_fisica_estabelecimento fk_pessoa_fisica_pessoa_fisica_estabelecimento; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pessoa_fisica_estabelecimento
    ADD CONSTRAINT fk_pessoa_fisica_pessoa_fisica_estabelecimento FOREIGN KEY (cpf) REFERENCES public.pessoa_fisica(cpf);


--
-- Name: pessoa_fisica_nfe fk_pessoa_fisica_pessoa_fisica_nfe; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pessoa_fisica_nfe
    ADD CONSTRAINT fk_pessoa_fisica_pessoa_fisica_nfe FOREIGN KEY (cpf) REFERENCES public.pessoa_fisica(cpf);


--
-- Name: inidonea fk_pessoa_inidonea; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inidonea
    ADD CONSTRAINT fk_pessoa_inidonea FOREIGN KEY (id_pessoa) REFERENCES public.pessoa(id_pessoa);


--
-- Name: estabelecimento fk_pessoa_juridica_estabelecimento; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.estabelecimento
    ADD CONSTRAINT fk_pessoa_juridica_estabelecimento FOREIGN KEY (cnpj) REFERENCES public.pessoa_juridica(cnpj);


--
-- Name: pessoa_pessoa_juridica fk_pessoa_juridica_pessoa_pessoa_juridica; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pessoa_pessoa_juridica
    ADD CONSTRAINT fk_pessoa_juridica_pessoa_pessoa_juridica FOREIGN KEY (cnpj) REFERENCES public.pessoa_juridica(cnpj);


--
-- Name: liquidacao fk_pessoa_liquidacao; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidacao
    ADD CONSTRAINT fk_pessoa_liquidacao FOREIGN KEY (id_pessoa) REFERENCES public.pessoa(id_pessoa);


--
-- Name: objeto_analise fk_pessoa_objeto_analise; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.objeto_analise
    ADD CONSTRAINT fk_pessoa_objeto_analise FOREIGN KEY (id_pessoa) REFERENCES public.pessoa(id_pessoa);


--
-- Name: participante_convenio fk_pessoa_participante_convenio; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.participante_convenio
    ADD CONSTRAINT fk_pessoa_participante_convenio FOREIGN KEY (id_pessoa) REFERENCES public.pessoa(id_pessoa);


--
-- Name: pessoa_fisica fk_pessoa_pessoa_fisica; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pessoa_fisica
    ADD CONSTRAINT fk_pessoa_pessoa_fisica FOREIGN KEY (id_pessoa) REFERENCES public.pessoa(id_pessoa);


--
-- Name: pessoa_juridica fk_pessoa_pessoa_juridica; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pessoa_juridica
    ADD CONSTRAINT fk_pessoa_pessoa_juridica FOREIGN KEY (id_pessoa) REFERENCES public.pessoa(id_pessoa);


--
-- Name: pessoa_municipio fk_pessoa_pessoa_municipio; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pessoa_municipio
    ADD CONSTRAINT fk_pessoa_pessoa_municipio FOREIGN KEY (id_pessoa) REFERENCES public.pessoa(id_pessoa);


--
-- Name: pessoa_pessoa_juridica fk_pessoa_pessoa_pessoa_juridica; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pessoa_pessoa_juridica
    ADD CONSTRAINT fk_pessoa_pessoa_pessoa_juridica FOREIGN KEY (id_pessoa) REFERENCES public.pessoa(id_pessoa);


--
-- Name: processo_licitatorio_pessoa fk_pessoa_processo_licitatorio_pessoa; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processo_licitatorio_pessoa
    ADD CONSTRAINT fk_pessoa_processo_licitatorio_pessoa FOREIGN KEY (id_pessoa) REFERENCES public.pessoa(id_pessoa);


--
-- Name: analise_agente fk_processo_licitatorio_analise_agente; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analise_agente
    ADD CONSTRAINT fk_processo_licitatorio_analise_agente FOREIGN KEY (id_processo_licitatorio) REFERENCES public.processo_licitatorio(id_processo_licitatorio);


--
-- Name: banco_de_precos fk_processo_licitatorio_banco_de_precos; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.banco_de_precos
    ADD CONSTRAINT fk_processo_licitatorio_banco_de_precos FOREIGN KEY (id_processo_licitatorio) REFERENCES public.processo_licitatorio(id_processo_licitatorio);


--
-- Name: contrato fk_processo_licitatorio_contrato; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contrato
    ADD CONSTRAINT fk_processo_licitatorio_contrato FOREIGN KEY (id_processo_licitatorio) REFERENCES public.processo_licitatorio(id_processo_licitatorio);


--
-- Name: documento fk_processo_licitatorio_documento; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento
    ADD CONSTRAINT fk_processo_licitatorio_documento FOREIGN KEY (id_processo_licitatorio) REFERENCES public.processo_licitatorio(id_processo_licitatorio);


--
-- Name: empenho fk_processo_licitatorio_empenho; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empenho
    ADD CONSTRAINT fk_processo_licitatorio_empenho FOREIGN KEY (id_processo_licitatorio) REFERENCES public.processo_licitatorio(id_processo_licitatorio);


--
-- Name: item_licitacao fk_processo_licitatorio_item_licitacao; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.item_licitacao
    ADD CONSTRAINT fk_processo_licitatorio_item_licitacao FOREIGN KEY (id_processo_licitatorio) REFERENCES public.processo_licitatorio(id_processo_licitatorio);


--
-- Name: nfe fk_processo_licitatorio_nfe; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nfe
    ADD CONSTRAINT fk_processo_licitatorio_nfe FOREIGN KEY (id_processo_licitatorio) REFERENCES public.processo_licitatorio(id_processo_licitatorio);


--
-- Name: objeto_analise fk_processo_licitatorio_objeto_analise; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.objeto_analise
    ADD CONSTRAINT fk_processo_licitatorio_objeto_analise FOREIGN KEY (id_processo_licitatorio) REFERENCES public.processo_licitatorio(id_processo_licitatorio);


--
-- Name: processo_licitatorio_pessoa fk_processo_licitatorio_processo_licitatorio_pessoa; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processo_licitatorio_pessoa
    ADD CONSTRAINT fk_processo_licitatorio_processo_licitatorio_pessoa FOREIGN KEY (id_processo_licitatorio) REFERENCES public.processo_licitatorio(id_processo_licitatorio);


--
-- Name: usuario_processo_licitatorio fk_processo_licitatorio_usuario_processo_licitatorio; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario_processo_licitatorio
    ADD CONSTRAINT fk_processo_licitatorio_usuario_processo_licitatorio FOREIGN KEY (id_processo_licitatorio) REFERENCES public.processo_licitatorio(id_processo_licitatorio);


--
-- Name: pessoa_fisica fk_situacao_cadastral_pessoa_fisica; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pessoa_fisica
    ADD CONSTRAINT fk_situacao_cadastral_pessoa_fisica FOREIGN KEY (id_situacao_cadastral) REFERENCES public.situacao_cadastral(id_situacao_cadastral);


--
-- Name: processo_licitatorio fk_tipo_cotacao_processo_licitatorio; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processo_licitatorio
    ADD CONSTRAINT fk_tipo_cotacao_processo_licitatorio FOREIGN KEY (id_tipo_cotacao) REFERENCES public.tipo_cotacao(id_tipo_cotacao);


--
-- Name: processo_licitatorio fk_tipo_licitacao_processo_licitatorio; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processo_licitatorio
    ADD CONSTRAINT fk_tipo_licitacao_processo_licitatorio FOREIGN KEY (id_tipo_licitacao) REFERENCES public.tipo_licitacao(id_tipo_licitacao);


--
-- Name: processo_licitatorio fk_tipo_objeto_licitacao_processo_licitatorio; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processo_licitatorio
    ADD CONSTRAINT fk_tipo_objeto_licitacao_processo_licitatorio FOREIGN KEY (id_tipo_objeto_licitacao) REFERENCES public.tipo_objeto_licitacao(id_tipo_objeto_licitacao);


--
-- Name: tipologia_alerta fk_tipologia_hipertipologia; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipologia_alerta
    ADD CONSTRAINT fk_tipologia_hipertipologia FOREIGN KEY (id_hipertipologia_alerta) REFERENCES public.hipertipologia_alerta(id_hipertipologia_alerta);


--
-- Name: objeto_analise fk_unidade_gestora_objeto_analise; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.objeto_analise
    ADD CONSTRAINT fk_unidade_gestora_objeto_analise FOREIGN KEY (id_unidade_gestora) REFERENCES public.unidade_gestora(id_unidade_gestora);


--
-- Name: processo_licitatorio fk_unidade_gestora_processo_licitatorio; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processo_licitatorio
    ADD CONSTRAINT fk_unidade_gestora_processo_licitatorio FOREIGN KEY (id_unidade_gestora) REFERENCES public.unidade_gestora(id_unidade_gestora);


--
-- Name: processo_licitatorio fk_unidade_orcamentaria_processo_licitatorio; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.processo_licitatorio
    ADD CONSTRAINT fk_unidade_orcamentaria_processo_licitatorio FOREIGN KEY (id_unidade_orcamentaria) REFERENCES public.unidade_orcamentaria(id_unidade_orcamentaria);


--
-- Name: sig_documento sig_documento_id_documento_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sig_documento
    ADD CONSTRAINT sig_documento_id_documento_fkey FOREIGN KEY (id_documento) REFERENCES public.documento(id_documento);


--
-- Name: sig_documento sig_documento_id_sig_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sig_documento
    ADD CONSTRAINT sig_documento_id_sig_fkey FOREIGN KEY (id_sig) REFERENCES public.sig(id_sig);


--
-- Name: sig_processo_licitatorio sig_processo_licitatorio_id_processo_licitatorio_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sig_processo_licitatorio
    ADD CONSTRAINT sig_processo_licitatorio_id_processo_licitatorio_fkey FOREIGN KEY (id_processo_licitatorio) REFERENCES public.processo_licitatorio(id_processo_licitatorio);


--
-- Name: sig_processo_licitatorio sig_processo_licitatorio_id_sig_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sig_processo_licitatorio
    ADD CONSTRAINT sig_processo_licitatorio_id_sig_fkey FOREIGN KEY (id_sig) REFERENCES public.sig(id_sig);


--
-- Name: view_processo_licitatorio_filtro; Type: MATERIALIZED VIEW DATA; Schema: public; Owner: -
--

REFRESH MATERIALIZED VIEW public.view_processo_licitatorio_filtro;


--
-- PostgreSQL database dump complete
--

\unrestrict ucowgYN9nPi6c7IOkyPUTTgOnTIB53qWv00APmAlMVsamFgCl6LO4APA2YEJ0lc

