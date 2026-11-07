"""SPEC — Relatório HTML estático do painel de comércio de café torrado

CONTEXTO
- O relatório pertence ao projeto de comércio exterior de café torrado e usa
  ``cafe.duckdb`` e os marts definidos em ``painel.py``, não dados da Olist.
- A docstring de ``painel.py`` continua sendo a especificação das métricas,
  dos formatadores e das funções de gráfico.

ARTEFATO E REUSO
- Executar com ``uv run python relatorio.py`` e gerar ``relatorio.html`` na
  raiz do projeto para que possa ser aberto diretamente no navegador.
- Ler os marts com ``painel.ler()``, formatar com ``painel.usd`` e
  ``painel.numero`` e construir gráficos exclusivamente com funções de
  ``painel.py``. Isso mantém o relatório alinhado ao app e evita duplicar
  regras de apresentação ou negócio.
- Não importar Streamlit. Cada gráfico é serializado com
  ``figura.to_html(full_html=False)``; somente o primeiro fragmento inclui a
  biblioteca Plotly do CDN. Assim o HTML é único e não repete o runtime.

PERÍODO E LAYOUT
- Usar o período padrão real do ``app.py``: janeiro a dezembro de 2023. Os
  dados de importação deste projeto estão disponíveis nesse intervalo; o
  período jan/2017–ago/2018 da spec inicial pertence ao painel Olist.
- Mostrar os oito cartões atuais com os mesmos dados do app, que representam
  o mês final selecionado (dezembro de 2023).
- Reproduzir a ordem e a disposição atuais do ``app.py``: cartões; gráficos
  01 e 03 lado a lado; 06 em largura total; 07 em largura total; 02 e 04 lado
  a lado; 05 em largura total. Esses são os sete gráficos existentes em
  ``painel.py``; a referência a quatro faixas não corresponde ao layout real.
- Incluir o intervalo no título do gráfico de exportações mensais e IDs fixos
  ``g01`` a ``g07`` para que o HTML permaneça estável entre execuções.

RODAPÉ E SAÍDA
- Registrar a data e hora local de geração no formato
  ``Dados de DD/MM/AAAA HH:MM``; o arquivo estático não consulta o banco ao
  ser aberto.
- Reconfigurar stdout para UTF-8 e imprimir o caminho e o tamanho do arquivo
  em KB para confirmar a saída gerada.
"""

import sys
from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd

import painel

RAIZ = Path(__file__).resolve().parent
CAMINHO_RELATORIO = RAIZ / "relatorio.html"
PERIODO_INICIAL = pd.Timestamp("2023-01-01")
PERIODO_FINAL = pd.Timestamp("2023-12-01")


