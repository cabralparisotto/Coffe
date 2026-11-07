import duckdb
import pytest

from pipeline import marts


def criar_conexao() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(":memory:")
    con.execute("CREATE SCHEMA refined")
    for nome in marts.TABELAS_REFINED:
        con.execute(f'CREATE TABLE refined."{nome}" (x INTEGER)')
    return con


def executar_transacao(con, arquivos):
    con.execute("BEGIN TRANSACTION")
    try:
        resultado = marts.criar_marts(con, arquivos)
        con.execute("COMMIT")
        return resultado
    except Exception:
        con.execute("ROLLBACK")
        raise


def test_cria_mart_e_remove_tabela_de_arquivo_apagado(tmp_path, monkeypatch):
    monkeypatch.setattr(marts, "PASTA_SQL", tmp_path)
    teste = tmp_path / "00_teste.sql"
    outro = tmp_path / "01_outro.sql"
    teste.write_text("SELECT 1 AS x", encoding="utf-8")
    outro.write_text("SELECT 2 AS x", encoding="utf-8")
    con = criar_conexao()

    arquivos, problemas = marts.descobrir_arquivos()
    assert problemas == []
    assert executar_transacao(con, arquivos) == [("teste", 1), ("outro", 1)]
    assert con.execute("SELECT x FROM marts.teste").fetchone() == (1,)

    teste.unlink()
    arquivos, problemas = marts.descobrir_arquivos()
    assert problemas == []
    executar_transacao(con, arquivos)
    nomes = {
        linha[0]
        for linha in con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'marts'"
        ).fetchall()
    }
    assert nomes == {"outro"}
    con.close()


def test_sql_invalido_restaura_schema_anterior(tmp_path):
    arquivo = tmp_path / "00_quebrado.sql"
    arquivo.write_text("SELECT FROM", encoding="utf-8")
    con = criar_conexao()
    con.execute("CREATE SCHEMA marts")
    con.execute("CREATE TABLE marts.anterior AS SELECT 42 AS resposta")

    with pytest.raises(marts.ErroSQLMart) as erro:
        executar_transacao(con, [(arquivo, "quebrado")])

    assert erro.value.arquivo.name == "00_quebrado.sql"
    assert con.execute("SELECT resposta FROM marts.anterior").fetchone() == (42,)
    assert con.execute(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema = 'marts' AND table_name = 'quebrado'"
    ).fetchone() == (0,)
    con.close()


def test_mart_vazio_restaura_schema_anterior(tmp_path):
    arquivo = tmp_path / "00_vazio.sql"
    arquivo.write_text("SELECT 1 AS x WHERE false", encoding="utf-8")
    con = criar_conexao()
    con.execute("CREATE SCHEMA marts")
    con.execute("CREATE TABLE marts.anterior AS SELECT 42 AS resposta")

    with pytest.raises(marts.MartVazio):
        executar_transacao(con, [(arquivo, "vazio")])

    assert con.execute("SELECT resposta FROM marts.anterior").fetchone() == (42,)
    con.close()


def test_descobrir_arquivos_lista_prefixo_invalido_e_colisoes(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(marts, "PASTA_SQL", tmp_path)
    (tmp_path / "teste.sql").write_text("SELECT 1", encoding="utf-8")
    (tmp_path / "01_repetido.sql").write_text("SELECT 1", encoding="utf-8")
    (tmp_path / "02_repetido.sql").write_text("SELECT 1", encoding="utf-8")

    arquivos, problemas = marts.descobrir_arquivos()

    assert [arquivo.name for arquivo, _ in arquivos] == [
        "01_repetido.sql",
        "02_repetido.sql",
    ]
    assert problemas == [
        "teste.sql",
        "01_repetido.sql, 02_repetido.sql -> repetido",
    ]
