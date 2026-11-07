import re
from datetime import datetime

import painel
import relatorio


def test_relatorio_tem_ids_fixos_um_cdn_e_saida_deterministica():
    dados = painel.ler()
    primeira_hora = datetime.fromisoformat("2026-10-25T14:03:00-03:00")
    segunda_hora = datetime.fromisoformat("2026-10-25T14:04:00-03:00")

    primeiro = relatorio.montar_html(dados, primeira_hora)
    segundo = relatorio.montar_html(dados, primeira_hora)
    proxima_execucao = relatorio.montar_html(dados, segunda_hora)

    def remover_rodape(texto: str) -> str:
        return re.sub(r"Dados de \d{2}/\d{2}/\d{4} \d{2}:\d{2}", "", texto)

    assert primeiro == segundo
    assert remover_rodape(primeiro) == remover_rodape(proxima_execucao)
    assert 'id="g01"' in primeiro
    assert 'id="g02"' in primeiro
    assert 'id="g03"' in primeiro
    assert 'id="g04"' in primeiro
    assert 'id="g05"' in primeiro
    assert 'id="g06"' in primeiro
    assert 'id="g07"' in primeiro
    assert primeiro.count("cdn.plot.ly") == 1
    assert "jan/2023 a dez/2023" in primeiro
    assert "Dados de 25/10/2026 14:03" in primeiro
    assert len(primeiro.encode("utf-8")) < 200 * 1024
