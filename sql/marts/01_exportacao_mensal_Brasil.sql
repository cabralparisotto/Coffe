--quanto o Brasil exportou por mês?
WITH exportacoes AS (
    SELECT
        CAST(ano AS INTEGER)                    AS ano,
        CAST(mes AS INTEGER)                    AS mes,
        pais_destino,
        valor_fob_usd,
        peso_kg,
        quantidade_estatistica
    FROM refined.exportacoes_brasil_cafe_torrado
    WHERE fluxo = 'export'
      AND ncm = '09012100'
)
SELECT
    make_date(ano, mes, 1)                      AS mes,
    COUNT(*)                                    AS registros_comerciais,
    COUNT(DISTINCT pais_destino)               AS paises_destino,
    SUM(valor_fob_usd)                          AS valor_exportado_usd,
    SUM(peso_kg)                                AS peso_exportado_kg,
    SUM(quantidade_estatistica)                 AS quantidade_estatistica,
    SUM(valor_fob_usd) / NULLIF(SUM(peso_kg), 0)
        AS preco_medio_usd_por_kg
FROM exportacoes
GROUP BY ano, mes
ORDER BY ano, mes;