--Quanto os países importam por mês?
WITH importacoes AS (
    SELECT
        CAST(ano AS INTEGER)                    AS ano,
        CAST(mes AS INTEGER)                    AS mes,
        pais_relator_codigo,
        valor_principal_usd,
        peso_liquido_kg
    FROM refined.importacoes_paises_cafe_torrado
    WHERE fluxo = 'M'
      AND codigo_produto_hs = '090121'
      AND parceiro_codigo = 0
)
SELECT
    make_date(ano, mes, 1)                      AS mes,
    COUNT(*)                                    AS registros_comerciais,
    COUNT(DISTINCT pais_relator_codigo)         AS paises_relatores,
    SUM(valor_principal_usd)                   AS valor_importado_usd,
    SUM(peso_liquido_kg)                       AS peso_importado_kg,
    SUM(valor_principal_usd)
        / NULLIF(SUM(peso_liquido_kg), 0)
        AS preco_medio_usd_por_kg
FROM importacoes
GROUP BY ano, mes
ORDER BY ano, mes;