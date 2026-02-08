# InserterUpdater - Serviço de Inserção e Atualização de Dados

## Visão Geral

O **InserterUpdater** é um serviço de processamento de dados que consome mensagens de uma fila (RabbitMQ), processa dados estruturados de licitações e contratos, e persiste as informações em dois bancos de dados:
- **PostgreSQL**: Banco relacional para dados estruturados
- **OrientDB**: Banco de grafos para relacionamentos e histórico de fontes

## Funcionalidades Principais

### 1. **Inserção Inteligente**
- Insere novos registros no PostgreSQL
- Respeita ordem de dependências entre tabelas (FKs)
- Suporta estruturas aninhadas (parent-child)

### 2. **Complementação de Dados**
- Quando um registro duplicado é detectado (mesma chave de identificação)
- Completa automaticamente campos NULL com novos valores
- Preserva dados existentes (não sobrescreve)
- Permite enriquecimento progressivo de dados de múltiplas fontes

### 3. **Persistência Dual**
- **PostgreSQL**: Dados estruturados e normalizados
- **OrientDB**: Grafo de relacionamentos + histórico de fontes

### 4. **Rastreamento de Operações**
- Retorna detalhes sobre inserções e atualizações realizadas
- Facilita auditoria e monitoramento

## Arquitetura

```
┌─────────────┐
│  RabbitMQ   │
│   (Fila)    │
└──────┬──────┘
       │ Mensagem JSON
       ▼
┌─────────────────────────────┐
│    InserterUpdater          │
│  ┌─────────────────────┐    │
│  │ 1. Validação        │    │
│  │ 2. Conversão Datas  │    │
│  │ 3. Verificação Dup. │    │
│  │ 4. Insert/Update    │    │
│  └─────────────────────┘    │
└──────┬──────────────┬───────┘
       │              │
       ▼              ▼
┌────────────┐  ┌──────────┐
│ PostgreSQL │  │ OrientDB │
│ (Relacional)│  │  (Grafo) │
└────────────┘  └──────────┘
```

## Formato de Entrada

### Estrutura Básica

```json
{
  "raw_data_id": "uuid-ou-identificador",
  "data_source": "NOME_DA_FONTE",
  "tabela_principal": {
    "campo1": "valor1",
    "campo2": "valor2"
  },
  "tabela_relacionada": {
    "campo_a": "valor_a",
    "campo_b": "valor_b"
  }
}
```

### Campos Obrigatórios

- **`raw_data_id`**: Identificador único do dado bruto original
- **`data_source`**: Nome da fonte de dados (ex: "PNCP", "PORTAL_TRANSPARENCIA", "TCE")
- **Tabelas**: Uma ou mais tabelas do modelo de dados

### Exemplo Completo

```json
{
  "raw_data_id": "abc123-def456",
  "data_source": "PNCP",
  "modalidade_licitacao": {
    "nome": "Pregão Eletrônico",
    "codigo": "PE"
  },
  "ente": {
    "nome": "Prefeitura Municipal de São Paulo",
    "cnpj": "12345678000190",
    "esfera": "MUNICIPAL"
  },
  "unidade_gestora": {
    "nome": "Secretaria de Educação",
    "codigo": "SEC-EDU-001"
  },
  "processo_licitatorio": {
    "numero": "2024/001",
    "objeto": "Aquisição de equipamentos de informática",
    "situacao": "EM_ANDAMENTO",
    "valor_estimado": 150000.00,
    "data_abertura": "2024-11-20"
  },
  "documento": {
    "numero": "DOC-2024-001",
    "tipo": "EDITAL",
    "data_publicacao": "2024-11-15"
  }
}
```

### Estruturas Aninhadas (Parent-Child)

```json
{
  "raw_data_id": "xyz789",
  "data_source": "PORTAL_TRANSPARENCIA",
  "processo_licitatorio": {
    "numero": "2024/002",
    "objeto": "Contratação de serviços",
    "item_licitacao": [
      {
        "descricao": "Item 1",
        "quantidade": 10,
        "valor_unitario": 100.00
      },
      {
        "descricao": "Item 2",
        "quantidade": 5,
        "valor_unitario": 200.00
      }
    ]
  }
}
```

### Formatos de Data Aceitos

O serviço converte automaticamente os seguintes formatos:
- `YYYY-MM-DDTHH:MM:SS` (ISO 8601)
- `DD/MM/YYYY`
- `DD-MM-YYYY`

Todos são convertidos para `YYYY-MM-DD` (formato PostgreSQL).

