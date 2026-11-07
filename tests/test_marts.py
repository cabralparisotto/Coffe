import duckdb
import pytest

from pipeline import marts


class SaidaCapturada:
    def __init__(self):
        self.conteudo = ""
        self.encoding = None

    def reconfigure(self, *, encoding):
        self.encoding = encoding

    def write(self, texto):
        self.conteudo += texto
        return len(texto)

    def flush(self):
        pass


def capturar_saida(monkeypatch):
    stdout = SaidaCapturada()
    stderr = SaidaCapturada()
    monkeypatch.setattr(marts.sys, "stdout", stdout)
    monkeypatch.setattr(marts.sys, "stderr", stderr)
    return stdout, stderr


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


def test_descobrir_arquivos_lista_prefixo_invalido_e_colisoes(tmp_path, monkeypatch):
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


def test_descobrir_arquivos_vazio_devolve_listas_vazias(tmp_path, monkeypatch):
    monkeypatch.setattr(marts, "PASTA_SQL", tmp_path)

    assert marts.descobrir_arquivos() == ([], [])


def test_validar_tabelas_refined_lista_as_ausentes():
    con = duckdb.connect(":memory:")

    with pytest.raises(marts.FaltaTabelaRefined) as erro:
        marts.validar_tabelas_refined(con)

    assert "refined.exportacoes_brasil_cafe_torrado" in str(erro.value)
    assert "refined.importacoes_paises_cafe_torrado" in str(erro.value)
    con.close()


def test_criar_marts_remove_um_ponto_e_virgula_final(tmp_path):
    arquivo = tmp_path / "00_teste.sql"
    arquivo.write_text("SELECT 1 AS x;   ", encoding="utf-8")
    con = criar_conexao()

    resultado = executar_transacao(con, [(arquivo, "teste")])

    assert resultado == [("teste", 1)]
    assert con.execute("SELECT x FROM marts.teste").fetchone() == (1,)
    con.close()


def test_main_sem_arquivos_sql_encerra_antes_de_conectar(tmp_path, monkeypatch):
    monkeypatch.setattr(marts, "PASTA_SQL", tmp_path)
    monkeypatch.setattr(
        marts,
        "conectar",
        lambda: pytest.fail("não deve conectar sem arquivos SQL"),
    )
    stdout, stderr = capturar_saida(monkeypatch)

    with pytest.raises(SystemExit) as erro:
        marts.main()

    assert erro.value.code == 1
    assert stdout.encoding == "utf-8"
    assert "Nenhum arquivo .sql" in stderr.conteudo


def test_main_nome_invalido_encerra_antes_de_conectar(tmp_path, monkeypatch):
    monkeypatch.setattr(marts, "PASTA_SQL", tmp_path)
    (tmp_path / "sem_prefixo.sql").write_text("SELECT 1", encoding="utf-8")
    monkeypatch.setattr(
        marts,
        "conectar",
        lambda: pytest.fail("não deve conectar com nome inválido"),
    )
    _, stderr = capturar_saida(monkeypatch)

    with pytest.raises(SystemExit) as erro:
        marts.main()

    assert erro.value.code == 1
    assert "sem_prefixo.sql" in stderr.conteudo


def test_main_sem_tabelas_refined_preserva_erro_e_fecha_conexao(tmp_path, monkeypatch):
    arquivo_sql = tmp_path / "sql"
    arquivo_sql.mkdir()
    (arquivo_sql / "01_teste.sql").write_text("SELECT 1", encoding="utf-8")
    banco = tmp_path / "teste.duckdb"
    monkeypatch.setattr(marts, "PASTA_SQL", arquivo_sql)
    monkeypatch.setattr(marts, "conectar", lambda: duckdb.connect(str(banco)))
    _, stderr = capturar_saida(monkeypatch)

    with pytest.raises(SystemExit) as erro:
        marts.main()

    assert erro.value.code == 1
    assert "uv run python -m pipeline.transformacao" in stderr.conteudo
    con = duckdb.connect(str(banco), read_only=True)
    assert con.execute(
        "SELECT count(*) FROM information_schema.schemata WHERE schema_name = 'marts'"
    ).fetchone() == (0,)
    con.close()


def test_main_cria_marts_e_imprime_contagens(tmp_path, monkeypatch):
    pasta_sql = tmp_path / "sql"
    pasta_sql.mkdir()
    (pasta_sql / "01_um.sql").write_text("SELECT 1 AS x", encoding="utf-8")
    (pasta_sql / "02_dois.sql").write_text(
        "SELECT 1 AS x UNION ALL SELECT 2 AS x", encoding="utf-8"
    )
    banco = tmp_path / "teste.duckdb"
    con = duckdb.connect(str(banco))
    con.execute("CREATE SCHEMA refined")
    for nome in marts.TABELAS_REFINED:
        con.execute(f'CREATE TABLE refined."{nome}" (x INTEGER)')
    con.close()
    monkeypatch.setattr(marts, "PASTA_SQL", pasta_sql)
    monkeypatch.setattr(marts, "conectar", lambda: duckdb.connect(str(banco)))
    stdout, _ = capturar_saida(monkeypatch)

    marts.main()

    assert stdout.encoding == "utf-8"
    assert "✓ marts.um" in stdout.conteudo
    assert "1 linhas" in stdout.conteudo
    assert "✓ marts.dois" in stdout.conteudo
    assert "2 linhas" in stdout.conteudo
    assert "Total: 2 marts, 3 linhas" in stdout.conteudo
    con = duckdb.connect(str(banco), read_only=True)
    assert con.execute("SELECT count(*) FROM marts.dois").fetchone() == (2,)
    con.close()


