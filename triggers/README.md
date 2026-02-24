
![CEOS Logo](https://media.licdn.com/dms/image/v2/D4D3DAQEjzxRpBN5e3g/image-scale_191_1128/B4DZZDnIySGwAc-/0/1744891056088/projeto_cos_cover?e=1752706800&v=beta&t=XVAojp8aAqxQSYJlzZFikBAZ-18keS1ClZyaYIGVe8k)

# Trigger - Projeto CEOS
O `trigger.py` é o ponto de partida da coleta de dados de uma **fonte específica** dentro do fluxo CEOS. Ele **inicia o processo** com base em **configurações pré-definidas**, informadas em arquivos JSON (ex: `e-sfinge.json`).

---

## 📌 O que é um Trigger?

No contexto do projeto **CEOS**, o trigger é responsável por **disparar a coleta de dados** com base em uma granularidade configurável:

- ⏱️ Diária
- 📆 Mensal
- ⚙️ Por evento
- 📂 Ao receber um arquivo externo

Ele **não processa dados diretamente**, apenas dá o _start_ para que o coletor responsável execute o trabalho principal.

---

## 📁 Estrutura do Projeto

```plaintext
/main-server
│
├── /collector
│   ├── /pncp            
│   ├── /dom             
│   ├── /notas           
│   └── /esfinge
│       └── main.py
│
├── /triggers                   ← 🎯 VOCÊ ESTÁ AQUI
│   ├── trigger-esfinge.py      
│   ├── esfinge.json            ← ⚙️ Configuração do trigger
│   └── /service_essentials     ← 🔧 Utilitários comuns
│
└── .env                        ← 🔐 Variáveis de ambiente (ex: chaves S3, tokens)
```

---
## Como executar

1. Certifique-se de ter o Python instalado.
> As filas devem estar em execução para que o trigger funcione corretamente. Para isso, siga as instruções do [main-server](https://codigos.ufsc.br/ceos/data-ingestion-system/main-server/-/blob/main/README.md?ref_type=heads).
2. Executar o trigger:
```bash
  python trigger-e-sfinge.py
```
---
## Resposta esperada
Ao executar, o serviço irá iniciar o fluxo configurado e exibir uma mensagem indicando o disparo do processo, por exemplo
```plaintext
    ################## Trigger started for the flow: e-Sfinge ##################
    [2025-07-09 18:42:46] [INFO] Connecting to RabbitMQ server - localhost:5672
    [2025-07-09 18:42:46] [INFO] Connected to RabbitMQ
    [2025-07-09 18:42:46] [INFO] Connecting to queue: esfinge_collector...
    [2025-07-09 18:42:46] [INFO] Queue 'esfinge_collector' declared.
    [2025-07-09 18:42:46] [INFO] ...connected to queues successfully.
    [2025-07-09 18:42:46] [INFO] Sending collecting message #0 to esfinge_collector: {'data_path': '../dataset_esfinge', 'year': '[2021, 2022, 2023]'}
    [2025-07-09 18:42:46] [INFO] Message published to queue 'esfinge_collector': {
        "data_path": "../dataset_esfinge",
        "year": "[2021, 2022, 2023]"
    }
```
---
## Diagrama de Fluxo Simplificado
```plaintext
                ┌────────────┐      ┌──────────────────┐     ┌──────────────┐
                │ Scheduler  │───►  │ trigger.py       │───► │  Coletor     │
                │ (cronjob)  │      │ (start do fluxo) │     │ (main.py)    │
                └────────────┘      └──────────────────┘     └──────────────┘
```
---
## Sobre o Arquivo de Configuração (.json)
Cada trigger possui um arquivo de configuração com nome do fluxo, por exemplo:
```json
{
  "nome_fluxo": "e-sfinge",
  "endpoint": "https://api.dados.gov.br/e-sfinge",
  "formato_saida": "json",
  "frequencia": "diaria",
  "autenticacao": {
    "tipo": "chave",
    "token": "ENV[API_TOKEN_ESFINGE]"
  }
}
```  
> 🔐 Valores marcados como ENV[...] devem estar presentes no arquivo .env.


---
## Contato

Em caso de dúvidas técnicas, procure os responsáveis pela arquitetura CEOS ou consulte a [documentação](https://codigos.ufsc.br/ceos/geral/wiki-ceos) principal do projeto.

[<img src="https://media.licdn.com/dms/image/v2/D4E0BAQGGTimP9w29Pg/company-logo_200_200/B4EZY1r9FRGgAI-/0/1744657437455?e=1757548800&v=beta&t=_03eBQvCdGrBVA5XQUs7WQH11XyKGXMGlcxnCKsjwis" width=115><br><sub>Projeto Céos</sub>](https://ceos.ufsc.br/)