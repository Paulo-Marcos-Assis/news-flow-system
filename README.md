# ceos-data-ingestion

## Funcionamento

### Ferramentas
- Gerenciamento das Triggers: localhost:1337
- RabbitMQ: localhost:15672
  - Usuário: admin
  - Senha: admin
- PGadmin: localhost:5050
  - Usuário: admin@admin.com
  - Senha: admin
- Mongo Express: localhost:8081
  - Usuário: admin
  - Senha: admin
- Orientdb Studio: localhost:2480
  - Usuário: root
  - Senha: admin
- Minio: localhost:9000
  - Usuário: minioadmin
  - Senha: minioadmin

Ao parar o main-server, os bancos de dados são mantidos. É importante não forçar o parada do container, e dar `docker compose down` para parar os containers.

### Banco de Dados

#### PostgreSQL

O banco PostgreSQL é inicializado automaticamente com o schema completo através do arquivo `service_essentials/postgres_manager/seed.sql`.

**Conexão via pgAdmin:**
1. Acesse `http://localhost:5050`
2. Login: `admin@admin.com` / `admin`
3. Adicione um novo servidor:
   - **Nome**: Local PostgreSQL (ou qualquer nome)
   - **Host**: `postgresql`
   - **Port**: `5432`
   - **Database**: `local`
   - **Username**: `admin`
   - **Password**: `admin`

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

Exemplo de microserviços:
```
  coletor-x:
    build: coletor/x
    <<: *dados-comuns
    environment:
      INPUT_QUEUE: "coleta_x"
      OUTPUT_QUEUE: "lista_x"
      ERROR_QUEUE: "erro_coletor_x"

  splitter-x:
    build: splitter/x
    <<: *dados-comuns
    environment:
      INPUT_QUEUE: "lista_x"
      OUTPUT_QUEUE: "licitacao_bruta_x"
      ERROR_QUEUE: "erro_splitter_x"
``` 
Note que a fila de output do primeiro serviço é o input do segundo. Desta maneira, uma ordem é mantida.

Neste caso, x substitui a fonte. O nome poderia ser coletor-pncp, coletor-dom, [...]. De acordo com o esboço do fluxo, algumas filas são compartilhadas entre as diferentes fontes.

### Triggers

Existem triggers implementados ([`trigger-dom.py`](triggers/trigger-dom.py) e [`trigger-pncp.py`](triggers/trigger-pncp.py)) para teste do sistema.

## Como rodar

### Pre Requisitos
- [ ] Terminal Linux
- [ ] GIT
- [ ] Docker (com plugin docker compose)


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
1. Copie um dos microserviços que ja existe sempre mantendo a estrutura de arquivo `tipo/item`, exemplo `coletor/dom`.
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

### Acessando o painel de filas

```
http://localhost:15672/
```
As credenciais de acesso estão no arquivo [`.env`](.env).