# 📚 Guia para Testar o Coletor de Notícias

**Para iniciantes em Python**  
**Data: 22/01/2026**

---

## 🎯 Objetivo

Este guia ensina como rodar **apenas o coletor de notícias** para baixar artigos e ver os resultados em arquivos JSON, **sem executar** todo o fluxo de classificação/extração.

---

## 📁 Estrutura de Arquivos

```
collector/noticias/
├── main.py                    # Coletor principal
├── crawler_configs.json       # Configurações dos 20 sites
├── test_collector.py          # Script de teste (NOVO!)
└── GUIA_TESTE_COLETOR.md     # Este guia
```

---

## 🚀 3 Formas de Testar o Coletor

### **Forma 1: Script Interativo (Mais Fácil)** ✅ Recomendado para iniciantes

```bash
cd /home/paulo/projects/main-server/collector/noticias
python3 test_collector.py
```

O script vai perguntar:
1. Qual opção você quer (1, 2 ou 3)
2. Qual portal testar
3. Qual data usar (ou Enter para hoje)

**Exemplo de uso:**
```
Escolha uma opção:
1. Testar um único portal
2. Testar todos os 9 portais funcionais
3. Testar portais específicos

Digite o número da opção: 1
Digite o nome do portal: g1sc
Data alvo (DD/MM/YYYY) ou Enter para hoje: 20/01/2026
```

---

### **Forma 2: Linha de Comando Direta**

Você pode editar o `test_collector.py` e chamar as funções diretamente:

```python
# Testar um portal específico
python3 -c "from test_collector import test_single_portal; test_single_portal('g1sc', '20/01/2026')"

# Testar múltiplos portais
python3 -c "from test_collector import test_multiple_portals; test_multiple_portals(['ndmais', 'nsc', 'g1sc'], '20/01/2026')"
```

---

### **Forma 3: Importar no Python Interativo**

```bash
cd /home/paulo/projects/main-server/collector/noticias
python3
```

Depois, no console Python:

```python
from test_collector import test_single_portal, test_multiple_portals

# Testar G1 SC com data específica
test_single_portal('g1sc', '20/01/2026')

# Testar todos os 9 portais
portals = ['ndmais', 'nsc', 'jornalconexao', 'olharsc', 'agoralaguna', 
           'ocpnews', 'jornalsulbrasil', 'iclnoticias', 'g1sc']
test_multiple_portals(portals, '20/01/2026')
```

---

## 📊 Entendendo os Resultados

### Arquivos JSON Gerados

Após executar o teste, você verá arquivos como:

```
resultado_g1sc_20260122_150530.json              # Um portal
resultado_multiplos_portais_20260122_150530.json # Múltiplos portais
```

### Estrutura do JSON (Um Portal)

```json
[
  {
    "title": "Título da notícia",
    "url": "https://g1.globo.com/sc/...",
    "date": "2026-01-20",
    "content": "Conteúdo completo do artigo...",
    "portal": "g1sc",
    "page": 3
  },
  {
    "title": "Outra notícia...",
    ...
  }
]
```

### Estrutura do JSON (Múltiplos Portais)

```json
{
  "g1sc": {
    "success": true,
    "article_count": 5,
    "articles": [...]
  },
  "ndmais": {
    "success": true,
    "article_count": 3,
    "articles": [...]
  }
}
```

---

## 🔍 Como Inspecionar os JSONs

### Opção 1: Editor de Texto
```bash
# Abrir no VS Code
code resultado_g1sc_20260122_150530.json

# Ou usar cat para ver no terminal
cat resultado_g1sc_20260122_150530.json | head -50
```

### Opção 2: Python (Mais Bonito)
```python
import json

# Ler o arquivo
with open('resultado_g1sc_20260122_150530.json', 'r', encoding='utf-8') as f:
    articles = json.load(f)

# Ver quantos artigos
print(f"Total: {len(articles)} artigos")

# Ver primeiro artigo
print(json.dumps(articles[0], indent=2, ensure_ascii=False))

# Ver apenas títulos
for i, article in enumerate(articles, 1):
    print(f"{i}. {article['title']}")
```

### Opção 3: Ferramenta Online
1. Copie o conteúdo do JSON
2. Cole em: https://jsonformatter.org/
3. Clique em "Format/Beautify"

---

## 📋 Lista de Portais Funcionais

Você pode testar qualquer um destes **9 portais**:

| Nome | Site | Observação |
|------|------|------------|
| `ndmais` | ND Mais | ✅ |
| `nsc` | NSC Total | ✅ |
| `jornalconexao` | Jornal Conexão | ✅ |
| `olharsc` | Olhar SC | ✅ |
| `agoralaguna` | Agora Laguna | ✅ |
| `ocpnews` | OCP News | ✅ |
| `jornalsulbrasil` | Jornal Sul Brasil | ✅ |
| `iclnoticias` | ICL Notícias | Foco em fraude |
| `g1sc` | G1 Santa Catarina | ✅ |

---

## 🐛 Problemas Comuns

### Erro: "ModuleNotFoundError: No module named 'tqdm'"

**Solução:**
```bash
pip3 install tqdm --user
```

### Erro: "Nenhum artigo encontrado"

**Possíveis causas:**
1. A data escolhida não tem artigos (ex: feriado)
2. O site mudou a estrutura HTML
3. Problema de conexão

**Solução:** Tente outra data ou outro portal.

### Erro: "Permission denied"

**Solução:**
```bash
chmod +x test_collector.py
```

---

## 💡 Exemplos Práticos

### Exemplo 1: Testar G1 SC hoje
```bash
python3 test_collector.py
# Escolha: 1
# Portal: g1sc
# Data: [Enter]
```

### Exemplo 2: Testar todos os portais em 20/01/2026
```bash
python3 test_collector.py
# Escolha: 2
# Data: 20/01/2026
```

### Exemplo 3: Testar 3 portais específicos
```bash
python3 test_collector.py
# Escolha: 3
# Portais: ndmais, nsc, g1sc
# Data: 20/01/2026
```

---

## 🎓 Próximos Passos

Depois de testar o coletor e ver os JSONs:

1. ✅ Você já sabe como baixar notícias
2. 📊 Pode inspecionar os dados coletados
3. 🔄 Pode integrar com o fluxo completo (classificação)
4. 🚀 Pode adicionar novos sites ao `crawler_configs.json`

---

## 📞 Dúvidas?

- Verifique os logs no terminal
- Inspecione os arquivos JSON gerados
- Teste com datas diferentes
- Teste um portal por vez primeiro

---

**Boa sorte! 🚀**
