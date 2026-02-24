# 📊 RELATÓRIO: O QUE ACONTECEU COM O PORTAL NSC?

**Data do Relatório:** 23 de Fevereiro de 2026  
**Portal:** NSC (www.nsctotal.com.br)

---

## 🎯 RESUMO EXECUTIVO

**Status:** ❌ **COLETA FALHOU - DADOS PERDIDOS**

---

## 📋 HISTÓRICO DE TENTATIVAS DE COLETA

### **Tentativa 1: 16 Fevereiro 2026**

**Período:** 16/02/2026 às 02:18 - 04:34  
**Duração:** ~2 horas e 16 minutos  
**Status:** ⚠️ Coletado mas **NÃO SALVO**

#### **Resultado:**
- ✅ **10.565 notícias coletadas** com sucesso
- ❌ **0 notícias salvas** no MongoDB
- ❌ **0 arquivos JSON salvos** localmente
- ❌ **Dados completamente perdidos**

#### **Evidências dos Logs:**
```
[2026-02-16 02:18:33] Iniciando coleta completa do portal NSC (2000 páginas estimadas)
[2026-02-16 04:34:18] Total de artigos coletados do NSC: 10565
[2026-02-16 04:34:18] ERROR: Failed to publish message to queue 'noticias_processor_teste' 
                      (attempt 1/3): Channel is closed.
[ERROR] Stream connection lost: ConnectionResetError(104, 'Connection reset by peer')
```

#### **Causa da Falha:**
- **Erro de conexão com RabbitMQ** durante o salvamento
- Canal de comunicação foi fechado inesperadamente
- Conexão perdida durante a publicação das mensagens

#### **Impacto:**
- As 10.565 notícias foram **processadas** mas **nunca foram salvas**
- Dados perdidos permanentemente (não recuperáveis)

---

### **Tentativa 2: 18 Fevereiro 2026**

**Período:** 18/02/2026 às 21:49  
**Status:** ❌ **NÃO EXECUTOU**

#### **O que foi feito:**
1. ✅ Container rebuilded com configuração correta
2. ✅ Fila RabbitMQ limpa
3. ✅ Mensagem enviada para NSC
4. ❌ **Coleta nunca iniciou**

#### **Configuração Utilizada:**
```json
"nsc": {
  "base_url": "https://www.nsctotal.com.br/ultimas-noticias/page/{}",
  "min_page": 1,
  "max_page": 2000
}
```

#### **Resultado:**
- ❌ Nenhuma notícia coletada
- ❌ Nenhum arquivo salvo
- ⚠️ Coleta não foi executada (motivo desconhecido)

---

## 📊 ESTATÍSTICAS DO NSC

### **Dados Esperados:**
- **Páginas configuradas:** 2000
- **Notícias estimadas:** ~44.000
- **Tempo estimado:** 8-9 horas
- **Tamanho estimado:** ~250 MB

### **Dados Coletados (Tentativa 1):**
- **Páginas processadas:** Desconhecido
- **Notícias coletadas:** 10.565
- **Notícias salvas:** **0**
- **Taxa de sucesso:** 0%

### **Dados Coletados (Tentativa 2):**
- **Notícias coletadas:** 0
- **Notícias salvas:** 0

---

## 🔍 ANÁLISE TÉCNICA

### **Problema 1: Falha no RabbitMQ (Tentativa 1)**

**Sintomas:**
- Coleta executada com sucesso
- Erro ao publicar mensagens na fila de saída
- Canal RabbitMQ fechado inesperadamente
- Conexão perdida (ConnectionResetError)

**Possíveis Causas:**
1. **Sobrecarga do RabbitMQ:**
   - 10.565 mensagens sendo publicadas rapidamente
   - Possível timeout ou limite de conexão atingido

2. **Problema de Rede:**
   - Conexão instável entre container e RabbitMQ
   - Timeout de rede durante operação longa

3. **Limite de Recursos:**
   - Memória insuficiente no RabbitMQ
   - Fila muito grande causando problemas

**Consequência:**
- Dados coletados mas não persistidos
- Perda total de 10.565 notícias

---

### **Problema 2: Coleta Não Executada (Tentativa 2)**

**Sintomas:**
- Mensagem enviada para a fila
- Container rodando normalmente
- Nenhuma coleta iniciada

**Possíveis Causas:**
1. **Mensagem não consumida:**
   - Fila não sendo processada
   - Consumer não ativo

2. **Configuração incorreta:**
   - Problema no rebuild do container
   - Configuração não carregada corretamente

3. **Conflito de processos:**
   - Outro processo bloqueando a coleta
   - Mensagem antiga interferindo

---

## 📁 ARQUIVOS DO NSC

