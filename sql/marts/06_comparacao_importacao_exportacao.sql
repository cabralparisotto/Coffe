--Comparação mensal: exportação brasileira x importação dos países.
WITH exportacoes_base AS (
    SELECT
        CAST(ano AS INTEGER) AS ano,
        CAST(mes AS INTEGER) AS mes,
        valor_fob_usd,
        peso_kg
    FROM refined.exportacoes_brasil_cafe_torrado
    WHERE fluxo = 'export'
      AND ncm = '09012100'
), exportacoes AS (
    SELECT
        make_date(ano, mes, 1) AS mes,
        SUM(valor_fob_usd) AS exportacoes_brasil_usd,
        SUM(peso_kg) AS exportacoes_brasil_kg
    FROM exportacoes_base
    GROUP BY ano, mes
), importacoes_base AS (
    SELECT
        CAST(ano AS INTEGER) AS ano,
        CAST(mes AS INTEGER) AS mes,
        valor_principal_usd,
        peso_liquido_kg
    FROM refined.importacoes_paises_cafe_torrado
    WHERE fluxo = 'M'
      AND codigo_produto_hs = '090121'
      AND parceiro_codigo = 0
), importacoes AS (
    SELECT
        make_date(ano, mes, 1) AS mes,
        SUM(valor_principal_usd) AS importacoes_paises_usd,
        SUM(peso_liquido_kg) AS importacoes_paises_kg
    FROM importacoes_base
    GROUP BY ano, mes
)
SELECT
    COALESCE(e.mes, i.mes) AS mes,
    e.exportacoes_brasil_usd,
    e.exportacoes_brasil_kg,
    i.importacoes_paises_usd,
    i.importacoes_paises_kg
FROM exportacoes AS e
FULL OUTER JOIN importacoes AS i USING (mes)
ORDER BY mes;