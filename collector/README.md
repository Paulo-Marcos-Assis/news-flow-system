![CEOS Logo](https://media.licdn.com/dms/image/v2/D4D3DAQEjzxRpBN5e3g/image-scale_191_1128/B4DZZDnIySGwAc-/0/1744891056088/projeto_cos_cover?e=1752706800&v=beta&t=XVAojp8aAqxQSYJlzZFikBAZ-18keS1ClZyaYIGVe8k)

# Collector - Projeto CEOS

O coletor `main.py` é responsável por processar as requisições disparadas pelo trigger, coletando dados da fonte configurada no trigger, armazenar o resultado da coleta em uma única mensagem e repassar essa mensagem ao `splitter`, conforme as regras do fluxo CEOS.

---

## O que é o Collector?

No contexto do projeto **CEOS**, um collector é o serviço que:

- Recebe comandos do trigger via fila (RabbitMQ)
- Realiza a coleta dos dados da fonte e-Sfinge (configuradas no arquivo `esfinge.json`)
- Processa, transforma e enfileira os dados coletados para o `splitter`
- Gera logs detalhados do processo
---
## 📁 Estrutura do Projeto

```plaintext
/main-server
│
├── /collector                   ← 🟢 VOCÊ ESTÁ AQUI
│   ├── /pncp            
│   ├── /dom             
│   ├── /notas           
│   └── /esfinge
│       
│
├── /triggers
│   ├── trigger-pncp.py
│   ├── trigger-dom.py
│   ├── trigger-notas.py
│   ├── trigger-esfinge.py
│   └── esfinge.json
│
└── .env
```

---
## Diagrama de Fluxo Simplificado
```plaintext
    ┌────────────┐      ┌──────────────────┐     ┌──────────────┐     ┌──────────────┐
    │ Scheduler  │───►  │    trigger.py    │───► │  Collector   │───► │  Splliter    │
    │ (cronjob)  │      │ (start do fluxo) │     │  (main.py)   │     │  (main.py)   │
    └────────────┘      └──────────────────┘     └──────────────┘     └──────────────┘
```
---
## Contato

Em caso de dúvidas técnicas, procure os responsáveis pela arquitetura CEOS ou consulte a [documentação](https://codigos.ufsc.br/ceos/geral/wiki-ceos) principal do projeto.

[<img src="https://media.licdn.com/dms/image/v2/D4E0BAQGGTimP9w29Pg/company-logo_200_200/B4EZY1r9FRGgAI-/0/1744657437455?e=1757548800&v=beta&t=_03eBQvCdGrBVA5XQUs7WQH11XyKGXMGlcxnCKsjwis" width=115><br><sub>Projeto Céos</sub>](https://ceos.ufsc.br/)
