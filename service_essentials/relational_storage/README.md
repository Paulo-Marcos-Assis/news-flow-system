# Relational Storage Manager

Abstração para gerenciamento de bancos de dados relacionais seguindo os princípios SOLID:
- **Dependency Inversion Principle (DIP)**: Código depende de abstrações, não de implementações concretas
- **Dependency Injection**: Dependências são injetadas via Factory
- **Factory Pattern**: Criação de instâncias centralizada e configurável

## Estrutura

```
relational_storage/
├── __init__.py
├── relational_storage_manager.py          # Interface abstrata (ABC)
├── postgresql_manager.py                  # Implementação PostgreSQL
├── relational_storage_manager_factory.py  # Factory para criação de instâncias
└── README.md
```

## Uso

### 1. Configuração via Variável de Ambiente

```bash
export RELATIONAL_STORAGE=postgresql  # Padrão: postgresql
```

### 2. Uso no Código

```python
from service_essentials.relational_storage.relational_storage_manager_factory import RelationalStorageManagerFactory

# Obter instância via Factory (Dependency Injection)
db_manager = RelationalStorageManagerFactory.get_relational_storage_manager()

# Usar a abstração
cursor = db_manager.get_cursor(cursor_factory=RealDictCursor)
db_manager.commit()
db_manager.close_connection()
```

## Interface (RelationalStorageManager)

### Métodos Principais

- `connect(**kwargs)`: Conecta ao banco de dados
- `get_connection()`: Retorna a conexão ativa
- `get_cursor(**kwargs)`: Retorna um cursor para executar queries
- `execute_query(query, params, fetch)`: Executa uma query SQL
- `execute_many(query, params_list)`: Executa query em lote
- `commit()`: Confirma a transação
- `rollback()`: Reverte a transação
- `close_connection()`: Fecha a conexão
- `is_connected()`: Verifica se está conectado

## Implementações Disponíveis

### PostgreSQL (postgresql_manager.py)

Implementação para PostgreSQL usando `psycopg2`.

**Variáveis de Ambiente:**
- `DATABASE_PG`: Nome do banco de dados
- `USERNAME_PG`: Usuário
- `SENHA_PG`: Senha
- `HOST_PG`: Host
- `PORT_PG`: Porta

## Adicionar Novas Implementações

Para adicionar suporte a outros bancos (MySQL, SQLite, etc.):

1. Criar nova classe que herda de `RelationalStorageManager`
2. Implementar todos os métodos abstratos
3. Adicionar no Factory (`relational_storage_manager_factory.py`)

```python
# Exemplo: MySQL
if relational_storage_type == "mysql":
    from service_essentials.relational_storage.mysql_manager import MySQLManager
    return MySQLManager()
```

## Benefícios

- **Testabilidade**: Fácil criar mocks da interface
- **Manutenibilidade**: Mudanças isoladas em cada implementação
- **Extensibilidade**: Adicionar novos bancos sem modificar código existente
- **Flexibilidade**: Trocar implementação via variável de ambiente