def cartoes(
    kpi: pd.Series | None,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Retorna os dois grupos de cartões usando os formatadores do painel."""
    exportacao = [
        (
            "Exportado · USD",
            painel.usd(kpi["valor_exportado_usd"]) if kpi is not None else "—",
        ),
        (
            "Exportado · kg",
            painel.numero(kpi["peso_exportado_kg"], 2) if kpi is not None else "—",
        ),
        (
            "Países de destino",
            painel.numero(kpi["paises_destino"]) if kpi is not None else "—",
        ),
        (
            "Preço médio exportado",
            f"{painel.usd(kpi['preco_medio_exportado_usd_kg'])}/kg"
            if kpi is not None and pd.notna(kpi["preco_medio_exportado_usd_kg"])
            else "—",
        ),
    ]
    importacao = [
        (
            "Importado · USD",
            painel.usd(kpi["valor_importado_usd"]) if kpi is not None else "—",
        ),
        (
            "Importado · kg",
            painel.numero(kpi["peso_importado_kg"], 2) if kpi is not None else "—",
        ),
        (
            "Países relatores",
            painel.numero(kpi["paises_relatores"]) if kpi is not None else "—",
        ),
        (
            "Preço médio importado",
            f"{painel.usd(kpi['preco_medio_importado_usd_kg'])}/kg"
            if kpi is not None and pd.notna(kpi["preco_medio_importado_usd_kg"])
            else "—",
        ),
    ]
    return exportacao, importacao


def html_cartoes(grupo: list[tuple[str, str]]) -> str:
    itens = "".join(
        '<article class="card">'
        f"<div>{escape(rotulo)}</div>"
        f"<strong>{escape(valor)}</strong>"
        "</article>"
        for rotulo, valor in grupo
    )
    return f'<div class="cards">{itens}</div>'


def montar_html(dados: dict[str, pd.DataFrame], gerado_em: datetime) -> str:
    """Monta o documento usando apenas os dados e gráficos do painel."""
    exportacoes = dados["exportacao_mensal_Brasil"]
    meses = {pd.Timestamp(mes) for mes in exportacoes["mes"].drop_duplicates()}
    if PERIODO_INICIAL in meses and PERIODO_FINAL in meses:
        inicio, fim = PERIODO_INICIAL, PERIODO_FINAL
    else:
        inicio, fim = min(meses), max(meses)

    def filtrar_periodo(df: pd.DataFrame) -> pd.DataFrame:
        return df.loc[df["mes"].between(inicio, fim)]

    linha_kpi = dados["kpis_mensais"].loc[dados["kpis_mensais"]["mes"] == fim]
    kpi = linha_kpi.iloc[0] if not linha_kpi.empty else None
    cartoes_exportacao, cartoes_importacao = cartoes(kpi)
    titulo_periodo = f"{painel.formatar_mes(inicio)} a {painel.formatar_mes(fim)}"

    figura_exportacoes = painel.grafico_exportacoes_mensais(
        filtrar_periodo(exportacoes)
    )
    figura_exportacoes.update_layout(
        title=f"01 · Exportações mensais · {titulo_periodo}"
    )

    figuras = [
        ("g01", figura_exportacoes),
        (
            "g03",
            painel.grafico_importacoes_mensais(
                filtrar_periodo(dados["quanto_os_paises_importam"])
            ),
        ),
        (
            "g06",
            painel.grafico_comparacao_mensal(
                filtrar_periodo(dados["comparacao_importacao_exportacao"])
            ),
        ),
        (
            "g07",
            painel.grafico_preco_medio_mensal(filtrar_periodo(dados["kpis_mensais"])),
        ),
        (
            "g02",
            painel.grafico_exportacoes_por_destino(
                dados["detalhamento_pais_destino"], fim
            ),
        ),
        (
            "g04",
            painel.grafico_importacoes_por_pais(
                dados["paises_mais_compram_torrado"], fim
            ),
        ),
        (
            "g05",
            painel.grafico_ranking_mensal(filtrar_periodo(dados["ranking_compram"])),
        ),
    ]

    fragmentos = []
    for indice, (div_id, figura) in enumerate(figuras):
        fragmentos.append(
            figura.to_html(
                full_html=False,
                include_plotlyjs="cdn" if indice == 0 else False,
                div_id=div_id,
            )
        )

    rodape = gerado_em.astimezone().strftime("Dados de %d/%m/%Y %H:%M")
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Café torrado · comércio exterior</title>
  <style>
    :root {{ color-scheme: light; font-family: Arial, sans-serif; }}
    body {{ margin: 0; padding: 28px; background: #f7f5f2; color: #25211e; }}
    main {{ max-width: 1440px; margin: 0 auto; }}
    h1 {{ margin: 0 0 6px; color: #3d2b1f; }}
    .periodo {{ margin: 0 0 24px; color: #6b625b; }}
    h2 {{ margin: 22px 0 12px; font-size: 1.2rem; }}
    .cards {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }}
    .card {{ padding: 16px; background: white; border-radius: 8px; box-shadow: 0 1px 5px #0001; }}
    .card div {{ color: #6b625b; font-size: .9rem; }}
    .card strong {{ display: block; margin-top: 8px; font-size: 1.35rem; color: #3d2b1f; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }}
    .grafico {{ min-width: 0; margin-top: 16px; padding: 8px; background: white; border-radius: 8px; }}
    footer {{ margin-top: 24px; color: #6b625b; font-size: .9rem; }}
    @media (max-width: 800px) {{
      body {{ padding: 14px; }}
      .cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <h1>Café torrado · comércio exterior</h1>
    <p class="periodo">Período: {escape(titulo_periodo)} · cartões referentes a {escape(painel.formatar_mes(fim))}</p>
    <h2>Indicadores de exportação</h2>
    {html_cartoes(cartoes_exportacao)}
    <h2>Indicadores de importação</h2>
    {html_cartoes(cartoes_importacao)}
    <section class="grid">
      <div class="grafico">{fragmentos[0]}</div>
      <div class="grafico">{fragmentos[1]}</div>
    </section>
    <div class="grafico">{fragmentos[2]}</div>
    <div class="grafico">{fragmentos[3]}</div>
    <section class="grid">
      <div class="grafico">{fragmentos[4]}</div>
      <div class="grafico">{fragmentos[5]}</div>
    </section>
    <div class="grafico">{fragmentos[6]}</div>
    <footer>{escape(rodape)}</footer>
  </main>
</body>
</html>
"""


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        dados = painel.ler()
    except (OSError, painel.MartsAusentes) as erro:
        print(f"Não foi possível gerar o relatório: {erro}", file=sys.stderr)
        sys.exit(1)

    documento = montar_html(dados, datetime.now().astimezone())
    CAMINHO_RELATORIO.write_text(documento, encoding="utf-8")
    tamanho_kb = CAMINHO_RELATORIO.stat().st_size / 1024
    print(f"Relatório: {CAMINHO_RELATORIO}")
    print(f"Tamanho: {tamanho_kb:.1f} KB")


if __name__ == "__main__":
    main()
