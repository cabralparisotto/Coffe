"""Interface do DuckDB para exploração local pelo navegador.

Spec:
- Abre ``olist.duckdb`` na raiz do projeto e instala/carrega a extensão ``ui``
  antes de executar ``CALL start_ui()``; isso fornece a exploração pelo
  navegador no endereço local esperado.
- Mantém o processo ativo enquanto a conexão serve a UI, imprime o endereço e
  a instrução de encerramento, e fecha a conexão ao receber Ctrl+C para
  liberar o lock antes de uma nova ingestão.
- Não cria banco: verificar a existência do arquivo antes de conectar evita
  que uma abertura acidental de banco vazio pareça uma ingestão concluída.
- Não depende do módulo de ingestão e reconfigura stdout para UTF-8 para exibir
  corretamente a instrução em terminais com encoding padrão diferente.
"""

import sys
import time
from pathlib import Path

import duckdb


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    caminho_banco = Path(__file__).resolve().parent / "olist.duckdb"
    if not caminho_banco.is_file():
        print(
            "O banco olist.duckdb não existe. É preciso rodar a ingestão antes.",
            file=sys.stderr,
        )
        sys.exit(1)

    con = duckdb.connect(str(caminho_banco))
    try:
        con.execute("INSTALL ui")
        con.execute("LOAD ui")
        con.execute("CALL start_ui()")
        print("Interface disponível em http://localhost:4213", flush=True)
        print("Ctrl+C para encerrar", flush=True)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        con.close()


if __name__ == "__main__":
    main()
