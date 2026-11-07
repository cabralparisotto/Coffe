--obter o detalhamento por país de destino
WITH exportacoes AS (
    SELECT
        CAST(ano AS INTEGER)                    AS ano,
        CAST(mes AS INTEGER)                    AS mes,
        pais_destino,
        valor_fob_usd,
        peso_kg
    FROM refined.exportacoes_brasil_cafe_torrado
    WHERE fluxo = 'export'
      AND ncm = '09012100'
)
SELECT
    make_date(ano, mes, 1)                      AS mes,
    pais_destino,
    COUNT(*)                                    AS registros_comerciais,
    SUM(valor_fob_usd)                          AS valor_exportado_usd,
    SUM(peso_kg)                                AS peso_exportado_kg,
    SUM(valor_fob_usd) / NULLIF(SUM(peso_kg), 0)
        AS preco_medio_usd_por_kg
FROM exportacoes
GROUP BY ano, mes, pais_destino
ORDER BY ano, mes, valor_exportado_usd DESC;