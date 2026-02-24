# PostgreSQL Manager

Este diretório contém scripts de inicialização e gerenciamento do PostgreSQL.

## Inicialização Automática

Os scripts SQL neste diretório são executados automaticamente pelo PostgreSQL na **primeira inicialização** do container, em ordem alfabética:

1. **`00-extensions.sql`** - Cria extensões necessárias (pgcrypto, pg_trgm)
2. **`seed.sql`** - Carrega dados iniciais (schemas, tabelas, dados de referência)

### ⚠️ Importante

Os scripts de inicialização **só são executados uma vez**, quando o banco de dados é criado pela primeira vez. Se você já tem dados em `./data/postgresql`, os scripts não serão executados novamente.

## Extensões PostgreSQL

### pg_trgm
- **Função**: Medição de similaridade de texto e busca por trigrams
- **Uso**: Função `similarity()` usada no quality-checker para matching de nomes de entes
- **Criação manual** (se necessário):
  ```sql
  CREATE EXTENSION IF NOT EXISTS pg_trgm;
  ```

### pgcrypto
- **Função**: Funções criptográficas
- **Uso**: Criptografia de dados sensíveis (CPF, etc.)

## Resetar o Banco de Dados

Para executar os scripts de inicialização novamente:

```bash
# 1. Parar os containers
docker compose down

# 2. Remover os dados persistidos
sudo rm -rf ./data/postgresql

# 3. Iniciar novamente (scripts serão executados)
docker compose up postgresql -d
```

## Arquivos Python

- **`postgres_base_client.py`** - Cliente base para conexão com PostgreSQL
- **`db_insert_functions.py`** - Funções auxiliares para inserção de dados
- **`helpers.py`** - Funções auxiliares gerais
