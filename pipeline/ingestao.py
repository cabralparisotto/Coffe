"""Ingestão das duas tabelas atuais de comércio de café.

Spec:
- Lê os CSVs de ``PASTA_RAW`` sem descompactar nem alterar nomes de colunas,
  valores, ordem ou quantidade de linhas; essa fronteira preserva o dado
  recebido para que decisões de limpeza pertençam à etapa refined.
- Usa ``encoding="utf-8"`` e ``dtype=str`` para não adivinhar codificação nem
  inferir números e datas, evitando, por exemplo, perder zeros à esquerda.
  Apenas campos vazios são nulos; textos como ``NA`` permanecem textos.
- Recria as tabelas ``raw.exportacoes_brasil_cafe_torrado`` e
  ``raw.importacoes_paises_cafe_torrado`` em cada execução, tornando a
  reexecução previsível e sem duplicação.
- Verifica a presença de todos os arquivos antes de abrir o banco para evitar
  uma ingestão parcial por arquivos ausentes.
- Exibe as contagens lidas do banco, com milhar separado por ponto, e o total
  para conferir o que foi persistido. O stdout é UTF-8 para preservar acentos
  em terminais cujo encoding padrão seja diferente.
"""

import sys

import pandas as pd

from pipeline.db import PASTA_RAW, conectar, criar_schema, gravar

ARQUIVOS = (
    (
        "tabela_1_exportacoes_brasil_cafe_torrado_500plus.csv",
        "exportacoes_brasil_cafe_torrado",
    ),
    (
        "tabela_2_importacoes_paises_cafe_torrado_500plus.csv",
        "importacoes_paises_cafe_torrado",
    ),
)


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    ausentes = [
        arquivo for arquivo, _ in ARQUIVOS if not (PASTA_RAW / arquivo).is_file()
    ]
    if ausentes:
        print(f"Arquivos ausentes em {PASTA_RAW}:")
        for arquivo in ausentes:
            print(f"- {arquivo}")
        sys.exit(1)

    dataframes = [
        (
            tabela,
            pd.read_csv(
                PASTA_RAW / arquivo,
                encoding="utf-8",
                dtype=str,
                keep_default_na=False,
                na_values=[""],
                skip_blank_lines=False,
            ),
        )
        for arquivo, tabela in ARQUIVOS
    ]

    con = conectar()
    try:
        criar_schema(con, "raw")
        total = 0
        for tabela, df in dataframes:
            contagem = gravar(con, df, "raw", tabela)
            total += contagem
            linhas = "linha" if contagem == 1 else "linhas"
            print(f"raw.{tabela}: {contagem:,} {linhas}".replace(",", "."))
        print(f"Total: {total:,} linhas".replace(",", "."))
    finally:
        con.close()


if __name__ == "__main__":
    main()