### Uso de ID como Referência

**Nova funcionalidade**: Você pode fornecer explicitamente o `id_*` (chave primária) de uma tabela para usá-lo como **referência** ao invés de tentar inserir um novo registro.

#### Como Funciona

Quando você fornece um campo `id_*` nos dados:
1. O sistema **detecta** que o ID foi fornecido
2. **Busca** o registro existente usando esse ID
3. **Retorna** o ID como referência (sem inserir ou atualizar)
4. **Usa** esse ID automaticamente para chaves estrangeiras em outras tabelas

#### Exemplo: Relacionar com Dados Existentes

```json
{
  "ente": {
    "id_ente": 6
  },
  "convenio": {
    "numero": "2024/001",
    "valor": 100000.00
  }
}
```

**Comportamento**:
- `ente`: ID 6 é usado como referência (não insere)
- `convenio`: Novo registro é inserido com `id_ente=6` como FK

**Saída**:
```json
{
  "data": {
    "insert": {
      "convenio": 42
    },
    "update": {}
  },
  "inserted_ids": {
    "ente": 6,
    "convenio": 42
  }
}
```

#### Casos de Uso

1. **Criar relacionamentos com dados existentes**: Quando você conhece o ID de uma entidade e quer criar novos registros relacionados
2. **Evitar duplicação**: Previne erro "duplicate key value violates unique constraint"
3. **Múltiplas referências**: Pode fornecer IDs de várias tabelas simultaneamente

**Documentação completa**: Ver `EXEMPLO_REFERENCIA_ID.md`

## Formato de Saída

### Estrutura Completa

```json
{
  "data": {
    "insert": {
      "tabela1": id_inserido,
      "tabela2": id_inserido
    },
    "update": {
      "tabela3": {
        "id": id_existente,
        "campo_atualizado1": "novo_valor1",
        "campo_atualizado2": "novo_valor2"
      }
    }
  },
  "inserted_ids": {
    "tabela1": id,
    "tabela2": id,
    "tabela3": id
  }
}
```

### Campos de Saída

#### `data.insert`
- **Tipo**: `dict`
- **Conteúdo**: `{nome_tabela: id_inserido}`
- **Significado**: Novos registros criados no PostgreSQL

#### `data.update`
- **Tipo**: `dict`
- **Conteúdo**: `{nome_tabela: {id: X, campo1: valor1, ...}}`
- **Significado**: Registros existentes que tiveram campos NULL completados
- **Campos incluídos**: Apenas os campos que foram atualizados + `id`

#### `inserted_ids`
- **Tipo**: `dict`
- **Conteúdo**: Todos os IDs do PostgreSQL processados (insert ou update)
- **Uso**: Compatibilidade com código legado

### Exemplos de Saída

#### Cenário 1: Apenas Inserções

**Entrada**: Dados completamente novos

**Saída**:
```json
{
  "data": {
    "insert": {
      "modalidade_licitacao": 52,
      "ente": 310,
      "unidade_gestora": 96,
      "processo_licitatorio": 7800,
      "documento": 11087
    },
    "update": {}
  },
  "inserted_ids": {
    "modalidade_licitacao": 52,
    "ente": 310,
    "unidade_gestora": 96,
    "processo_licitatorio": 7800,
    "documento": 11087
  }
}
```

#### Cenário 2: Inserção + Atualização

**Entrada**: Modalidade nova + Processo existente com campos NULL

**Saída**:
```json
{
  "data": {
    "insert": {
      "modalidade_licitacao": 52
    },
    "update": {
      "processo_licitatorio": {
        "id": 7799,
        "situacao": "HOMOLOGADA",
        "data_homologacao": "2024-11-19",
        "valor_homologado": 145000.00
      }
    }
  },
  "inserted_ids": {
    "modalidade_licitacao": 52,
    "processo_licitatorio": 7799
  }
}
```

#### Cenário 3: Apenas Atualização

**Entrada**: Todos os registros já existem, apenas completando campos NULL

**Saída**:
```json
{
  "data": {
    "insert": {},
    "update": {
      "processo_licitatorio": {
        "id": 7799,
        "valor_estimado": 150000.00
      },
      "documento": {
        "id": 11087,
        "data_publicacao": "2024-11-15",
        "url": "https://exemplo.com/doc.pdf"
      }
    }
  },
  "inserted_ids": {
    "processo_licitatorio": 7799,
    "documento": 11087
  }
}
```

#### Cenário 4: Duplicado sem Atualizações

