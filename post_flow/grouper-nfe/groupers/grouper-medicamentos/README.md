# Projeto i2e
---

Este projeto implementa um pipeline completo de processamento de dados, heurísticas e utilização de modelos de linguagem. O objetivo é testar diferentes metodologias com LLMs menores na desambiguação de descrições de medicamentos em itens de notas fiscais (NF-es), a partir da regra-ouro preparada por @lucas.souza.vieira, @myllena.correa, @g.v.heisler e outros, utilizando os registros de medicamentos e respectivas apresentações da Anvisa e do CEMED.
Justificativa/Contextualização: É necessário utilizar LLMs menores e livres em servidores da nuvem do SETIC para extrair e vincular informações de NF-es. Técnicas de ICT (few-shot, Chain-of-Thought, etc.) têm se mostrado um caminho promissor para melhorar o desempenho de LLMs menores em diversas aplicações.


## Pré-requisitos

- Python 3.10 ou superior.  
- Git instalado e configurado.    
- (Opcional) Jupyter Notebook para exploração de dados (notebooks/).  

---

## 1 - Clonar o Repositório
```bash
SSH: git clone git@codigos.ufsc.br:ceos/geral/linha-1-fraudes/banco-de-pre-os/i2e-extracao-de-informacao-inteligente.git  
HTTPS: git clone https://codigos.ufsc.br/ceos/geral/linha-1-fraudes/banco-de-pre-os/i2e-extracao-de-informacao-inteligente.git
cd i2e
```
---

## 2 - Criar e Ativar Ambiente Virtual

**No Linux/macOS:**
```bash  
python -m venv .venv  
source .venv/bin/activate
```
**No Windows:**
```bash  
python -m venv .venv  
.venv\Scripts\activate
```
---

## 3 - Instalar Dependências

**Usando pip padrão:**
```bash  
pip install -r requirements.txt
```
**Usando uv (gerenciador de ambientes e pacotes):** 
```bash 
uv pip install -r requirements.txt 
```
---

## 4 - Instalar o Projeto em Modo de Desenvolvimento

**Usando pip padrão:** 
```bash 
pip install -e .
```
**Usando uv (gerenciador de ambientes e pacotes):** 
```bash  
uv pip install -e .
```
---

## 5 - Executar o Pipeline Principal
```bash
python src/main.py
```
> Executa todo o fluxo do pipeline, do pré-processamento à geração de resultados.

---

## Estrutura do Projeto
```bash
/  
├─── data/                # Dados brutos e processados  
├─── notebooks/           # Notebooks para exploração,análise e testes  
├─── results/             # Resultados gerados pelas heurísticas e modelos  
├─── src/                 # Código-fonte do pipeline  
│    ├─── data_processing/ # Scripts de limpeza e pré-processamento  
│    ├─── evaluation/      # Scripts de avaliação  
│    ├─── heuristics/      # Lógicas de negócio  
│    ├─── llm_linking/     # Integração com modelos de linguagem  
│    ├─── utils/           # Funções utilitárias  
│    └─── main.py          # Ponto de entrada do pipeline  
├─── .gitignore  
├─── config.yaml          # Configuração principal  
├─── params.yaml          # Parâmetros de modelos e scripts  
├─── pyproject.toml       # Configuração do pacote  
└─── requirements.txt     # Dependências Python  
```
---

## Notas Adicionais

- Certifique-se de adicionar o conjunto de dados inicial em data/raw e conferir se as features são as esperadas em src/data_processing_data_cleaning.py
- Para explorar dados, utilize os notebooks em notebooks/.  
- Para ajustar parâmetros do pipeline, edite params.yaml.  
- Para alterar configurações gerais, edite config.yaml.
