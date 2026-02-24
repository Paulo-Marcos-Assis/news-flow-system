# 📚 Guia: Coleta Completa de Notícias

## ✅ Confirmação: 9 Portais Funcionais

Sim, você tem **9 portais funcionais** configurados:

1. ~~ndmais~~ (você já tem as notícias)
2. **nsc**
3. **jornalconexao**
4. **olharsc**
5. **agoralaguna**
6. **ocpnews**
7. **jornalsulbrasil**
8. **iclnoticias**
9. **g1sc**

**Total para raspar: 8 portais** (excluindo ndmais)

---

## 📊 Estimativa de Tempo e Volume

### Configurações Atuais (max_page)

| Portal | max_page | Artigos Estimados* | Tempo Estimado** |
|--------|----------|-------------------|------------------|
| **nsc** | 2000 | ~30,000 | ~4h 30min |
| **g1sc** | 1000 | ~15,000 | ~2h 15min |
| **jornalconexao** | 500 | ~7,500 | ~1h 10min |
| **olharsc** | 500 | ~7,500 | ~1h 10min |
| **agoralaguna** | 500 | ~7,500 | ~1h 10min |
| **ocpnews** | 500 | ~7,500 | ~1h 10min |
| **jornalsulbrasil** | 500 | ~7,500 | ~1h 10min |
| **iclnoticias** | 300 | ~4,500 | ~40min |

**TOTAL (8 portais): ~87,000 artigos em ~12-14 horas**

\* Assumindo ~15 artigos por página  
\** Tempo considerando 0.5s por artigo + 2s por página

### ⚠️ Observações Importantes

1. **Tempo Real Pode Variar**: Depende da velocidade dos sites, carga do servidor, etc.
2. **Volume de Dados**: ~87,000 artigos = vários GB de dados
3. **Recursos**: Certifique-se de ter espaço em disco suficiente
4. **Rede**: Processo intensivo em requisições HTTP

---

## 🎯 Estratégia Recomendada: Teste com 3 Portais

Como você sugeriu, é **altamente recomendado** começar com 3 portais menores para validar:

### Fase 1: Teste (3 portais menores)
- **iclnoticias** (300 páginas, ~40min)
- **jornalconexao** (500 páginas, ~1h 10min)
- **olharsc** (500 páginas, ~1h 10min)

**Total Fase 1: ~3 horas, ~19,500 artigos**

### Fase 2: Portais Médios (4 portais)
- **agoralaguna** (500 páginas)
- **ocpnews** (500 páginas)
- **jornalsulbrasil** (500 páginas)
- **g1sc** (1000 páginas)

**Total Fase 2: ~6 horas, ~37,500 artigos**

### Fase 3: Portal Grande (1 portal)
- **nsc** (2000 páginas)

**Total Fase 3: ~4h 30min, ~30,000 artigos**

---

## 🚀 Como Executar

### Opção 1: Script Automatizado (Recomendado)

#### Teste com 3 portais:
```bash
cd /home/paulo/projects/main-server/triggers
source ../.venv/bin/activate
export QUEUE_SERVER_ADDRESS=localhost
export RABBIT_MQ_USER=admin
export RABBIT_MQ_PWD=admin

python3 trigger-collect-all.py iclnoticias jornalconexao olharsc
```

#### Todos os 8 portais (exceto ndmais):
```bash
python3 trigger-collect-all.py
```

#### Portais específicos:
```bash
python3 trigger-collect-all.py nsc g1sc
```

### Opção 2: Manual via RabbitMQ

Envie mensagens JSON para a fila `noticias_collector`:

```json
{
    "portal_name": "nsc",
    "collect_all": "yes",
    "entity_type": "noticias_sc",
    "folder_path": null,
    "date": null
}
```

---

## 📋 Pré-requisitos

### 1. Rebuild do Container (OBRIGATÓRIO)

O código foi modificado para suportar `collect_all`. Você precisa fazer rebuild:

```bash
cd /home/paulo/projects/main-server
docker compose stop collector-noticias
docker compose build collector-noticias
docker compose up -d collector-noticias
```

### 2. RabbitMQ Rodando

```bash
docker compose ps rabbitmq
# Se não estiver rodando:
docker compose up -d rabbitmq
```

