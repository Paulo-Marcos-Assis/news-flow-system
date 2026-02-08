# 📰 Setup do Fluxo de Notícias

Este documento descreve como configurar e executar o sistema completo de coleta, processamento e análise de notícias.

## 📋 Pré-requisitos

- Docker e Docker Compose
- Python 3.8+
- Git
- Acesso ao servidor Ollama (para processamento com LLM)

## 🏗️ Arquitetura do Sistema

O fluxo de notícias é composto por 3 módulos principais:

### 1. **Collector** (`collector/noticias/`)
Responsável por coletar notícias de portais configurados.

**Principais arquivos:**
- `main.py` - Script principal do coletor
- `crawler_configs.json` - Configurações dos portais a serem coletados
- `requirements.txt` - Dependências Python

### 2. **Processor** (`processor/noticias/`)
Processa as notícias coletadas, extraindo features e metadados.

**Principais arquivos:**
- `main.py` - Script principal do processador
- `extractor/feature_extractor.py` - Extração de features usando LLM
- `requirements.txt` - Dependências Python

### 3. **Post-Flow** (`post_flow/cross-reference-noticias/`)
Realiza análises e cruzamento de dados das notícias processadas.

**Principais arquivos:**
- `main.py` - Script principal de pós-processamento
- `requirements.txt` - Dependências Python

## 🚀 Como Executar

### Passo 1: Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```bash
# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=admin

# MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_USER=admin
MONGO_PASSWORD=admin
MONGO_DB=noticias

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Ollama (para processamento com LLM)
OLLAMA_HOST=https://ollama-dev.ceos.ufsc.br
OLLAMA_MODEL=gpt-oss:20b
```

### Passo 2: Iniciar Infraestrutura

```bash
# Subir todos os serviços (RabbitMQ, MongoDB, MinIO, etc)
docker compose up -d
```

### Passo 3: Executar o Fluxo Completo

#### 3.1 Coletar Notícias
```bash
cd collector/noticias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

#### 3.2 Processar Notícias
```bash
cd processor/noticias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

#### 3.3 Pós-Processamento
```bash
cd post_flow/cross-reference-noticias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Passo 4: Configurar Triggers (Opcional)

Para execução automática periódica:

```bash
cd triggers
python trigger-noticias.py
```

## 🔧 Configuração dos Portais

Edite `collector/noticias/crawler_configs.json` para adicionar/remover portais:

```json
{
  "portals": [
    {
      "name": "ndmais",
      "base_url": "https://ndmais.com.br",
      "sections": ["politica", "economia", "seguranca"],
      "enabled": true
    }
  ]
}
```

## 📊 Monitoramento

### RabbitMQ
- URL: http://localhost:15672
- Usuário: admin
- Senha: admin

### MongoDB Express
- URL: http://localhost:8081
- Usuário: admin
- Senha: admin

### MinIO
- URL: http://localhost:9000
- Usuário: minioadmin
- Senha: minioadmin

## 🐛 Troubleshooting

### Problema: Coletor não encontra notícias
**Solução:** Verifique se os seletores CSS em `crawler_configs.json` estão corretos para o portal.

### Problema: Processador falha ao conectar com Ollama
**Solução:** Verifique se `OLLAMA_HOST` está correto no `.env` e se o servidor está acessível.

### Problema: Filas RabbitMQ não processam
**Solução:** Verifique se os serviços estão rodando com `docker compose ps`.

## 📝 Logs

Logs são salvos em:
- `collector/noticias/logs/`
- `processor/noticias/logs/`
- `post_flow/cross-reference-noticias/logs/`

## 🔄 Fluxo de Dados

```
Portais de Notícias
        ↓
   [Collector]
        ↓
   RabbitMQ Queue
        ↓
   [Processor]
        ↓
   MongoDB + MinIO
        ↓
   [Post-Flow]
        ↓
   Análises e Relatórios
```

## 📦 Dependências Principais

- **beautifulsoup4** - Parsing HTML
- **requests** - HTTP requests
- **pika** - RabbitMQ client
- **pymongo** - MongoDB client
- **minio** - MinIO client
- **langchain-ollama** - LLM integration
- **sentry-sdk** - Error tracking

## 🆘 Suporte

Para dúvidas ou problemas, consulte a documentação completa no README.md principal.
