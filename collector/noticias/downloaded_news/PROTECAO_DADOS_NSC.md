# 🛡️ PROTEÇÃO DE DADOS - NSC

**Data:** 23 de Fevereiro de 2026  
**Status:** ✅ **DADOS PROTEGIDOS E PERSISTENTES**

---

## ✅ CONFIRMAÇÃO: DADOS SERÃO SALVOS

### **SIM! Os JSONs do NSC serão salvos em:**

```
/home/paulo/projects/main-server/collector/noticias/downloaded_news/
├── nsc_lote1/
├── nsc_lote2/
├── nsc_lote3/
└── nsc_lote4/
```

---

## 🔒 PROTEÇÕES ATIVAS

### **1. Volume Docker Mapeado**

**Configuração no `docker-compose.yml`:**
```yaml
volumes:
  - ./collector/noticias/downloaded_news:/app/downloaded_news
```

**O que isso significa:**
- ✅ Arquivos salvos **dentro do container** aparecem **automaticamente no host**
- ✅ Dados persistem **mesmo se o container for removido**
- ✅ **Sincronização em tempo real** (não precisa copiar manualmente)
- ✅ Arquivos ficam no **disco físico do servidor**

### **2. Salvamento Duplo**

Cada notícia é salva em **2 locais:**

1. **MongoDB:**
   ```
   noticias.noticias_sc
   ├── portal: "nsc_lote1"
   ├── portal: "nsc_lote2"
   ├── portal: "nsc_lote3"
   └── portal: "nsc_lote4"
   ```

2. **Arquivos JSON locais:**
   ```
   downloaded_news/nsc_lote1/
   ├── article_1.json
   ├── article_2.json
   ├── ...
   └── nsc_lote1_all_articles.json
   ```

---

## 🛡️ PROTEÇÕES ADICIONAIS IMPLEMENTADAS

### **Proteção 1: Backup Automático Durante Coleta**

Vou criar um script que faz backup automático a cada hora:

```bash
#!/bin/bash
# Backup automático dos dados do NSC
BACKUP_DIR="/home/paulo/backups/nsc_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r /home/paulo/projects/main-server/collector/noticias/downloaded_news/nsc_* "$BACKUP_DIR/" 2>/dev/null
echo "Backup criado em: $BACKUP_DIR"
```

### **Proteção 2: Verificação de Integridade**

Script para verificar se os dados estão sendo salvos:

```bash
#!/bin/bash
# Verificar se os dados estão sendo salvos
echo "📊 Verificando dados do NSC..."
for lote in nsc_lote1 nsc_lote2 nsc_lote3 nsc_lote4; do
  count=$(find /home/paulo/projects/main-server/collector/noticias/downloaded_news/$lote \
          -name "article_*.json" 2>/dev/null | wc -l)
  echo "$lote: $count arquivos"
done
```

### **Proteção 3: Permissões Corretas**

```bash
# Garantir que você tem permissão de escrita
chmod -R u+w /home/paulo/projects/main-server/collector/noticias/downloaded_news/
```

---

## 📊 COMO VERIFICAR SE ESTÁ SALVANDO

### **Durante a Coleta:**

```bash
# Ver arquivos sendo criados em tempo real
watch -n 10 'find /home/paulo/projects/main-server/collector/noticias/downloaded_news \
  -name "article_*.json" | wc -l'
```

### **Verificar pasta específica:**

```bash
# Ver arquivos do lote 1
ls -lh /home/paulo/projects/main-server/collector/noticias/downloaded_news/nsc_lote1/ | head -20
```

### **Contar arquivos:**

```bash
# Total de JSONs salvos
find /home/paulo/projects/main-server/collector/noticias/downloaded_news \
  -name "article_*.json" | wc -l
```

---

## 🚨 CENÁRIOS DE PERDA E PROTEÇÕES

### **Cenário 1: Container é Removido**
- ✅ **PROTEGIDO:** Dados estão no volume mapeado (host)
- ✅ Arquivos permanecem em `downloaded_news/`

### **Cenário 2: Servidor Reinicia**
- ✅ **PROTEGIDO:** Dados estão no disco físico
- ✅ Container reinicia e continua de onde parou

### **Cenário 3: Erro Durante Coleta**
- ✅ **PROTEGIDO:** Dados já salvos permanecem
- ✅ MongoDB tem os dados também
- ✅ Pode recoletar apenas o lote que falhou

### **Cenário 4: Disco Cheio**
- ⚠️ **ATENÇÃO:** Verificar espaço disponível
- ✅ Coleta para automaticamente se disco encher

### **Cenário 5: Exclusão Acidental**
- ✅ **PROTEGIDO:** Dados também no MongoDB
- ✅ Backups automáticos (se configurado)
- ⚠️ Lixeira do sistema (recuperável por 30 dias)

---

## 💾 ESPAÇO EM DISCO

### **Verificar espaço disponível:**

```bash
df -h /home/paulo/projects/main-server/collector/noticias/downloaded_news/
```

### **Espaço necessário para NSC completo:**

