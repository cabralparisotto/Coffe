# Comércio exterior de café torrado

Pipeline de dados e painel para explorar exportações brasileiras e importações
internacionais de café torrado não descafeinado. O projeto usa Python, DuckDB,
SQL, Streamlit e Plotly.

**Painel ao vivo:** [Abrir o app no Streamlit](https://cabralparisotto-coffe-app-lapdf9.streamlit.app/)

> **Importante:** os códigos NCM 09012100 e HS 090121 identificam café torrado
> não descafeinado. Neste projeto, são usados como proxy para estudar comércio
> de café especial, mas não identificam qualidade, certificação, pontuação,
> microlote ou uma categoria comercial de café especial.

## O que o projeto faz

O pipeline separa os dados em três schemas DuckDB:

1. **`raw`** — cópia das colunas dos CSVs de entrada, sem inferir tipos ou
   transformar os dados. As colunas são carregadas como texto; campos vazios
   são nulos.
2. **`refined`** — duas tabelas tipadas, validadas e preparadas para análise:
   - `refined.exportacoes_brasil_cafe_torrado`
   - `refined.importacoes_paises_cafe_torrado`
3. **`marts`** — tabelas analíticas criadas pelos arquivos SQL em
   `sql/marts/`. Cada arquivo gera uma tabela; o prefixo numérico organiza a
   ordem de execução e não faz parte do nome da tabela.

O painel Streamlit lê os marts em modo somente leitura e apresenta oito
indicadores, sete gráficos e um filtro de período. O relatório HTML reutiliza
as mesmas funções de leitura, formatação e gráficos.

## Dados de entrada

Os CSVs ficam em `data/raw/`:

- `tabela_1_exportacoes_brasil_cafe_torrado_500plus.csv` — exportações
  brasileiras mensais, de 2015 a 2024, detalhadas por país de destino e UF.
- `tabela_2_importacoes_paises_cafe_torrado_500plus.csv` — importações
  mensais de 2023 reportadas por países parceiros Mundo.

Os arquivos desta pasta foram copiados sem alterações da fonte original. Mais
detalhes estão em [`data/raw/README.md`](data/raw/README.md). O pipeline trabalha
com as cópias locais: a ingestão e a transformação não baixam dados da internet.

Se os CSVs não estiverem disponíveis no clone, coloque os dois arquivos na
pasta `data/raw/` com os nomes acima antes de rodar o pipeline.

## Requisitos

- Python 3.13 ou superior
- [uv](https://docs.astral.sh/uv/)

As dependências de execução — DuckDB, pandas, Plotly e Streamlit — e as
dependências de desenvolvimento estão declaradas em `pyproject.toml` e
travadas em `uv.lock`.

## Instalação

Na raiz do repositório:

```bash
uv sync
```

## Executar o pipeline

Rode as etapas na ordem abaixo:

```bash
uv run python -m pipeline.ingestao
uv run python -m pipeline.transformacao
uv run python -m pipeline.marts
```

### 1. Ingestão

`pipeline.ingestao` lê os CSVs de `data/raw/` e recria as tabelas
`raw.tabela_1_exportacoes` e `raw.tabela_2_importacoes`. A saída mostra a
contagem de linhas gravadas.

### 2. Transformação

`pipeline.transformacao` valida os arquivos e as tabelas `raw`, converte os
tipos usando DuckDB e cria ou substitui as duas tabelas de `refined`. A etapa
remove somente duplicatas integralmente idênticas e encerra com erro se houver
conflitos de chave, falhas de conversão ou violações das regras de negócio.
Ela requer que os CSVs originais continuem em `data/raw/` e que cada arquivo
tenha pelo menos 500 linhas e 10 colunas.

### 3. Marts

`pipeline.marts` lê os arquivos `sql/marts/*.sql` em ordem alfabética e recria
o schema `marts` dentro de uma transação. Se uma consulta falhar ou produzir
uma tabela vazia, a transação é revertida e a execução termina com código de
erro.

| Arquivo SQL | Tabela criada | Conteúdo |
|---|---|---|
| `01_exportacao_mensal_Brasil.sql` | `marts.exportacao_mensal_Brasil` | Indicadores mensais das exportações brasileiras |
| `02_detalhamento_pais_destino.sql` | `marts.detalhamento_pais_destino` | Exportações mensais por país de destino |
| `03_quanto_os_paises_importam.sql` | `marts.quanto_os_paises_importam` | Indicadores mensais das importações reportadas |
| `04_paises_mais_compram_torrado.sql` | `marts.paises_mais_compram_torrado` | Importações mensais por país relator |
| `05_ranking_compram.sql` | `marts.ranking_compram` | Ranking mensal dos destinos brasileiros |
| `06_comparacao_importacao_exportacao.sql` | `marts.comparacao_importacao_exportacao` | Comparação mensal de valores e volumes |
| `07_kpis_mensais.sql` | `marts.kpis_mensais` | Valores, pesos, países e preços médios mensais usados nos cartões e no gráfico de preços |

As regras analíticas ficam nos arquivos SQL. Para alterar uma regra ou criar
uma análise nova, edite ou adicione um arquivo SQL numerado e rode novamente
`uv run python -m pipeline.marts`.

## Abrir o painel

Depois de gerar os marts:

```bash
uv run streamlit run app.py
```

O Streamlit mostrará o endereço local do painel no terminal. O filtro inicia
em janeiro a dezembro de 2023. Os cartões e os gráficos por país mostram o mês
final selecionado; as séries temporais mostram o intervalo. Os dados de
exportação vão até 2024, enquanto os dados de importação disponíveis neste
conjunto cobrem 2023.

O painel lê `cafe.duckdb` em modo somente leitura para permitir que os marts
sejam atualizados sem manter uma conexão de escrita aberta.

## Gerar o relatório HTML

```bash
uv run python relatorio.py
```

O comando cria ou substitui `relatorio.html` na raiz. O arquivo contém os
cartões e gráficos do período padrão do painel e informa o horário de geração.
Os gráficos usam Plotly via CDN; abrir o relatório requer acesso à internet
para carregar a biblioteca Plotly.

## Interface do DuckDB (opcional)

O projeto também contém uma interface local de exploração do DuckDB:

```bash
uv run python ui.py
```

O módulo informa o endereço local quando a interface inicia. Encerre com
`Ctrl+C` para fechar a conexão.

## Testes

```bash
uv run pytest
```

Para executar com cobertura:

```bash
uv run pytest --cov
```

## Estrutura relevante

```text
data/raw/       CSVs de entrada
pipeline/       ingestão, transformação e criação dos marts
sql/marts/      consultas SQL que definem cada mart
app.py          aplicação Streamlit
painel.py       leitura, formatação e funções de gráficos reutilizáveis
relatorio.py    geração do relatório HTML estático
ui.py           interface local de exploração do DuckDB
cafe.duckdb     banco DuckDB do projeto, na raiz
```