**Entrada**: Registro já existe e todos os campos estão preenchidos

**Saída**:
```json
{
  "data": {
    "insert": {},
    "update": {}
  },
  "inserted_ids": {
    "processo_licitatorio": 7799
  }
}
```

**Nota**: Mesmo sem inserção ou atualização no PostgreSQL, o dado é enviado ao OrientDB para manter histórico de fontes (dados do OrientDB não são retornados na resposta).

## Configuração

### Variáveis de Ambiente

#### PostgreSQL
```bash
DATABASE_PG=nome_do_banco
USERNAME_PG=usuario
SENHA_PG=senha
HOST_PG=localhost
PORT_PG=5432
```

#### OrientDB
```bash
HOST_ORIENT=localhost
PORT_ORIENT=2424
USERNAME_ORIENT=admin
SENHA_ORIENT=admin
DATABASE_ORIENT=ceos_graph
```

#### RabbitMQ
```bash
QUEUE_MANAGER=rabbitmq
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
```

#### Banco de Dados Relacional
```bash
RELATIONAL_STORAGE=postgresql  # Padrão
```

## Arquivos de Configuração

### `db_identifiers/`

- **`fks.json`**: Mapeamento de Foreign Keys entre tabelas
- **`insert_order.json`**: Ordem de inserção das tabelas (respeita dependências)
- **`identifiers.json`**: Campos identificadores únicos por tabela (para detectar duplicatas)

### Exemplo `identifiers.json`
```json
{
  "processo_licitatorio": ["numero", "id_ente"],
  "documento": ["numero", "tipo"],
  "ente": ["cnpj"]
}
```

## Fluxo de Processamento

1. **Recebimento**: Mensagem chega via RabbitMQ
2. **Conversão**: Datas são convertidas para formato padrão
3. **Validação**: Estrutura é validada
4. **Processamento por Tabela** (seguindo `insert_order.json`):
   - Verifica se registro já existe (via `identifiers.json`)
   - **Se não existe**: INSERT no PostgreSQL
   - **Se existe**: UPDATE apenas campos NULL
   - Envia para OrientDB (sempre)
5. **Relacionamentos**: Cria edges no OrientDB entre vértices relacionados
6. **Commit**: Transação é confirmada
7. **Notificação**: Publica resultado em exchange topic
8. **Retorno**: Estrutura com detalhes de insert/update

## Logs

### Níveis de Log

- **INFO**: Operações normais (insert, update, conexões)
- **WARNING**: Situações inesperadas mas não críticas
- **ERROR**: Erros que impedem processamento

### Exemplos de Logs

```
[INFO] Inserção da tabela: processo_licitatorio
[INFO] [OK] Registro já existente na tabela 'processo_licitatorio' com ID: 7799
[INFO] [UPDATE] Tabela: processo_licitatorio, ID: 7799, Campos atualizados: 2
[INFO] [OrientDB] Enviado para o Orient (existente) -> id=7799, raw=abc123, table=processo_licitatorio
[INFO] [OrientDB] Adição de relacionamento processo_licitatorio: #50:999 --related_to--> ente: #46:456
```

## Tratamento de Erros

### Reconexão Automática
- Se a conexão com PostgreSQL cair, tenta reconectar automaticamente
- Se falhar, aborta o processamento da mensagem

### Rollback
- Em caso de erro durante processamento, toda a transação é revertida
- Mensagem volta para a fila para reprocessamento

### Validação
- Campos obrigatórios são verificados
- Tipos de dados são validados
- FKs são resolvidas automaticamente

## Uso

### Iniciar o Serviço

```bash
cd inserter-updater
python main.py
```

### Enviar Mensagem de Teste

```python
import json
from service_essentials.queue_manager.queue_manager_factory import QueueManagerFactory

queue_manager = QueueManagerFactory.get_queue_manager()
queue_manager.connect()

mensagem = {
    "raw_data_id": "test-123",
    "data_source": "TESTE",
    "processo_licitatorio": {
        "numero": "2024/999",
        "objeto": "Teste de inserção"
    }
}

queue_manager.publish_message("inserter_updater_queue", json.dumps(mensagem))
```

## Documentação Adicional

- **`COMPLEMENTACAO_DADOS.md`**: Detalhes sobre complementação de dados de múltiplas fontes
- **`EXEMPLO_SAIDA.md`**: Exemplos detalhados de saídas em diferentes cenários

## Dependências

```
psycopg2
pika (RabbitMQ)
pyorient (OrientDB)
```

Veja `requirements.txt` para versões específicas.
