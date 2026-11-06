"""SPEC — Pipeline raw → refined para comércio de café torrado

CONTEXTO
Estou construindo um pipeline de dados em Python sobre duas tabelas públicas de
comércio exterior relacionadas a café torrado. Trabalho com spec-driven
development: esta especificação é a fonte da verdade e o código é consequência
dela. Não acrescente requisitos que não estejam escritos aqui. Se algo estiver
ambíguo, pergunte antes de escrever código.

O código HS/NCM utilizado é 090121/09012100, definido como café torrado, não
descafeinado. Esse código é um proxy comercial de café especial. A classificação
aduaneira não identifica diretamente qualidade specialty, certificação,
pontuação, microlote ou origem específica.

STACK
- Python 3.13.
- Dependências gerenciadas com uv.
- DuckDB.
- Arquivo do banco: cafe.duckdb na raiz do projeto.
- Nenhum orquestrador.
- Script executável pela linha de comando.
- Entrada em arquivos CSV UTF-8.
- O separador dos arquivos gerados é vírgula.
- O primeiro arquivo possui BOM UTF-8; a leitura deve aceitar UTF-8-SIG.

ARQUIVOS DE ENTRADA
Os arquivos devem estar em data/raw/ com estes nomes:
1. tabela_1_exportacoes_brasil_cafe_torrado_500plus.csv
2. tabela_2_importacoes_paises_cafe_torrado_500plus.csv

As tabelas originais também existem em:
- /home/ubuntu/coffee_specialty_500/tabela_1_exportacoes_brasil_cafe_torrado_500plus.csv
- /home/ubuntu/coffee_specialty_500/tabela_2_importacoes_paises_cafe_torrado_500plus.csv

O pipeline deve trabalhar com os arquivos copiados para data/raw/, não com
URLs e não com chamadas online durante a transformação.

ARTEFATO A PRODUZIR
Criar pipeline/transformacao.py, executável com:

    uv run python -m pipeline.transformacao

O script deve:
- ler as duas tabelas do schema raw;
- escrever somente no schema refined;
- nunca escrever em raw;
- usar SQL DuckDB para conversões, validações e criação das tabelas;
- não carregar o CSV inteiro em estruturas Python para fazer a transformação.

Se pipeline/db.py já existir e expuser uma função de conexão, reutilize-a. Caso
ela ainda não exista, não invente uma arquitetura diferente sem perguntar.

1. INGESTÃO RAW
Antes da transformação, devem existir estas duas tabelas no schema raw:
- raw.tabela_1_exportacoes
- raw.tabela_2_importacoes

Todas as colunas de raw devem ser VARCHAR. Campos vazios devem ser armazenados
como NULL. Os nomes das colunas devem ser preservados exatamente como aparecem
nos CSVs.

A Tabela 1 deve conter, no mínimo, estas 14 colunas:

    coNcm
    year
    monthNumber
    country
    state
    ncm
    metricFOB
    metricKG
    metricStatistic
    source
    flow
    period_from
    period_to
    query_ncm

A Tabela 2 deve conter, no mínimo, estas 52 colunas:

    typeCode
    freqCode
    refPeriodId
    refYear
    refMonth
    period
    reporterCode
    reporterISO
    reporterDesc
    flowCode
    flowDesc
    partnerCode
    partnerISO
    partnerDesc
    partner2Code
    partner2ISO
    partner2Desc
    classificationCode
    classificationSearchCode
    isOriginalClassification
    cmdCode
    cmdDesc
    aggrLevel
    isLeaf
    customsCode
    customsDesc
    mosCode
    motCode
    motDesc
    qtyUnitCode
    qtyUnitAbbr
    qty
    isQtyEstimated
    altQtyUnitCode
    altQtyUnitAbbr
    altQty
    isAltQtyEstimated
    netWgt
    isNetWgtEstimated
    grossWgt
    isGrossWgtEstimated
    cifvalue
    fobvalue
    primaryValue
    legacyEstimationFlag
    isReported
    isAggregate
    source
    query_hs
    query_flow
    query_partner
    query_year

Se uma coluna obrigatória não existir, o script deve informar o arquivo, a
coluna ausente e encerrar com sys.exit(1).

2. SAÍDA REFINED
Criar ou substituir estas duas tabelas:
- refined.exportacoes_brasil_cafe_torrado
- refined.importacoes_paises_cafe_torrado

A execução deve usar CREATE OR REPLACE TABLE. Nunca fazer INSERT incremental.
Executar o script dez vezes deve produzir o mesmo resultado da primeira
execução.

3. REFINED DA TABELA 1
A tabela refined.exportacoes_brasil_cafe_torrado deve ter estas colunas e tipos:

Coluna                  Tipo             Regra
ncm                     VARCHAR          Copiar coNcm; deve ser 09012100
ano                     INTEGER          Converter year
mes                     INTEGER          Converter monthNumber
pais_destino            VARCHAR          Copiar country
uf_origem               VARCHAR          Copiar state
produto                 VARCHAR          Copiar ncm
valor_fob_usd           DECIMAL(18,2)    Converter metricFOB
peso_kg                 DECIMAL(18,3)    Converter metricKG
quantidade_estatistica  DECIMAL(18,3)    Converter metricStatistic
fonte                   VARCHAR          Copiar source
fluxo                   VARCHAR          Copiar flow
periodo_inicio          DATE             Converter period_from, formato %Y-%m
periodo_fim             DATE             Converter period_to, formato %Y-%m
ncm_consulta             VARCHAR          Copiar query_ncm

A granularidade da tabela 1 é uma linha por combinação de:

    ncm, ano, mes, pais_destino, uf_origem

Não agregar, resumir, pivotar ou eliminar linhas durante a transformação.

4. REFINED DA TABELA 2
A tabela refined.importacoes_paises_cafe_torrado deve preservar os campos
comerciais originais e criar nomes refinados em português para os campos usados
na análise.

As colunas refinadas devem ser:

Coluna                              Tipo             Origem
tipo_registro                       VARCHAR          typeCode
frequencia                          VARCHAR          freqCode
periodo_id                          BIGINT           refPeriodId
ano                                 INTEGER          refYear
mes                                 INTEGER          refMonth
periodo                             VARCHAR          period
pais_relator_codigo                 INTEGER          reporterCode
pais_relator_iso                    VARCHAR          reporterISO
pais_relator                        VARCHAR          reporterDesc
fluxo                               VARCHAR          flowCode
parceiro_codigo                     INTEGER          partnerCode
parceiro_iso                        VARCHAR          partnerISO
parceiro                            VARCHAR          partnerDesc
codigo_produto_hs                   VARCHAR          cmdCode
descricao_produto                   VARCHAR          cmdDesc
classificacao                       VARCHAR          classificationCode
classificacao_busca                 VARCHAR          classificationSearchCode
aduana                              VARCHAR          customsCode
modo_transporte_codigo              INTEGER          motCode
unidade_quantidade_codigo           INTEGER          qtyUnitCode
quantidade                          DECIMAL(18,3)    qty
quantidade_alternativa              DECIMAL(18,3)    altQty
peso_liquido_kg                     DECIMAL(18,3)    netWgt
peso_bruto_kg                       DECIMAL(18,3)    grossWgt
valor_cif_usd                       DECIMAL(18,2)    cifvalue
valor_fob_usd                       DECIMAL(18,2)    fobvalue
valor_principal_usd                 DECIMAL(18,2)    primaryValue
quantidade_estimada                 BOOLEAN          isQtyEstimated
quantidade_alternativa_estimada     BOOLEAN          isAltQtyEstimated
peso_liquido_estimado               BOOLEAN          isNetWgtEstimated
peso_bruto_estimado                 BOOLEAN          isGrossWgtEstimated
registro_reportado                  BOOLEAN          isReported
registro_agregado                   BOOLEAN          isAggregate
fonte                               VARCHAR          source
hs_consulta                         VARCHAR          query_hs
fluxo_consulta                      VARCHAR          query_flow
parceiro_consulta                   VARCHAR          query_partner
ano_consulta                        INTEGER          query_year

As colunas abaixo também devem ser preservadas com seus nomes originais, pois
fazem parte do retorno bruto da API e não devem ser descartadas:

    partner2Code
    partner2ISO
    partner2Desc
    aggrLevel
    isLeaf
    mosCode
    qtyUnitAbbr
    altQtyUnitCode
    altQtyUnitAbbr
    legacyEstimationFlag

Para essas colunas preservadas sem uso analítico imediato, manter VARCHAR,
exceto quando o conteúdo for inequivocamente inteiro ou booleano conforme o
nome original.

A granularidade da tabela 2 é uma linha por combinação de:

    periodo, pais_relator_codigo, parceiro_codigo, codigo_produto_hs

Como a consulta foi feita com parceiro Mundo e HS 090121, o resultado esperado
é:

    fluxo = M
    parceiro_codigo = 0
    codigo_produto_hs = 090121
    ano = 2023

Não agregar, resumir, pivotar ou eliminar linhas durante a transformação.

5. TIPOS E CONVERSÕES
As conversões devem ser realizadas pelo DuckDB em SQL, não por conversão linha a
linha em Python. Use CAST e strptime/strptime(...)::DATE para conversões. Não
use TRY_CAST, try_strptime ou qualquer conversão que transforme erro em nulo.

Tipos obrigatórios:
- códigos de produto, país e identificadores que possam ter zeros à esquerda:
  VARCHAR;
- anos, meses e códigos numéricos sem risco de zero à esquerda: INTEGER;
- periodo_id: BIGINT;
- valores monetários: DECIMAL(18,2);
- pesos e quantidades: DECIMAL(18,3);
- indicadores is..., isReported e isAggregate: BOOLEAN;
- periodo_inicio e periodo_fim: DATE.

A conversão de period_from e period_to deve acrescentar o primeiro dia do mês
antes de converter, por exemplo 2015-01 vira 2015-01-01.

A conversão de period da Tabela 2 não deve ser transformada em data sem que isso
esteja explicitamente solicitado; preservar period como VARCHAR e manter ano e
mes como inteiros.

6. CONVERSÃO QUE FALHA
Se qualquer conversão falhar, parar tudo e usar sys.exit(1).

A mensagem de erro deve informar:
- tabela de origem;
- coluna de origem;
- tipo de destino;
- um exemplo do valor inválido;
- a quantidade de valores inválidos, se disponível.

Não substituir o valor inválido por NULL, zero, string vazia ou valor padrão.

7. NULOS
Nenhuma linha deve ser apagada por conter nulo. Nenhum nulo deve ser
preenchido. Nulos em descrições, ISO, valores comerciais ou campos estimados
devem permanecer nulos. Não preencher nomes de países, descrições de produtos
ou códigos ISO por consulta externa.

A Tabela 2 possui campos de descrição e ISO que podem estar nulos no retorno da
API; isso é esperado e deve ser preservado.

8. DUPLICATAS
Para a Tabela 1, a chave lógica é:

    ncm, ano, mes, pais_destino, uf_origem

Para a Tabela 2, a chave lógica é:

    periodo, pais_relator_codigo, parceiro_codigo, codigo_produto_hs

Antes de criar as tabelas refined:
1. contar linhas inteiramente repetidas;
2. manter apenas uma cópia de cada linha inteiramente repetida;
3. informar quantas linhas repetidas foram removidas;
4. verificar se uma mesma chave lógica possui conteúdos diferentes;
5. em caso de chave repetida com conteúdo diferente, parar, mostrar a chave e
   as linhas conflitantes e executar sys.exit(1).

Não escolher silenciosamente uma linha conflitante.

Se não houver duplicatas, informar zero. A transformação não deve criar
agregações para resolver duplicidade.

9. VALIDAÇÕES DE NEGÓCIO
As validações abaixo devem falhar com mensagem clara:
- Tabela 1: ncm deve ser 09012100 em todas as linhas não nulas.
- Tabela 1: fluxo deve ser export em todas as linhas não nulas.
- Tabela 2: codigo_produto_hs deve ser 090121 em todas as linhas não nulas.
- Tabela 2: fluxo deve ser M em todas as linhas não nulas.
- Tabela 2: parceiro_codigo deve ser 0 em todas as linhas não nulas.
- Tabela 2: ano deve ser 2023 em todas as linhas não nulas.
- nenhuma linha deve ser removida apenas por falhar uma regra de negócio;
  regra de negócio inválida encerra a execução.

10. SAÍDA NA TELA
Imprimir uma linha por tabela no formato:

    refined.exportacoes_brasil_cafe_torrado  10.870 -> 10.870 linhas (0 duplicatas)
    refined.importacoes_paises_cafe_torrado     588 ->    588 linhas (0 duplicatas)

Os números devem usar ponto como separador de milhar.

Abaixo de cada tabela, imprimir as colunas que possuem nulos e suas contagens:

    nulos mantidos: pais_destino 0, uf_origem 0

Não imprimir colunas sem nulos. As contagens devem vir do banco DuckDB, não de
contadores mantidos apenas em Python.

Imprimir ao final:

    Total: 11.458 linhas

Configurar stdout para UTF-8.

REEXECUÇÃO
Usar CREATE OR REPLACE TABLE. Nunca fazer append. Rodar o script duas vezes
seguidas deve produzir exatamente as mesmas tabelas, contagens, tipos e saída
na tela.

ERROS DE PRÉ-CONDIÇÃO
Antes de transformar, verificar:
- existência dos arquivos CSV;
- existência das tabelas raw;
- presença de todas as colunas obrigatórias;
- quantidade mínima de 500 linhas em cada CSV raw;
- quantidade mínima de 10 colunas em cada CSV raw.

Se alguma pré-condição falhar, informar precisamente o problema e executar
sys.exit(1).

CRITÉRIOS DE ACEITE
- Existem duas tabelas em refined.
- refined.exportacoes_brasil_cafe_torrado possui 10.870 linhas na versão
  fornecida e 14 colunas refinadas.
- refined.importacoes_paises_cafe_torrado possui 588 linhas na versão fornecida
  e pelo menos 10 colunas.
- A transformação não elimina linhas por nulo.
- Todas as linhas de entrada são preservadas, exceto duplicatas inteiramente
  repetidas, se existirem.
- Valores monetários são DECIMAL(18,2).
- Pesos e quantidades são DECIMAL(18,3).
- Códigos de produto permanecem como texto, preservando zeros à esquerda.
- A Tabela 1 permanece mensal e detalhada por país de destino e UF de origem.
- A Tabela 2 permanece mensal e detalhada por país relator.
- O código de produto não é reinterpretado como categoria de qualidade
  specialty.
- Executar duas vezes produz a mesma saída.

ENTREGA, NESTA ORDEM
1. Coloque esta especificação integral como docstring no topo de
   pipeline/transformacao.py.
2. Implemente o código de transformação abaixo da docstring.
3. Inclua comentários somente quando a decisão não for óbvia pelo código.
4. Ao final da execução, mostre as validações realizadas.
5. Liste explicitamente qualquer decisão assumida que não esteja nesta spec.
   Se a lista não estiver vazia, pare antes de implementar e peça
   esclarecimento.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import duckdb

from pipeline.db import PASTA_RAW, conectar, criar_schema

ARQUIVOS = {
    "raw.tabela_1_exportacoes": (
        "tabela_1_exportacoes_brasil_cafe_torrado_500plus.csv",
        "refined.exportacoes_brasil_cafe_torrado",
    ),
    "raw.tabela_2_importacoes": (
        "tabela_2_importacoes_paises_cafe_torrado_500plus.csv",
        "refined.importacoes_paises_cafe_torrado",
    ),
}

MAPEAMENTOS = {
    "raw.tabela_1_exportacoes": (
        ("coNcm", "ncm", "VARCHAR"),
        ("year", "ano", "INTEGER"),
        ("monthNumber", "mes", "INTEGER"),
        ("country", "pais_destino", "VARCHAR"),
        ("state", "uf_origem", "VARCHAR"),
        ("ncm", "produto", "VARCHAR"),
        ("metricFOB", "valor_fob_usd", "DECIMAL(18,2)"),
        ("metricKG", "peso_kg", "DECIMAL(18,3)"),
        ("metricStatistic", "quantidade_estatistica", "DECIMAL(18,3)"),
        ("source", "fonte", "VARCHAR"),
        ("flow", "fluxo", "VARCHAR"),
        ("period_from", "periodo_inicio", "DATE_MONTH"),
        ("period_to", "periodo_fim", "DATE_MONTH"),
        ("query_ncm", "ncm_consulta", "VARCHAR"),
    ),
    "raw.tabela_2_importacoes": (
        ("typeCode", "tipo_registro", "VARCHAR"),
        ("freqCode", "frequencia", "VARCHAR"),
        ("refPeriodId", "periodo_id", "BIGINT"),
        ("refYear", "ano", "INTEGER"),
        ("refMonth", "mes", "INTEGER"),
        ("period", "periodo", "VARCHAR"),
        ("reporterCode", "pais_relator_codigo", "INTEGER"),
        ("reporterISO", "pais_relator_iso", "VARCHAR"),
        ("reporterDesc", "pais_relator", "VARCHAR"),
        ("flowCode", "fluxo", "VARCHAR"),
        ("partnerCode", "parceiro_codigo", "INTEGER"),
        ("partnerISO", "parceiro_iso", "VARCHAR"),
        ("partnerDesc", "parceiro", "VARCHAR"),
        ("cmdCode", "codigo_produto_hs", "VARCHAR"),
        ("cmdDesc", "descricao_produto", "VARCHAR"),
        ("classificationCode", "classificacao", "VARCHAR"),
        ("classificationSearchCode", "classificacao_busca", "VARCHAR"),
        ("customsCode", "aduana", "VARCHAR"),
        ("motCode", "modo_transporte_codigo", "INTEGER"),
        ("qtyUnitCode", "unidade_quantidade_codigo", "INTEGER"),
        ("qty", "quantidade", "DECIMAL(18,3)"),
        ("altQty", "quantidade_alternativa", "DECIMAL(18,3)"),
        ("netWgt", "peso_liquido_kg", "DECIMAL(18,3)"),
        ("grossWgt", "peso_bruto_kg", "DECIMAL(18,3)"),
        ("cifvalue", "valor_cif_usd", "DECIMAL(18,2)"),
        ("fobvalue", "valor_fob_usd", "DECIMAL(18,2)"),
        ("primaryValue", "valor_principal_usd", "DECIMAL(18,2)"),
        ("isQtyEstimated", "quantidade_estimada", "BOOLEAN"),
        ("isAltQtyEstimated", "quantidade_alternativa_estimada", "BOOLEAN"),
        ("isNetWgtEstimated", "peso_liquido_estimado", "BOOLEAN"),
        ("isGrossWgtEstimated", "peso_bruto_estimado", "BOOLEAN"),
        ("isReported", "registro_reportado", "BOOLEAN"),
        ("isAggregate", "registro_agregado", "BOOLEAN"),
        ("source", "fonte", "VARCHAR"),
        ("query_hs", "hs_consulta", "VARCHAR"),
        ("query_flow", "fluxo_consulta", "VARCHAR"),
        ("query_partner", "parceiro_consulta", "VARCHAR"),
        ("query_year", "ano_consulta", "INTEGER"),
        ("partner2Code", "partner2Code", "VARCHAR"),
        ("partner2ISO", "partner2ISO", "VARCHAR"),
        ("partner2Desc", "partner2Desc", "VARCHAR"),
        ("aggrLevel", "aggrLevel", "INTEGER"),
        ("isLeaf", "isLeaf", "BOOLEAN"),
        ("mosCode", "mosCode", "INTEGER"),
        ("qtyUnitAbbr", "qtyUnitAbbr", "VARCHAR"),
        ("altQtyUnitCode", "altQtyUnitCode", "INTEGER"),
        ("altQtyUnitAbbr", "altQtyUnitAbbr", "VARCHAR"),
        ("legacyEstimationFlag", "legacyEstimationFlag", "INTEGER"),
    ),
}

CHAVES = {
    "raw.tabela_1_exportacoes": (
        "ncm",
        "ano",
        "mes",
        "pais_destino",
        "uf_origem",
    ),
    "raw.tabela_2_importacoes": (
        "periodo",
        "pais_relator_codigo",
        "parceiro_codigo",
        "codigo_produto_hs",
    ),
}


def identificador(nome: str) -> str:
    return '"' + nome.replace('"', '""') + '"'


def tabela_sql(nome: str) -> str:
    return ".".join(identificador(parte) for parte in nome.split("."))


def formatar_numero(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def expressao_conversao(coluna: str, tipo: str) -> str:
    coluna_sql = identificador(coluna)
    if tipo == "DATE_MONTH":
        return f"strptime({coluna_sql} || '-01', '%Y-%m-%d')::DATE"
    return f"CAST({coluna_sql} AS {tipo})"


def encerrar(mensagem: str) -> None:
    print(mensagem, file=sys.stderr)
    sys.exit(1)


def ler_descricao_csv(con: duckdb.DuckDBPyConnection, caminho: Path):
    caminho_sql = "'" + str(caminho).replace("'", "''") + "'"
    fonte = (
        f"read_csv({caminho_sql}, header=true, all_varchar=true, "
        "encoding='utf-8', delim=',')"
    )
    try:
        colunas = con.execute(f"DESCRIBE SELECT * FROM {fonte}").fetchall()
        linhas = con.execute(f"SELECT count(*) FROM {fonte}").fetchone()[0]
    except duckdb.Error as erro:
        encerrar(f"Não foi possível validar o CSV {caminho}: {erro}")
    return colunas, linhas


def validar_pre_condicoes(con: duckdb.DuckDBPyConnection) -> None:
    ausentes = [
        arquivo
        for arquivo, _ in ARQUIVOS.values()
        if not (PASTA_RAW / arquivo).is_file()
    ]
    if ausentes:
        encerrar(
            "Arquivos CSV ausentes em "
            f"{PASTA_RAW}: {', '.join(ausentes)}. Rode a ingestão após "
            "restaurar os arquivos de entrada."
        )

    for origem, (arquivo, _) in ARQUIVOS.items():
        existe = con.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema = 'raw' AND table_name = ?",
            [origem.split(".", 1)[1]],
        ).fetchone()[0]
        if not existe:
            encerrar(
                f"Tabela {origem} ausente. Rode `uv run python -m "
                "pipeline.ingestao` antes da transformação."
            )

        caminho = PASTA_RAW / arquivo
        colunas_csv, linhas_csv = ler_descricao_csv(con, caminho)
        nomes_csv = [linha[0] for linha in colunas_csv]
        if len(nomes_csv) < 10:
            encerrar(
                f"Arquivo {arquivo} tem {len(nomes_csv)} colunas; "
                "o mínimo exigido é 10."
            )
        if linhas_csv < 500:
            encerrar(
                f"Arquivo {arquivo} tem {linhas_csv} linhas; "
                "o mínimo exigido é 500."
            )

        colunas_raw = con.execute(
            f"DESCRIBE SELECT * FROM {tabela_sql(origem)}"
        ).fetchall()
        nomes_raw = [linha[0] for linha in colunas_raw]
        faltantes_csv = [
            coluna
            for coluna, _, _ in MAPEAMENTOS[origem]
            if coluna not in nomes_csv
        ]
        faltantes_raw = [
            coluna
            for coluna, _, _ in MAPEAMENTOS[origem]
            if coluna not in nomes_raw
        ]
        for coluna in faltantes_csv:
            encerrar(f"Arquivo {arquivo}: coluna obrigatória ausente: {coluna}.")
        for coluna in faltantes_raw:
            encerrar(
                f"Tabela {origem}: coluna obrigatória ausente: {coluna} "
                f"(arquivo correspondente: {arquivo})."
            )
        tipos_nao_texto = [
            f"{nome}: {tipo}"
            for nome, tipo, *_ in colunas_raw
            if tipo.upper() != "VARCHAR"
        ]
        if tipos_nao_texto:
            encerrar(
                f"Tabela {origem} contém colunas que não são VARCHAR: "
                + ", ".join(tipos_nao_texto)
            )


def validar_conversoes(
    con: duckdb.DuckDBPyConnection, origem: str
) -> None:
    for coluna, _, tipo in MAPEAMENTOS[origem]:
        if tipo == "VARCHAR":
            continue
        expressao = expressao_conversao(coluna, tipo)
        try:
            con.execute(
                f"SELECT count({expressao}) FROM {tabela_sql(origem)} "
                f"WHERE {identificador(coluna)} IS NOT NULL"
            ).fetchone()
        except duckdb.Error as erro:
            mensagem = str(erro)
            exemplo = re.search(r"string '([^']*)'", mensagem)
            valor = exemplo.group(1) if exemplo else mensagem
            encerrar(
                f"Falha de conversão em {origem}, coluna {coluna}, "
                f"destino {tipo.replace('_MONTH', '')}; exemplo inválido: "
                f"{valor}. Quantidade de valores inválidos não disponível "
                f"(CAST interrompe na primeira falha). Erro DuckDB: {mensagem}"
            )


def criar_tabela_temporaria(
    con: duckdb.DuckDBPyConnection, origem: str, indice: int
) -> tuple[str, int, int]:
    nome_dedup = f"_raw_sem_duplicatas_{indice}"
    nome_stage = f"_refined_stage_{indice}"
    con.execute(
        f"CREATE TEMP TABLE {identificador(nome_dedup)} AS "
        f"SELECT DISTINCT * FROM {tabela_sql(origem)}"
    )
    total_origem = con.execute(
        f"SELECT count(*) FROM {tabela_sql(origem)}"
    ).fetchone()[0]
    total_dedup = con.execute(
        f"SELECT count(*) FROM {identificador(nome_dedup)}"
    ).fetchone()[0]
    colunas_select = []
    for coluna, nome_novo, tipo in MAPEAMENTOS[origem]:
        colunas_select.append(
            f"{expressao_conversao(coluna, tipo)} AS {identificador(nome_novo)}"
        )
    con.execute(
        f"CREATE TEMP TABLE {identificador(nome_stage)} AS "
        f"SELECT {', '.join(colunas_select)} "
        f"FROM {identificador(nome_dedup)}"
    )
    return nome_stage, total_origem, total_origem - total_dedup


def validar_chaves(
    con: duckdb.DuckDBPyConnection, origem: str, nome_stage: str
) -> None:
    chaves = CHAVES[origem]
    colunas_chave = ", ".join(identificador(coluna) for coluna in chaves)
    conflitos = con.execute(
        f"SELECT {colunas_chave}, count(*) AS ocorrencias "
        f"FROM {identificador(nome_stage)} GROUP BY {colunas_chave} "
        "HAVING count(*) > 1"
    ).fetchall()
    if not conflitos:
        return

    print(
        f"Chaves lógicas conflitantes em {origem}: "
        f"{len(conflitos)} grupo(s).",
        file=sys.stderr,
    )
    for conflito in conflitos:
        chave = conflito[:-1]
        print(
            "Chave: "
            + ", ".join(
                f"{coluna}={valor!r}"
                for coluna, valor in zip(chaves, chave, strict=True)
            ),
            file=sys.stderr,
        )
        condicao = " AND ".join(
            f"{identificador(coluna)} IS NOT DISTINCT FROM ?"
            for coluna in chaves
        )
        linhas = con.execute(
            f"SELECT * FROM {identificador(nome_stage)} WHERE {condicao}",
            list(chave),
        ).fetchall()
        nomes_colunas = [
            item[0]
            for item in con.execute(
                f"DESCRIBE SELECT * FROM {identificador(nome_stage)}"
            ).fetchall()
        ]
        for linha in linhas:
            print(dict(zip(nomes_colunas, linha, strict=True)), file=sys.stderr)
    sys.exit(1)


def validar_regra(
    con: duckdb.DuckDBPyConnection,
    origem: str,
    nome_stage: str,
    coluna: str,
    operador: str,
    esperado,
) -> None:
    divergentes, exemplo = con.execute(
        f"SELECT count(*), first({identificador(coluna)}) "
        f"FROM {identificador(nome_stage)} "
        f"WHERE {identificador(coluna)} IS NOT NULL "
        f"AND NOT ({identificador(coluna)} {operador} ?)",
        [esperado],
    ).fetchone()
    if divergentes:
        encerrar(
            f"Validação de negócio falhou em {origem}: {coluna} deveria "
            f"ser {esperado!r}; {divergentes} valor(es) divergente(s), "
            f"exemplo: {exemplo!r}."
        )


def validar_regras_de_negocio(
    con: duckdb.DuckDBPyConnection, origem: str, nome_stage: str
) -> None:
    regras = {
        "raw.tabela_1_exportacoes": (
            ("ncm", "=", "09012100"),
            ("fluxo", "=", "export"),
        ),
        "raw.tabela_2_importacoes": (
            ("codigo_produto_hs", "=", "090121"),
            ("fluxo", "=", "M"),
            ("parceiro_codigo", "=", 0),
            ("ano", "=", 2023),
        ),
    }
    for coluna, operador, esperado in regras[origem]:
        validar_regra(
            con, origem, nome_stage, coluna, operador, esperado
        )


def contagem_nulos(
    con: duckdb.DuckDBPyConnection, tabela: str
) -> list[tuple[str, int]]:
    descricao = con.execute(
        f"DESCRIBE SELECT * FROM {tabela_sql(tabela)}"
    ).fetchall()
    expressao = ", ".join(
        f"count(*) FILTER (WHERE {identificador(linha[0])} IS NULL)"
        for linha in descricao
    )
    contagens = con.execute(
        f"SELECT {expressao} FROM {tabela_sql(tabela)}"
    ).fetchone()
    return [
        (linha[0], quantidade)
        for linha, quantidade in zip(descricao, contagens, strict=True)
        if quantidade
    ]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    con = conectar()
    transacao_aberta = False
    try:
        validar_pre_condicoes(con)
        con.execute("BEGIN TRANSACTION")
        transacao_aberta = True
        etapas = {}
        for indice, origem in enumerate(ARQUIVOS, start=1):
            validar_conversoes(con, origem)
            nome_stage, total_origem, duplicatas = criar_tabela_temporaria(
                con, origem, indice
            )
            validar_chaves(con, origem, nome_stage)
            validar_regras_de_negocio(con, origem, nome_stage)
            etapas[origem] = (nome_stage, total_origem, duplicatas)

        criar_schema(con, "refined")
        for origem, (_, tabela_refined) in ARQUIVOS.items():
            nome_stage, _, _ = etapas[origem]
            con.execute(
                f"CREATE OR REPLACE TABLE {tabela_sql(tabela_refined)} "
                f"AS SELECT * FROM {identificador(nome_stage)}"
            )
        con.execute("COMMIT")
        transacao_aberta = False

        total_refined = 0
        for origem, (_, tabela_refined) in ARQUIVOS.items():
            _, total_origem, duplicatas = etapas[origem]
            total_saida = con.execute(
                f"SELECT count(*) FROM {tabela_sql(tabela_refined)}"
            ).fetchone()[0]
            total_refined += total_saida
            linha = (
                f"{tabela_refined} {formatar_numero(total_origem):>7} -> "
                f"{formatar_numero(total_saida):>7} linhas "
                f"({formatar_numero(duplicatas)} duplicatas)"
            )
            print(linha)
            nulos = contagem_nulos(con, tabela_refined)
            if nulos:
                detalhes = ", ".join(
                    f"{coluna} {formatar_numero(contagem)}"
                    for coluna, contagem in nulos
                )
                print(f"    nulos mantidos: {detalhes}")

        print(f"Total: {formatar_numero(total_refined)} linhas")
        print("Validações realizadas:")
        print("- arquivos, tabelas, colunas e mínimos de linhas/colunas: OK")
        print("- colunas raw VARCHAR e conversões SQL: OK")
        print("- duplicatas completas removidas e chaves lógicas sem conflito: OK")
        print("- regras de negócio das duas tabelas: OK")
        print("- tabelas refined substituídas sem append: OK")
    except SystemExit:
        if transacao_aberta:
            con.execute("ROLLBACK")
        raise
    except duckdb.Error as erro:
        if transacao_aberta:
            con.execute("ROLLBACK")
        encerrar(f"Erro DuckDB durante a transformação: {erro}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
