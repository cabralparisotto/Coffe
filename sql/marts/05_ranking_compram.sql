--Ranking mensal dos países que compraram café do Brasil.
WITH exportacoes_base AS (
    SELECT
        CAST(ano AS INTEGER) AS ano,
        CAST(mes AS INTEGER) AS mes,
        pais_destino,
        valor_fob_usd,
        peso_kg
    FROM refined.exportacoes_brasil_cafe_torrado
    WHERE fluxo = 'export'
      AND ncm = '09012100'
), exportacoes AS (
    SELECT
        make_date(ano, mes, 1) AS mes,
        pais_destino,
        SUM(valor_fob_usd) AS valor_exportado_usd,
        SUM(peso_kg) AS peso_exportado_kg
    FROM exportacoes_base
    GROUP BY ano, mes, pais_destino
), ranking AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY mes
            ORDER BY valor_exportado_usd DESC
        ) AS posicao
    FROM exportacoes
)
SELECT
    mes,
    posicao,
    pais_destino,
    valor_exportado_usd,
    peso_exportado_kg,
    valor_exportado_usd / NULLIF(peso_exportado_kg, 0)
        AS preco_medio_usd_por_kg
FROM ranking
WHERE posicao <= 10
ORDER BY mes, posicao;