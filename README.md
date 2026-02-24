# ceos-data-ingestion

## Funcionamento

### Ferramentas
- Gerenciamento das Triggers: 
- RabbitMQ: localhost:15672
- PGadmin: localhost:5050
- Mongo Express: localhost:8081

- Orientdb Studio: localhost:2480

- Minio: localhost:9000


Ao parar o main-server, os bancos de dados são mantidos. É importante não forçar o parada do container, e dar `docker compose down` para parar os containers.

### Banco de Dados

#### PostgreSQL

O banco PostgreSQL é inicializado automaticamente com o schema completo através do arquivo `service_essentials/postgres_manager/seed.sql`.


**Conexão via terminal:**
```bash
docker compose exec postgresql psql -U admin -d local
```

**Resetar banco de dados:**
Se precisar recriar o banco do zero:
```bash
docker compose down
sudo rm -rf ./data/postgresql
docker compose up --build
```

### Microserviços

No arquivo [`docker-compose.yml`](docker-compose.yml) estão algumas configurações e também o esquema das filas de microserviços. 

### Triggers

### Primeira Execução
Pra rodar o projeto pela primeira vez deve-de criar a imagem base

```
docker compose build ceos-base
```

### Rodar o projeto

```
docker compose up 
```

### Adicionando um Microserviço
1. Copie um dos microserviços que ja existe sempre mantendo a estrutura de arquivo `tipo/item`, exemplo `coletor/`.
2. Personalize o `main.py` e `requirements.txt`. Caso necessite, o `Dockerfile` local tambem.
3. Adicione seu microserviço no `docker-compose.yml`, exemplo:
```
  tipo-item:
    build: tipo/item
    <<: *dados-comuns
    environment:
      INPUT_QUEUE: "coleta_item"
      OUTPUT_QUEUE: "lista_item"
      ERROR_QUEUE: "erro_tipo_item"
``` 

### Recompilando

```
docker compose up --build
```
