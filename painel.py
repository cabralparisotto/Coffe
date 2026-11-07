"""SPEC — Visualização do pipeline de comércio exterior de café torrado

CONTEXTO
- O projeto usa Python 3.13, uv, DuckDB, pandas, Streamlit e Plotly.
- O banco do projeto é ``cafe.duckdb`` na raiz, e não ``olist.duckdb``.
- O pipeline produz tabelas de exportação do Brasil e importação de café
  torrado; os dados não representam pedidos, clientes ou avaliações.

ARTEFATOS E ESCOPO
- Este módulo lê, formata e cria figuras, sem importar Streamlit. Assim as
  figuras podem ser reutilizadas fora da página.
- ``ler`` devolve um DataFrame por mart e executa somente ``SELECT *`` em cada
  tabela solicitada. A conexão read-only é aberta e fechada dentro da função
  para não impedir que ``pipeline.marts`` atualize o banco.
- Os sete marts necessários são ``exportacao_mensal_Brasil``,
  ``detalhamento_pais_destino``, ``quanto_os_paises_importam``,
  ``paises_mais_compram_torrado``, ``ranking_compram``,
  ``comparacao_importacao_exportacao`` e ``kpis_mensais``. O último é definido
  por ``sql/marts/07_kpis_mensais.sql`` e reúne valores mensais já agregados
  no SQL para os oito cartões.

REGRAS DE APRESENTAÇÃO
- Não calcular novas métricas em Python: os valores exibidos vêm dos marts.
  Permitidos são recorte de linhas, ordenação, limite de linhas, rótulos e
  formatação de texto. Uma regra de negócio nova precisa ser definida no SQL.
- Os formatadores são funções puras e não dependem da localidade do sistema.
  A moeda é exibida em USD, pois os valores de origem são em dólares.
- Cada gráfico tem uma função que recebe DataFrames e devolve uma figura
  Plotly, sem conexão ao banco ou dependência de Streamlit.

FILTRO E CARTÕES
- O filtro de período recorta as séries temporais e o ranking mensal.
- Os cartões mostram os valores do último mês selecionado no intervalo; os
  gráficos por país mostram esse mesmo mês. Isso permite comparar a seleção
  temporal sem criar agregações na camada de apresentação.
- Quando ``pais_relator`` estiver ausente no dado de origem, o gráfico de
  importações usa o código numérico do relator para não ocultar as barras.
- O mart ``kpis_mensais`` alimenta os cartões e o gráfico mensal de preços
  médios de exportação e importação em USD/kg.
- A seleção inicial é janeiro a dezembro de 2023, período mensal existente
  tanto nos dados de exportação quanto nos de importação. O histórico de
  exportações chega a dezembro de 2024; fora de 2023, campos de importação
  sem valor no mart são apresentados como ``—``.
"""

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

CAMINHO_BANCO = Path(__file__).resolve().parent / "cafe.duckdb"
MARTS = (
    "exportacao_mensal_Brasil",
    "detalhamento_pais_destino",
    "quanto_os_paises_importam",
    "paises_mais_compram_torrado",
    "ranking_compram",
    "comparacao_importacao_exportacao",
    "kpis_mensais",
)
COR_CAFE = "#6F4E37"
MESES_PT = (
    "jan",
    "fev",
    "mar",
    "abr",
    "mai",
    "jun",
    "jul",
    "ago",
    "set",
    "out",
    "nov",
    "dez",
)


class MartsAusentes(Exception):
    """Um ou mais marts necessários não existem no banco."""

    def __init__(self, nomes: list[str]):
        self.nomes = nomes
        super().__init__(", ".join(nomes))


def ler(marts: tuple[str, ...] = MARTS) -> dict[str, pd.DataFrame]:
    """Lê cada tabela de mart solicitada e fecha a conexão antes de retornar."""
    con = duckdb.connect(str(CAMINHO_BANCO), read_only=True)
    dados = {}
    ausentes = []
    try:
        for nome in marts:
            try:
                dados[nome] = con.execute(f"SELECT * FROM marts.{nome}").fetchdf()
            except duckdb.CatalogException:
                ausentes.append(nome)
    finally:
        con.close()

    if ausentes:
        raise MartsAusentes(ausentes)
    return dados


def numero(valor, casas: int = 0) -> str:
    """Formata números com ponto para milhar e vírgula para decimal."""
    if valor is None or pd.isna(valor):
        return "—"
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "\0").replace(".", ",").replace("\0", ".")


def usd(valor, casas: int = 2) -> str:
    """Formata um valor monetário em dólares americanos."""
    resultado = numero(valor, casas)
    return "—" if resultado == "—" else f"US$ {resultado}"


