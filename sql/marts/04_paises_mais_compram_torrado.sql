--paises que mais compram café torrado do Brasil
WITH importacoes AS (
    SELECT
        CAST(ano AS INTEGER)                    AS ano,
        CAST(mes AS INTEGER)                    AS mes,
        pais_relator_codigo,
        COALESCE(
            pais_relator,
            CASE pais_relator_codigo
                WHEN 36 THEN 'Austrália'
                WHEN 56 THEN 'Bélgica'
                WHEN 76 THEN 'Brasil'
                WHEN 100 THEN 'Bulgária'
                WHEN 124 THEN 'Canadá'
                WHEN 152 THEN 'Chile'
                WHEN 170 THEN 'Colômbia'
                WHEN 191 THEN 'Croácia'
                WHEN 204 THEN 'Benim'
                WHEN 208 THEN 'Dinamarca'
                WHEN 233 THEN 'Estônia'
                WHEN 246 THEN 'Finlândia'
                WHEN 276 THEN 'Alemanha'
                WHEN 300 THEN 'Grécia'
                WHEN 348 THEN 'Hungria'
                WHEN 372 THEN 'Irlanda'
                WHEN 376 THEN 'Israel'
                WHEN 380 THEN 'Itália'
                WHEN 392 THEN 'Japão'
                WHEN 398 THEN 'Cazaquistão'
                WHEN 404 THEN 'Quênia'
                WHEN 410 THEN 'Coreia do Sul'
                WHEN 440 THEN 'Lituânia'
                WHEN 442 THEN 'Luxemburgo'
                WHEN 458 THEN 'Malásia'
                WHEN 484 THEN 'México'
                WHEN 504 THEN 'Marrocos'
                WHEN 528 THEN 'Países Baixos'
                WHEN 554 THEN 'Nova Zelândia'
                WHEN 586 THEN 'Paquistão'
                WHEN 591 THEN 'Panamá'
                WHEN 600 THEN 'Paraguai'
                WHEN 616 THEN 'Polônia'
                WHEN 620 THEN 'Portugal'
                WHEN 642 THEN 'Romênia'
                WHEN 688 THEN 'Sérvia'
                WHEN 702 THEN 'Singapura'
                WHEN 710 THEN 'África do Sul'
                WHEN 724 THEN 'Espanha'
                WHEN 752 THEN 'Suécia'
                WHEN 764 THEN 'Tailândia'
                WHEN 792 THEN 'Turquia'
                WHEN 804 THEN 'Ucrânia'
                WHEN 818 THEN 'Egito'
                WHEN 834 THEN 'Tanzânia'
                WHEN 854 THEN 'Burkina Faso'
                WHEN 858 THEN 'Uruguai'
                WHEN 860 THEN 'Uzbequistão'
                WHEN 887 THEN 'Iêmen'
                WHEN 894 THEN 'Zâmbia'
                ELSE CAST(pais_relator_codigo AS VARCHAR)
            END
        ) AS pais_relator,
        valor_principal_usd,
        peso_liquido_kg
    FROM refined.importacoes_paises_cafe_torrado
    WHERE fluxo = 'M'
      AND codigo_produto_hs = '090121'
      AND parceiro_codigo = 0
)
SELECT
    make_date(ano, mes, 1)                      AS mes,
    pais_relator_codigo,
    pais_relator,
    valor_principal_usd                         AS valor_importado_usd,
    peso_liquido_kg                              AS peso_importado_kg,
    valor_principal_usd / NULLIF(peso_liquido_kg, 0)
        AS preco_medio_usd_por_kg
FROM importacoes
ORDER BY mes, valor_importado_usd DESC;