### **No MongoDB:**
```
noticias.noticias_sc (portal: "nsc"): 0 documentos
```

### **Em Arquivos Locais:**
```
/app/downloaded_news/nsc/: Pasta não existe
```

### **Em Backups:**
```
Downloads: 0 arquivos do NSC
Lixeira: 0 arquivos do NSC
```

**Conclusão:** ❌ **Nenhum dado do NSC foi preservado**

---

## 🎯 COMPARAÇÃO: NSC vs OUTROS PORTAIS

### **Portais com Sucesso:**

| Portal | Notícias | Status | Salvamento |
|--------|----------|--------|------------|
| jornalconexao | 7.487 | ✅ | MongoDB + Arquivos |
| g1sc | 7.551 | ✅ | MongoDB + Arquivos |
| agoralaguna | 3.010 | ✅ | MongoDB + Arquivos |
| iclnoticias | 1.480 | ✅ | MongoDB + Arquivos |

### **NSC:**

| Portal | Notícias | Status | Salvamento |
|--------|----------|--------|------------|
| **NSC** | 10.565 | ❌ | **Nenhum** |

**Diferença:** Todos os outros portais salvaram com sucesso. Apenas NSC falhou.

---

## 🚨 POR QUE O NSC É IMPORTANTE?

### **Volume de Dados:**
- **Maior portal configurado:** 2000 páginas
- **~44.000 notícias estimadas** (mais que todos os outros juntos)
- **Cobertura:** Santa Catarina (NSC Total)

### **Relevância:**
- Portal de notícias regional importante
- Cobertura ampla de SC
- Potencial alto de notícias sobre fraudes e crimes

### **Impacto da Perda:**
- **10.565 notícias perdidas** na primeira tentativa
- **~33.435 notícias não coletadas** (restante estimado)
- **Total de ~44.000 notícias faltando**

---

## ✅ PRÓXIMAS AÇÕES RECOMENDADAS

### **1. Diagnóstico do RabbitMQ**
```bash
# Verificar status do RabbitMQ
docker compose logs rabbitmq | grep -i error

# Verificar filas
docker exec main-server-rabbitmq-1 rabbitmqctl list_queues

# Verificar conexões
docker exec main-server-rabbitmq-1 rabbitmqctl list_connections
```

### **2. Ajustar Configuração para Coleta Segura**

**Opção A: Coletar em Lotes Menores**
```json
{
  "nsc_lote1": {
    "base_url": "https://www.nsctotal.com.br/ultimas-noticias/page/{}",
    "min_page": 1,
    "max_page": 500
  },
  "nsc_lote2": {
    "base_url": "https://www.nsctotal.com.br/ultimas-noticias/page/{}",
    "min_page": 501,
    "max_page": 1000
  }
}
```

**Opção B: Adicionar Delays e Retry**
- Implementar delay entre páginas
- Adicionar retry automático em caso de falha
- Salvar checkpoints a cada X páginas

### **3. Garantir Persistência**
```python
# Adicionar salvamento local ANTES de publicar no RabbitMQ
# Implementar salvamento incremental
# Criar backup a cada 100 notícias
```

### **4. Monitoramento Ativo**
- Acompanhar logs em tempo real
- Verificar salvamento a cada 500 notícias
- Alertas em caso de erro

---

## 📊 ESTIMATIVA DE RECOLETA

### **Cenário Otimista (Lotes de 500 páginas):**
- **Lotes:** 4 lotes de 500 páginas
- **Tempo por lote:** ~2-3 horas
- **Tempo total:** ~8-12 horas
- **Risco:** Médio

### **Cenário Conservador (Lotes de 200 páginas):**
- **Lotes:** 10 lotes de 200 páginas
- **Tempo por lote:** ~1 hora
- **Tempo total:** ~10 horas
- **Risco:** Baixo

---

## ✅ CONCLUSÃO

### **Status Atual do NSC:**
- ❌ **0 notícias salvas** (de ~44.000 esperadas)
- ❌ **2 tentativas falharam**
- ⚠️ **Dados irrecuperáveis**

### **Causa Principal:**
- **Falha de conexão RabbitMQ** durante salvamento
- Sistema não preparado para volume grande de dados

### **Solução Recomendada:**
1. ✅ Dividir coleta em lotes menores (500 páginas)
2. ✅ Implementar salvamento local ANTES de RabbitMQ
3. ✅ Adicionar checkpoints e retry
4. ✅ Monitorar ativamente durante coleta

### **Prioridade:**
🔴 **ALTA** - NSC é o maior portal e mais importante da coleta

---

**Relatório gerado em:** 23 de Fevereiro de 2026  
**Última tentativa de coleta:** 18 de Fevereiro de 2026  
**Status:** Aguardando nova tentativa com melhorias