def test_main_erro_sql_informa_arquivo_e_reverte_schema(tmp_path, monkeypatch):
    pasta_sql = tmp_path / "sql"
    pasta_sql.mkdir()
    (pasta_sql / "01_quebrado.sql").write_text("SELECT FROM", encoding="utf-8")
    banco = tmp_path / "teste.duckdb"
    con = duckdb.connect(str(banco))
    con.execute("CREATE SCHEMA refined")
    for nome in marts.TABELAS_REFINED:
        con.execute(f'CREATE TABLE refined."{nome}" (x INTEGER)')
    con.execute("CREATE SCHEMA marts")
    con.execute("CREATE TABLE marts.anterior AS SELECT 42 AS resposta")
    con.close()
    monkeypatch.setattr(marts, "PASTA_SQL", pasta_sql)
    monkeypatch.setattr(marts, "conectar", lambda: duckdb.connect(str(banco)))
    _, stderr = capturar_saida(monkeypatch)

    with pytest.raises(SystemExit) as erro:
        marts.main()

    assert erro.value.code == 1
    assert "01_quebrado.sql" in stderr.conteudo
    con = duckdb.connect(str(banco), read_only=True)
    assert con.execute("SELECT resposta FROM marts.anterior").fetchone() == (42,)
    con.close()


def test_main_mart_vazio_reverte_schema(tmp_path, monkeypatch):
    pasta_sql = tmp_path / "sql"
    pasta_sql.mkdir()
    (pasta_sql / "01_vazio.sql").write_text(
        "SELECT 1 AS x WHERE false", encoding="utf-8"
    )
    banco = tmp_path / "teste.duckdb"
    con = duckdb.connect(str(banco))
    con.execute("CREATE SCHEMA refined")
    for nome in marts.TABELAS_REFINED:
        con.execute(f'CREATE TABLE refined."{nome}" (x INTEGER)')
    con.execute("CREATE SCHEMA marts")
    con.execute("CREATE TABLE marts.anterior AS SELECT 42 AS resposta")
    con.close()
    monkeypatch.setattr(marts, "PASTA_SQL", pasta_sql)
    monkeypatch.setattr(marts, "conectar", lambda: duckdb.connect(str(banco)))
    _, stderr = capturar_saida(monkeypatch)

    with pytest.raises(SystemExit) as erro:
        marts.main()

    assert erro.value.code == 1
    assert "Mart vazio em 01_vazio.sql" in stderr.conteudo
    con = duckdb.connect(str(banco), read_only=True)
    assert con.execute("SELECT resposta FROM marts.anterior").fetchone() == (42,)
    con.close()


def test_main_falha_ao_ler_sql_reverte_schema(tmp_path, monkeypatch):
    pasta_sql = tmp_path / "sql"
    pasta_sql.mkdir()
    (pasta_sql / "01_diretorio.sql").mkdir()
    banco = tmp_path / "teste.duckdb"
    con = duckdb.connect(str(banco))
    con.execute("CREATE SCHEMA refined")
    for nome in marts.TABELAS_REFINED:
        con.execute(f'CREATE TABLE refined."{nome}" (x INTEGER)')
    con.execute("CREATE SCHEMA marts")
    con.execute("CREATE TABLE marts.anterior AS SELECT 42 AS resposta")
    con.close()
    monkeypatch.setattr(marts, "PASTA_SQL", pasta_sql)
    monkeypatch.setattr(marts, "conectar", lambda: duckdb.connect(str(banco)))
    _, stderr = capturar_saida(monkeypatch)

    with pytest.raises(SystemExit) as erro:
        marts.main()

    assert erro.value.code == 1
    assert "Não foi possível ler um arquivo SQL" in stderr.conteudo
    con = duckdb.connect(str(banco), read_only=True)
    assert con.execute("SELECT resposta FROM marts.anterior").fetchone() == (42,)
    con.close()


def test_main_informa_erro_generico_de_transacao_duckdb(monkeypatch):
    con = duckdb.connect(":memory:")
    con.execute("BEGIN TRANSACTION")
    monkeypatch.setattr(marts, "descobrir_arquivos", lambda: ([(None, "x")], []))
    monkeypatch.setattr(marts, "conectar", lambda: con)
    _, stderr = capturar_saida(monkeypatch)

    with pytest.raises(SystemExit) as erro:
        marts.main()

    assert erro.value.code == 1
    assert "Erro DuckDB ao construir os marts" in stderr.conteudo
