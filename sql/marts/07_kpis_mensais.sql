-- Indicadores mensais de exportação brasileira e importação.
WITH exportacoes AS (
    SELECT
        make_date(CAST(ano AS INTEGER), CAST(mes AS INTEGER), 1) AS mes,
        SUM(valor_fob_usd) AS valor_exportado_usd,
        SUM(peso_kg) AS peso_exportado_kg,
        COUNT(DISTINCT pais_destino) AS paises_destino,
        SUM(valor_fob_usd) / NULLIF(SUM(peso_kg), 0)
            AS preco_medio_exportado_usd_kg
    FROM refined.exportacoes_brasil_cafe_torrado
    WHERE fluxo = 'export'
      AND ncm = '09012100'
    GROUP BY CAST(ano AS INTEGER), CAST(mes AS INTEGER)
), importacoes AS (
    SELECT
        make_date(CAST(ano AS INTEGER), CAST(mes AS INTEGER), 1) AS mes,
        SUM(valor_principal_usd) AS valor_importado_usd,
        SUM(peso_liquido_kg) AS peso_importado_kg,
        COUNT(DISTINCT pais_relator_codigo) AS paises_relatores,
        SUM(valor_principal_usd) / NULLIF(SUM(peso_liquido_kg), 0)
            AS preco_medio_importado_usd_kg
    FROM refined.importacoes_paises_cafe_torrado
    WHERE fluxo = 'M'
      AND codigo_produto_hs = '090121'
      AND parceiro_codigo = 0
    GROUP BY CAST(ano AS INTEGER), CAST(mes AS INTEGER)
)
SELECT
    COALESCE(e.mes, i.mes) AS mes,
    e.valor_exportado_usd,
    e.peso_exportado_kg,
    e.paises_destino,
    e.preco_medio_exportado_usd_kg,
    i.valor_importado_usd,
    i.peso_importado_kg,
    i.paises_relatores,
    i.preco_medio_importado_usd_kg
FROM exportacoes AS e
FULL OUTER JOIN importacoes AS i USING (mes)
ORDER BY mes;