def formatar_mes(valor) -> str:
    """Formata uma data mensal em português sem depender da localidade."""
    mes = pd.Timestamp(valor)
    return f"{MESES_PT[mes.month - 1]}/{mes.year}"


def grafico_exportacoes_mensais(df: pd.DataFrame) -> go.Figure:
    figura = px.line(
        df,
        x="mes",
        y="valor_exportado_usd",
        markers=True,
        title="01 · Exportações mensais",
        labels={"mes": "Mês", "valor_exportado_usd": "Exportado (US$)"},
    )
    figura.update_traces(line_color=COR_CAFE)
    figura.update_layout(xaxis_tickformat="%m/%Y", yaxis_title="US$")
    return figura


def grafico_importacoes_mensais(df: pd.DataFrame) -> go.Figure:
    figura = px.line(
        df,
        x="mes",
        y="valor_importado_usd",
        markers=True,
        title="03 · Importações mensais",
        labels={"mes": "Mês", "valor_importado_usd": "Importado (US$)"},
    )
    figura.update_traces(line_color=COR_CAFE)
    figura.update_layout(xaxis_tickformat="%m/%Y", yaxis_title="US$")
    return figura


def grafico_preco_medio_mensal(df: pd.DataFrame) -> go.Figure:
    figura = px.line(
        df,
        x="mes",
        y=["preco_medio_exportado_usd_kg", "preco_medio_importado_usd_kg"],
        markers=True,
        title="07 · Preço médio mensal de exportação e importação",
        labels={
            "mes": "Mês",
            "value": "Preço médio (US$/kg)",
            "variable": "Série",
            "preco_medio_exportado_usd_kg": "Exportação",
            "preco_medio_importado_usd_kg": "Importação",
        },
        color_discrete_sequence=[COR_CAFE, "#C9A66B"],
    )
    figura.update_layout(xaxis_tickformat="%m/%Y", yaxis_title="US$/kg")
    return figura


def grafico_comparacao_mensal(df: pd.DataFrame) -> go.Figure:
    figura = px.line(
        df,
        x="mes",
        y=["exportacoes_brasil_usd", "importacoes_paises_usd"],
        markers=True,
        title="06 · Exportações brasileiras x importações registradas",
        labels={
            "mes": "Mês",
            "value": "Valor (US$)",
            "variable": "Série",
            "exportacoes_brasil_usd": "Exportações do Brasil",
            "importacoes_paises_usd": "Importações mundiais",
        },
        color_discrete_sequence=[COR_CAFE, "#C9A66B"],
    )
    figura.update_layout(xaxis_tickformat="%m/%Y", yaxis_title="US$")
    return figura


def grafico_exportacoes_por_destino(df: pd.DataFrame, mes) -> go.Figure:
    recorte = df.loc[df["mes"] == mes]
    recorte = recorte.sort_values("valor_exportado_usd", ascending=False).head(10)
    figura = px.bar(
        recorte,
        x="valor_exportado_usd",
        y="pais_destino",
        orientation="h",
        title="02 · Destinos das exportações no mês final",
        labels={
            "valor_exportado_usd": "Exportado (US$)",
            "pais_destino": "País de destino",
        },
        color_discrete_sequence=[COR_CAFE],
    )
    figura.update_yaxes(autorange="reversed")
    figura.update_layout(xaxis_title="US$")
    return figura


def grafico_importacoes_por_pais(df: pd.DataFrame, mes) -> go.Figure:
    recorte = df.loc[df["mes"] == mes]
    recorte = recorte.sort_values("valor_importado_usd", ascending=False).head(10)
    recorte = recorte.copy()
    recorte["pais_relator"] = recorte["pais_relator"].fillna(
        recorte["pais_relator_codigo"].map(lambda codigo: f"Código {codigo}")
    )
    figura = px.bar(
        recorte,
        x="valor_importado_usd",
        y="pais_relator",
        orientation="h",
        title="04 · Países relatores de importação no mês final",
        labels={
            "valor_importado_usd": "Importado (US$)",
            "pais_relator": "País relator",
        },
        color_discrete_sequence=[COR_CAFE],
    )
    figura.update_yaxes(autorange="reversed")
    figura.update_layout(xaxis_title="US$")
    return figura


def grafico_ranking_mensal(df: pd.DataFrame) -> go.Figure:
    figura = px.line(
        df,
        x="mes",
        y="posicao",
        color="pais_destino",
        title="05 · Evolução do ranking mensal de destinos",
        labels={
            "mes": "Mês",
            "posicao": "Posição no ranking",
            "pais_destino": "País de destino",
        },
    )
    figura.update_yaxes(autorange="reversed", dtick=1)
    figura.update_layout(xaxis_tickformat="%m/%Y")
    return figura
