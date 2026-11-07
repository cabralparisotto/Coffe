"""SPEC — Construção transacional dos marts a partir de refined

ESCOPO
- Ler somente de ``refined`` e escrever somente em ``marts``. Isso preserva
  raw e refined como fontes/etapas anteriores do pipeline.
- Apagar e recriar ``marts`` a cada execução. Assim, tabelas cujo SQL foi
  removido não permanecem no banco.
- Neste repositório, ``pipeline.transformacao`` produz duas tabelas refined;
  validar ambas antes de alterar marts evita executar sobre uma transformação
  incompleta.

UM ARQUIVO, UMA TABELA
- Ler os arquivos ``sql/marts/*.sql`` em ordem alfabética e criar uma tabela
  com o nome do arquivo sem ``.sql`` e sem o prefixo de dois dígitos e ``_``.
  Isso mantém a ordem e o nome dos marts definidos pelos próprios arquivos.
- Remover somente espaços ao redor e um ponto e vírgula final do SQL. A regra
  de negócio deve permanecer inteiramente no arquivo .sql.

SAÍDA
- Reconfigurar stdout para UTF-8 e imprimir uma linha por mart com sua
  contagem consultada no banco e separador de milhar com ponto.
- Imprimir ao final o número de marts e o total de linhas para tornar o
  resultado da execução verificável.

ERROS E ATOMICIDADE
- Falta de qualquer tabela refined necessária, diretório sem SQL, prefixo
  inválido, nome de tabela duplicado, SQL inválido ou mart vazio encerra com
  código 1. Um mart vazio costuma indicar um JOIN sem correspondências e
  pode fazer um dashboard parecer inativo.
- Validar os nomes antes de executar SQL evita iniciar uma carga que não pode
  ser nomeada sem ambiguidade.
- Executar a substituição inteira em uma transação. Se qualquer passo falhar,
  rollback restaura o schema marts da última execução bem-sucedida, evitando
  deixar o dashboard com um schema parcial.
"""

import re
import sys
from pathlib import Path

import duckdb

from pipeline.db import conectar

PASTA_SQL = Path(__file__).resolve().parent.parent / "sql" / "marts"
TABELAS_REFINED = (
    "exportacoes_brasil_cafe_torrado",
    "importacoes_paises_cafe_torrado",
)
PADRAO_ARQUIVO = re.compile(r"^\d{2}_(.+)\.sql$")


class FaltaTabelaRefined(Exception):
    """Uma das tabelas necessárias da transformação não existe."""


class ErroSQLMart(Exception):
    """Um arquivo SQL falhou ao criar ou contar seu mart."""

    def __init__(self, arquivo: Path, erro: duckdb.Error):
        self.arquivo = arquivo
        self.erro = erro


class MartVazio(Exception):
    """Um mart criado não contém linhas."""

    def __init__(self, arquivo: Path):
        self.arquivo = arquivo


def identificador(nome: str) -> str:
    return '"' + nome.replace('"', '""') + '"'


def formatar_numero(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def descobrir_arquivos() -> tuple[list[tuple[Path, str]], list[str]]:
    arquivos_sql = sorted(PASTA_SQL.glob("*.sql"), key=lambda caminho: caminho.name)
    if not arquivos_sql:
        return [], []

    invalidos = []
    candidatos = []
    for arquivo in arquivos_sql:
        correspondencia = PADRAO_ARQUIVO.fullmatch(arquivo.name)
        if correspondencia is None:
            invalidos.append(arquivo.name)
        else:
            candidatos.append((arquivo, correspondencia.group(1)))

    por_nome: dict[str, list[str]] = {}
    for arquivo, nome_tabela in candidatos:
        por_nome.setdefault(nome_tabela.casefold(), []).append(arquivo.name)

    duplicados = [
        f"{', '.join(nomes)} -> {nomes[0][3:-4]}"
        for nomes in por_nome.values()
        if len(nomes) > 1
    ]
    return candidatos, invalidos + duplicados


def validar_tabelas_refined(con: duckdb.DuckDBPyConnection) -> None:
    existentes = {
        linha[0]
        for linha in con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'refined' AND table_type = 'BASE TABLE'"
        ).fetchall()
    }
    ausentes = [nome for nome in TABELAS_REFINED if nome not in existentes]
    if ausentes:
        raise FaltaTabelaRefined(
            "Tabelas ausentes em refined: "
            + ", ".join(f"refined.{nome}" for nome in ausentes)
            + ". Rode `uv run python -m pipeline.transformacao`."
        )


def criar_marts(
    con: duckdb.DuckDBPyConnection,
    arquivos: list[tuple[Path, str]],
) -> list[tuple[str, int]]:
    validar_tabelas_refined(con)
    con.execute("DROP SCHEMA IF EXISTS marts CASCADE")
    con.execute("CREATE SCHEMA marts")

    resultados = []
    for arquivo, nome_tabela in arquivos:
        try:
            consulta = arquivo.read_text(encoding="utf-8").strip()
            if consulta.endswith(";"):
                consulta = consulta[:-1].rstrip()
            con.execute(
                f"CREATE TABLE marts.{identificador(nome_tabela)} AS {consulta}"
            )
            total = con.execute(
                f"SELECT count(*) FROM marts.{identificador(nome_tabela)}"
            ).fetchone()[0]
        except duckdb.Error as erro:
            raise ErroSQLMart(arquivo, erro) from erro

        if total == 0:
            raise MartVazio(arquivo)
        resultados.append((nome_tabela, total))
    return resultados


def encerrar(mensagem: str) -> None:
    print(mensagem, file=sys.stderr)
    sys.exit(1)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    arquivos, problemas = descobrir_arquivos()
    if not arquivos and not problemas:
        encerrar(f"Nenhum arquivo .sql encontrado em {PASTA_SQL}.")
    if problemas:
        encerrar("Arquivos ou nomes de tabela inválidos: " + "; ".join(problemas))

    con = conectar()
    transacao_aberta = False
    try:
        con.execute("BEGIN TRANSACTION")
        transacao_aberta = True
        resultados = criar_marts(con, arquivos)
        con.execute("COMMIT")
        transacao_aberta = False
    except FaltaTabelaRefined as erro:
        if transacao_aberta:
            con.execute("ROLLBACK")
        encerrar(str(erro))
    except ErroSQLMart as erro:
        if transacao_aberta:
            con.execute("ROLLBACK")
        encerrar(f"Falha em {erro.arquivo.name}: {erro.erro}")
    except MartVazio as erro:
        if transacao_aberta:
            con.execute("ROLLBACK")
        encerrar(f"Mart vazio em {erro.arquivo.name}; execução cancelada.")
    except OSError as erro:
        if transacao_aberta:
            con.execute("ROLLBACK")
        encerrar(f"Não foi possível ler um arquivo SQL: {erro}")
    except duckdb.Error as erro:
        if transacao_aberta:
            con.execute("ROLLBACK")
        encerrar(f"Erro DuckDB ao construir os marts: {erro}")
    finally:
        con.close()

    total_linhas = 0
    for nome_tabela, total in resultados:
        total_linhas += total
        print(f"✓ marts.{nome_tabela:<28} {formatar_numero(total)} linhas")
    print(
        f"Total: {len(resultados)} marts, "
        f"{formatar_numero(total_linhas)} linhas"
    )


if __name__ == "__main__":
    main()
