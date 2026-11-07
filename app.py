"""Página Streamlit para explorar os marts de comércio de café torrado."""

import duckdb
import pandas as pd
import streamlit as st

import painel

st.set_page_config(page_title="Café · comércio exterior", layout="wide")


@st.cache_data
def carregar_dados() -> dict[str, pd.DataFrame]:
    return painel.ler()


if not painel.CAMINHO_BANCO.is_file():
    st.error(
        f"Banco ausente: {painel.CAMINHO_BANCO}. "
        "Execute `uv run python -m pipeline.marts`."
    )
    st.stop()

try:
    dados = carregar_dados()
except painel.MartsAusentes as erro:
    nomes = ", ".join(f"marts.{nome}" for nome in erro.nomes)
    st.error(f"Marts ausentes: {nomes}. Execute `uv run python -m pipeline.marts`.")
    st.stop()
except duckdb.Error as erro:
    st.error(f"Não foi possível ler cafe.duckdb: {erro}")
    st.stop()

meses = sorted(
    pd.Timestamp(mes)
    for mes in dados["exportacao_mensal_Brasil"]["mes"].drop_duplicates()
)
padrao = (pd.Timestamp("2023-01-01"), pd.Timestamp("2023-12-01"))
if padrao[0] not in meses or padrao[1] not in meses:
    padrao = (meses[0], meses[-1])

coluna_titulo, coluna_filtro = st.columns([2, 1])
with coluna_titulo:
    st.title("Café torrado · comércio exterior")
    if st.button("Recarregar dados"):
        st.cache_data.clear()
        st.rerun()

with coluna_filtro:
    st.subheader("Período")
    periodo = st.select_slider(
        "Selecione o intervalo",
        options=meses,
        value=padrao,
        format_func=painel.formatar_mes,
    )

inicio, fim = periodo
st.caption(
    "Os cartões e os gráficos por país mostram o mês final selecionado; "
    "as séries temporais mostram o intervalo. Os dados de importação "
    "disponíveis neste banco cobrem 2023."
)


def filtrar_periodo(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[df["mes"].between(inicio, fim)]


linha_mes = dados["kpis_mensais"].loc[dados["kpis_mensais"]["mes"] == fim]
kpis = linha_mes.iloc[0] if not linha_mes.empty else None

st.subheader(f"Indicadores de {painel.formatar_mes(fim)}")
cartoes_exportacao = st.columns(4)
cartoes_importacao = st.columns(4)

valores_exportacao = (
    (
        "Exportado · USD",
        painel.usd(kpis["valor_exportado_usd"]) if kpis is not None else "—",
    ),
    (
        "Exportado · kg",
        painel.numero(kpis["peso_exportado_kg"], 2) if kpis is not None else "—",
    ),
    (
        "Países de destino",
        painel.numero(kpis["paises_destino"]) if kpis is not None else "—",
    ),
    (
        "Preço médio exportado",
        f"{painel.usd(kpis['preco_medio_exportado_usd_kg'])}/kg"
        if kpis is not None and pd.notna(kpis["preco_medio_exportado_usd_kg"])
        else "—",
    ),
)
valores_importacao = (
    (
        "Importado · USD",
        painel.usd(kpis["valor_importado_usd"]) if kpis is not None else "—",
    ),
    (
        "Importado · kg",
        painel.numero(kpis["peso_importado_kg"], 2) if kpis is not None else "—",
    ),
    (
        "Países relatores",
        painel.numero(kpis["paises_relatores"]) if kpis is not None else "—",
    ),
    (
        "Preço médio importado",
        f"{painel.usd(kpis['preco_medio_importado_usd_kg'])}/kg"
        if kpis is not None and pd.notna(kpis["preco_medio_importado_usd_kg"])
        else "—",
    ),
)

for coluna, (rotulo, valor) in zip(cartoes_exportacao, valores_exportacao):
    coluna.metric(rotulo, valor)
for coluna, (rotulo, valor) in zip(cartoes_importacao, valores_importacao):
    coluna.metric(rotulo, valor)

coluna_exportacoes, coluna_importacoes = st.columns(2)
with coluna_exportacoes:
    st.plotly_chart(
        painel.grafico_exportacoes_mensais(
            filtrar_periodo(dados["exportacao_mensal_Brasil"])
        ),
        width="stretch",
    )
with coluna_importacoes:
    st.plotly_chart(
        painel.grafico_importacoes_mensais(
            filtrar_periodo(dados["quanto_os_paises_importam"])
        ),
        width="stretch",
    )

st.plotly_chart(
    painel.grafico_comparacao_mensal(
        filtrar_periodo(dados["comparacao_importacao_exportacao"])
    ),
    width="stretch",
)

st.plotly_chart(
    painel.grafico_preco_medio_mensal(filtrar_periodo(dados["kpis_mensais"])),
    width="stretch",
)

coluna_destinos, coluna_relatores = st.columns(2)
with coluna_destinos:
    st.plotly_chart(
        painel.grafico_exportacoes_por_destino(dados["detalhamento_pais_destino"], fim),
        width="stretch",
    )
with coluna_relatores:
    st.plotly_chart(
        painel.grafico_importacoes_por_pais(dados["paises_mais_compram_torrado"], fim),
        width="stretch",
    )

st.plotly_chart(
    painel.grafico_ranking_mensal(filtrar_periodo(dados["ranking_compram"])),
    width="stretch",
)