### 3. Espaço em Disco

Verifique se tem espaço suficiente:

```bash
df -h
```

Recomendado: **pelo menos 20GB livres**

---

## 📊 Monitoramento

### Logs do Coletor

```bash
# Acompanhar em tempo real
docker compose logs -f collector-noticias

# Ver últimas 100 linhas
docker compose logs --tail=100 collector-noticias

# Filtrar por portal específico
docker compose logs collector-noticias | grep "portal_name.*nsc"
```

### Fila RabbitMQ

Acesse: http://localhost:15672  
Usuário: `admin`  
Senha: `admin`

Vá em **Queues** → `noticias_collector` para ver:
- Mensagens pendentes
- Taxa de processamento
- Mensagens processadas

### Progresso Estimado

O coletor mostra barras de progresso (tqdm) nos logs:

```
Coletando páginas do nsc: 45%|████▌     | 900/2000 [1:23:45<1:42:30, 5.59s/it]
```

---

## 🛑 Como Parar a Coleta

### Parar o Coletor

```bash
docker compose stop collector-noticias
```

### Limpar a Fila (se necessário)

```bash
curl -u admin:admin -X DELETE http://localhost:15672/api/queues/%2F/noticias_collector/contents
```

### Reiniciar

```bash
docker compose up -d collector-noticias
```

---

## 📁 Onde os Dados São Salvos

Os artigos coletados são enviados para a fila `noticias_processor` e depois salvos no:

- **MinIO** (bucket configurado em `PUBLIC_BUCKET`)
- **MongoDB** (se configurado no pipeline)

Para verificar no MinIO:
```bash
docker compose logs collector-noticias | grep "artigos coletados"
```

---

## ⚠️ Problemas Comuns

### 1. "ModuleNotFoundError: No module named 'tqdm'"

```bash
source /home/paulo/projects/main-server/.venv/bin/activate
pip install tqdm
```

### 2. "ConnectionRefusedError" (RabbitMQ)

```bash
# Verificar se RabbitMQ está rodando
docker compose ps rabbitmq

# Iniciar se necessário
docker compose up -d rabbitmq
```

### 3. Container não usa código atualizado

```bash
# Fazer rebuild
docker compose build collector-noticias
docker compose up -d collector-noticias
```

### 4. Coleta muito lenta

- Verifique a conexão de internet
- Alguns sites podem ter rate limiting
- Ajuste o `time.sleep(0.2)` no código se necessário

---

## 📈 Próximos Passos Após Coleta

1. **Verificar quantidade coletada**:
   ```bash
   docker compose logs collector-noticias | grep "Total de artigos coletados"
   ```

2. **Processar os artigos** (se tiver pipeline configurado):
   - Classificação
   - Extração de entidades
   - Armazenamento final

3. **Análise dos dados**:
   - Verificar qualidade
   - Identificar duplicatas
   - Validar datas

---

## 💡 Dicas

1. **Execute em horário de baixo tráfego** nos sites (madrugada)
2. **Monitore o primeiro portal** antes de enviar todos
3. **Faça backup** dos dados coletados
4. **Documente problemas** encontrados em cada portal
5. **Ajuste max_page** se necessário após validação

---

## 🎓 Exemplo Completo: Fase 1 (Teste)

```bash
# 1. Ativar ambiente
cd /home/paulo/projects/main-server/triggers
source ../.venv/bin/activate

# 2. Configurar variáveis
export QUEUE_SERVER_ADDRESS=localhost
export RABBIT_MQ_USER=admin
export RABBIT_MQ_PWD=admin

# 3. Rebuild do container (primeira vez)
cd ..
docker compose build collector-noticias
docker compose up -d collector-noticias

# 4. Voltar para triggers e executar
cd triggers
python3 trigger-collect-all.py iclnoticias jornalconexao olharsc

# 5. Monitorar
docker compose logs -f collector-noticias
```

**Tempo estimado: ~3 horas**

Após validar que funciona, prossiga com as Fases 2 e 3!

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs: `docker compose logs collector-noticias`
2. Verifique a fila: http://localhost:15672
3. Verifique o código: `/home/paulo/projects/main-server/collector/noticias/main.py`

Boa coleta! 🚀
