# Configuração Automática do pgAdmin

Esta pasta contém arquivos de configuração para que o pgAdmin carregue automaticamente o servidor PostgreSQL ao iniciar.

## Arquivos

### `servers.json`
Define os servidores PostgreSQL que serão carregados automaticamente no pgAdmin. Estrutura:

```json
{
  "Servers": {
    "1": {
      "Name": "PostgreSQL Local",
      "Group": "Servers",
      "Host": "postgresql",
      "Port": 5432,
      "MaintenanceDB": "local",
      "Username": "local",
      "SSLMode": "prefer",
      "Comment": "Banco de dados local do projeto"
    }
  }
}
```

**Campos importantes:**
- `Name`: Nome que aparecerá no pgAdmin
- `Host`: Nome do serviço Docker (deve corresponder ao nome no docker-compose.yml)
- `Port`: Porta interna do PostgreSQL (5432)
- `MaintenanceDB`: Database padrão para conexão
- `Username`: Usuário do PostgreSQL

### `pgpass`
Arquivo de senhas no formato PostgreSQL para autenticação automática:

```
hostname:port:database:username:password
```

Exemplo:
```
postgresql:5432:*:local:locallocallocal
```

O `*` no campo database significa que a senha será usada para qualquer database.

## Como Funciona

1. O `docker-compose.yml` monta esses arquivos no container do pgAdmin
2. A variável de ambiente `PGADMIN_SERVER_JSON_FILE` aponta para o `servers.json`
3. O entrypoint customizado copia o `pgpass` para o local correto e ajusta permissões
4. Ao acessar o pgAdmin (http://localhost:5050), o servidor já estará configurado
5. Ao clicar no servidor, a conexão será feita automaticamente sem pedir senha

## Credenciais de Acesso ao pgAdmin

- **URL**: http://localhost:5050
- **Email**: admin@admin.com
- **Senha**: admin

## Modificando a Configuração

### Adicionar Novo Servidor

Edite o `servers.json` e adicione uma nova entrada:

```json
{
  "Servers": {
    "1": { ... },
    "2": {
      "Name": "PostgreSQL Produção",
      "Host": "postgres-prod.example.com",
      ...
    }
  }
}
```

### Alterar Senha

Edite o arquivo `pgpass` seguindo o formato:
```
host:port:database:username:password
```

### Aplicar Mudanças

Após modificar os arquivos, reinicie o pgAdmin:

```bash
docker compose restart pgadmin
```

## Segurança

⚠️ **Importante**: O arquivo `pgpass` contém senhas em texto plano. 

- **Desenvolvimento local**: OK usar senhas simples
- **Produção**: Use secrets do Docker ou variáveis de ambiente criptografadas
- Nunca commite senhas de produção no Git

## Troubleshooting

### Servidor não aparece automaticamente

1. Verifique se o `servers.json` está bem formatado (JSON válido)
2. Verifique os logs: `docker compose logs pgadmin`
3. Limpe os dados do pgAdmin: `sudo rm -rf data/pgadmin/*` e reinicie

### Pede senha ao conectar

1. Verifique se o formato do `pgpass` está correto
2. Verifique se as permissões estão corretas (600)
3. Confirme que o hostname, porta, usuário e senha correspondem ao PostgreSQL

### Erro de conexão

1. Verifique se o PostgreSQL está rodando: `docker compose ps postgresql`
2. Teste a conexão manualmente: `docker compose exec postgresql psql -U local -d local`
3. Verifique se o hostname no `servers.json` corresponde ao nome do serviço no docker-compose
