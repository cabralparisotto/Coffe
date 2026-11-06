"""Módulo compartilhado de conexão e gravação do banco.

Spec:
- ``PASTA_RAW`` aponta para os arquivos de entrada relativamente à localização
  deste módulo, em ``data/raw``; ``cafe.duckdb`` também fica na raiz do projeto. Assim, executar
  etapas a partir de outra pasta não cria um banco vazio no diretório errado.
- ``conectar`` abre ou cria o banco e devolve a conexão ao chamador, que é
  responsável por fechá-la; nenhuma conexão global mantém o arquivo bloqueado.
- ``criar_schema`` cria o schema somente se necessário para que etapas possam
  ser repetidas sem falhar quando ele já existe.
- ``gravar`` substitui a tabela usando os valores e tipos presentes no
  DataFrame, sem limpeza ou conversão, e consulta a contagem persistida para
  que a saída reflita o conteúdo do banco. A relação registrada é removida ao
  final para não deixar objetos temporários para trás.
- Este módulo não lê arquivos, imprime nem codifica nomes de tabelas ou regras
  de negócio, pois cada etapa deve decidir esses detalhes explicitamente.
"""

from pathlib import Path as _Path

import duckdb as _duckdb

PASTA_RAW = _Path(__file__).resolve().parent.parent / "data" / "raw"


def conectar():
    """Abre o banco localizado na raiz do projeto."""
    caminho_banco = _Path(__file__).resolve().parent.parent / "cafe.duckdb"
    return _duckdb.connect(str(caminho_banco))


def criar_schema(con, nome):
    """Cria um schema se ele ainda não existir."""
    nome_sql = '"' + nome.replace('"', '""') + '"'
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {nome_sql}")


def gravar(con, df, schema, tabela):
    """Substitui uma tabela pelos dados do DataFrame e devolve sua contagem."""
    schema_sql = '"' + schema.replace('"', '""') + '"'
    tabela_sql = '"' + tabela.replace('"', '""') + '"'
    con.register("_dataframe_para_gravar", df)
    try:
        con.execute(
            f"CREATE OR REPLACE TABLE {schema_sql}.{tabela_sql} "
            "AS SELECT * FROM _dataframe_para_gravar"
        )
        resultado = con.execute(
            f"SELECT count(*) FROM {schema_sql}.{tabela_sql}"
        ).fetchall()
        return resultado[0][0]
    finally:
        con.unregister("_dataframe_para_gravar")
