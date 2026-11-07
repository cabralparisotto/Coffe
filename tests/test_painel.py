import pandas as pd

import painel


def test_formatadores_usam_notacao_pt_br():
    assert painel.numero(1_003_862.14, 2) == "1.003.862,14"
    assert painel.usd(1_003_862.14) == "US$ 1.003.862,14"
    assert painel.numero(float("nan")) == "—"
    assert painel.formatar_mes(pd.Timestamp("2023-01-01")) == "jan/2023"


def test_grafico_de_destinos_filtra_mes_e_mostra_os_dez_maiores():
    mes = pd.Timestamp("2023-01-01")
    dados = pd.DataFrame(
        {
            "mes": [mes] * 11 + [pd.Timestamp("2023-02-01")],
            "pais_destino": [f"país_{indice}" for indice in range(11)] + ["outro_mês"],
            "valor_exportado_usd": list(range(11)) + [100],
        }
    )

    figura = painel.grafico_exportacoes_por_destino(dados, mes)

    assert list(figura.data[0].y) == [f"país_{indice}" for indice in range(10, 0, -1)]


def test_grafico_de_importacoes_usa_codigo_quando_nome_esta_ausente():
    mes = pd.Timestamp("2023-12-01")
    dados = pd.DataFrame(
        {
            "mes": [mes, mes],
            "pais_relator": [None, "País conhecido"],
            "pais_relator_codigo": [36, 76],
            "valor_importado_usd": [100, 50],
        }
    )

    figura = painel.grafico_importacoes_por_pais(dados, mes)

    assert list(figura.data[0].y) == ["Código 36", "País conhecido"]


def test_grafico_de_precos_mensais_compara_duas_series():
    dados = pd.DataFrame(
        {
            "mes": [pd.Timestamp("2023-01-01")],
            "preco_medio_exportado_usd_kg": [8.5],
            "preco_medio_importado_usd_kg": [9.8],
        }
    )

    figura = painel.grafico_preco_medio_mensal(dados)

    assert len(figura.data) == 2
    assert list(figura.data[0].y) == [8.5]
    assert list(figura.data[1].y) == [9.8]