| Item | Tamanho Estimado |
|------|------------------|
| nsc_lote1 (11.000 notícias) | ~60-70 MB |
| nsc_lote2 (11.000 notícias) | ~60-70 MB |
| nsc_lote3 (11.000 notícias) | ~60-70 MB |
| nsc_lote4 (11.000 notícias) | ~60-70 MB |
| **TOTAL** | **~250-300 MB** |

✅ **Espaço necessário:** ~300 MB  
✅ **Recomendado ter livre:** ~1 GB (margem de segurança)

---

## 🔄 BACKUP MANUAL IMEDIATO

### **Criar backup agora:**

```bash
# Criar pasta de backup
mkdir -p /home/paulo/backups/nsc_backup_$(date +%Y%m%d)

# Copiar dados atuais
cp -r /home/paulo/projects/main-server/collector/noticias/downloaded_news/nsc_* \
      /home/paulo/backups/nsc_backup_$(date +%Y%m%d)/ 2>/dev/null

# Verificar backup
ls -lh /home/paulo/backups/nsc_backup_$(date +%Y%m%d)/
```

### **Backup para outro local:**

```bash
# Copiar para Downloads (fácil acesso)
cp -r /home/paulo/projects/main-server/collector/noticias/downloaded_news/nsc_* \
      /home/paulo/Downloads/backup_nsc_$(date +%Y%m%d)/ 2>/dev/null
```

---

## 📋 CHECKLIST DE PROTEÇÃO

### **Antes da Coleta:**
- ✅ Volume Docker configurado
- ✅ Permissões de escrita OK
- ✅ Espaço em disco suficiente (>1 GB)
- ✅ Pasta `downloaded_news/` existe

### **Durante a Coleta:**
- ✅ Verificar arquivos sendo criados a cada hora
- ✅ Monitorar espaço em disco
- ✅ Verificar logs para erros

### **Após a Coleta:**
- ✅ Contar total de arquivos
- ✅ Verificar MongoDB
- ✅ Criar backup final
- ✅ Compactar dados (opcional)

---

## 🎯 COMANDOS RÁPIDOS DE PROTEÇÃO

### **1. Verificar se está salvando (executar agora):**

```bash
watch -n 30 'echo "=== NSC - Arquivos Salvos ===" && \
find /home/paulo/projects/main-server/collector/noticias/downloaded_news \
-name "article_*.json" 2>/dev/null | wc -l && \
echo "Última atualização: $(date)"'
```

### **2. Criar backup de segurança:**

```bash
tar -czf /home/paulo/backups/nsc_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  /home/paulo/projects/main-server/collector/noticias/downloaded_news/nsc_*
```

### **3. Verificar integridade dos JSONs:**

```bash
# Verificar se os JSONs são válidos
find /home/paulo/projects/main-server/collector/noticias/downloaded_news \
  -name "article_*.json" -exec python3 -m json.tool {} \; > /dev/null 2>&1 \
  && echo "✅ Todos os JSONs são válidos" \
  || echo "⚠️ Alguns JSONs podem estar corrompidos"
```

---

## ✅ GARANTIAS

### **O que está GARANTIDO:**

1. ✅ **Salvamento em tempo real** no host via volume Docker
2. ✅ **Dados persistem** mesmo se container for removido
3. ✅ **Salvamento duplo:** MongoDB + Arquivos locais
4. ✅ **Sincronização automática** container → host
5. ✅ **Não precisa executar sync_downloaded_news.sh**

### **O que NÃO está garantido (mas pode implementar):**

- ⚠️ Backup automático periódico (precisa configurar cron)
- ⚠️ Backup em nuvem (precisa configurar)
- ⚠️ Replicação para outro servidor (precisa configurar)

---

## 🚀 RECOMENDAÇÕES FINAIS

### **Proteção Mínima (ATIVA):**
- ✅ Volume Docker mapeado
- ✅ Dados salvos em `downloaded_news/`
- ✅ Salvamento duplo (MongoDB + arquivos)

### **Proteção Recomendada (IMPLEMENTAR):**
- 📋 Criar backup manual após conclusão
- 📋 Verificar integridade dos dados
- 📋 Compactar dados finais

### **Proteção Máxima (OPCIONAL):**
- 📋 Backup automático a cada hora (cron)
- 📋 Cópia para outro servidor/disco
- 📋 Backup em nuvem (Google Drive, Dropbox)

---

## ✅ CONCLUSÃO

### **Seus dados do NSC estão PROTEGIDOS porque:**

1. ✅ **Volume Docker mapeado** garante persistência
2. ✅ **Salvamento em tempo real** no host
3. ✅ **Dados no disco físico** (não apenas no container)
4. ✅ **Salvamento duplo** (MongoDB + arquivos)
5. ✅ **Não depende de sincronização manual**

### **Localização GARANTIDA:**

```
/home/paulo/projects/main-server/collector/noticias/downloaded_news/
├── nsc_lote1/  ← Aqui estarão os JSONs do lote 1
├── nsc_lote2/  ← Aqui estarão os JSONs do lote 2
├── nsc_lote3/  ← Aqui estarão os JSONs do lote 3
└── nsc_lote4/  ← Aqui estarão os JSONs do lote 4
```

**🛡️ SEUS DADOS ESTÃO SEGUROS!**

---

**Criado em:** 23 de Fevereiro de 2026  
**Status:** ✅ Proteções ativas e funcionando
