#!/usr/bin/env python3
"""
Script para coletar TODAS as notícias de portais específicos.
Uso: python3 trigger-collect-all.py [portal1] [portal2] [portal3] ...

Se nenhum portal for especificado, coleta de todos os portais configurados (exceto ndmais).
"""

import time
import json
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

# Setup paths
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service_essentials.queue_manager.queue_manager_factory import QueueManagerFactory

# Portais disponíveis (excluindo ndmais)
AVAILABLE_PORTALS = [
    "nsc",
    "jornalconexao",
    "olharsc",
    "agoralaguna",
    "ocpnews",
    "jornalsulbrasil",
    "iclnoticias",
    "g1sc"
]

# Configurações de max_page para estimativas
MAX_PAGES = {
    "nsc": 2000,
    "jornalconexao": 500,
    "olharsc": 500,
    "agoralaguna": 500,
    "ocpnews": 500,
    "jornalsulbrasil": 500,
    "iclnoticias": 300,
    "g1sc": 1000
}

def estimate_time(portals):
    """
    Estima o tempo necessário para coletar todos os portais.
    
    Premissas:
    - ~10-20 artigos por página
    - ~0.2s por artigo (sleep entre requests)
    - ~2s por página (request + parsing)
    """
    total_pages = sum(MAX_PAGES.get(p, 500) for p in portals)
    avg_articles_per_page = 15
    total_articles_estimate = total_pages * avg_articles_per_page
    
    # Tempo por página (request + parsing)
    time_per_page = 2  # segundos
    
    # Tempo por artigo (request + parsing + sleep)
    time_per_article = 0.5  # segundos
    
    total_time_seconds = (total_pages * time_per_page) + (total_articles_estimate * time_per_article)
    
    hours = int(total_time_seconds // 3600)
    minutes = int((total_time_seconds % 3600) // 60)
    
    return {
        "portals": len(portals),
        "total_pages": total_pages,
        "estimated_articles": total_articles_estimate,
        "estimated_time_seconds": total_time_seconds,
        "estimated_time_formatted": f"{hours}h {minutes}min"
    }

def send_collect_all_messages(portals, queue_name="noticias_collector"):
    """
    Envia mensagens para coletar TODAS as notícias dos portais especificados.
    """
    messages = []
    
    for portal in portals:
        messages.append({
            "portal_name": portal,
            "collect_all": "yes",
            "entity_type": "noticias_sc",
            "folder_path": None,
            "date": None
        })
    
    return messages

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 COLETA COMPLETA DE NOTÍCIAS - TODOS OS PORTAIS")
    print("=" * 70)
    print()
    
    # Determinar quais portais coletar
    if len(sys.argv) > 1:
        # Portais especificados via argumentos
        requested_portals = sys.argv[1:]
        portals_to_collect = []
        
        for portal in requested_portals:
            if portal in AVAILABLE_PORTALS:
                portals_to_collect.append(portal)
            else:
                print(f"⚠️  Portal '{portal}' não encontrado. Portais disponíveis:")
                for p in AVAILABLE_PORTALS:
                    print(f"   - {p}")
                sys.exit(1)
    else:
        # Coletar todos os portais
        portals_to_collect = AVAILABLE_PORTALS
    
    print(f"📋 Portais selecionados para coleta completa ({len(portals_to_collect)}):")
    for i, portal in enumerate(portals_to_collect, 1):
        print(f"   {i}. {portal} (max_page: {MAX_PAGES.get(portal, '?')})")
    print()
    
    # Mostrar estimativa
    estimate = estimate_time(portals_to_collect)
    print("⏱️  ESTIMATIVA DE TEMPO:")
    print(f"   • Total de páginas a processar: ~{estimate['total_pages']:,}")
    print(f"   • Artigos estimados: ~{estimate['estimated_articles']:,}")
    print(f"   • Tempo estimado: {estimate['estimated_time_formatted']}")
    print()
    print("   ⚠️  ATENÇÃO: Esta é uma estimativa conservadora.")
    print("      O tempo real pode variar dependendo de:")
    print("      - Velocidade de resposta dos sites")
    print("      - Número real de artigos por página")
    print("      - Carga do servidor")
    print()
    
    # Confirmação
    response = input("Deseja continuar? (sim/não): ").strip().lower()
    if response not in ['sim', 's', 'yes', 'y']:
        print("❌ Operação cancelada pelo usuário.")
        sys.exit(0)
    
    print()
    print("=" * 70)
    print("📤 ENVIANDO MENSAGENS PARA A FILA...")
    print("=" * 70)
    print()
    
    # Gerar mensagens
    messages = send_collect_all_messages(portals_to_collect)
    
    # Conectar ao RabbitMQ
    try:
        queue_manager = QueueManagerFactory.get_queue_manager()
        queue_manager.connect()
        print(f"✅ Conectado ao RabbitMQ")
        
        queue_name = "noticias_collector"
        queue_manager.declare_queue(queue_name)
        print(f"✅ Fila '{queue_name}' declarada")
        print()
        
        # Enviar mensagens
        for i, message in enumerate(messages, 1):
            portal = message['portal_name']
            print(f"📨 Enviando mensagem #{i}/{len(messages)}: {portal}")
            queue_manager.publish_message(queue_name, json.dumps(message, indent=2))
            print(f"   ✅ Mensagem enviada com sucesso")
        
        print()
        print("=" * 70)
        print("✅ TODAS AS MENSAGENS FORAM ENVIADAS COM SUCESSO!")
        print("=" * 70)
        print()
        print("📊 PRÓXIMOS PASSOS:")
        print("   1. O coletor processará as mensagens automaticamente")
        print("   2. Monitore o progresso com: docker compose logs -f collector-noticias")
        print("   3. Verifique a fila em: http://localhost:15672 (admin/admin)")
        print()
        print(f"⏱️  Tempo estimado total: {estimate['estimated_time_formatted']}")
        print()
        
    except Exception as e:
        print(f"❌ ERRO ao conectar ou enviar para o RabbitMQ: {e}")
        print()
        print("💡 DICA: Certifique-se de que:")
        print("   1. O RabbitMQ está rodando: docker compose ps rabbitmq")
        print("   2. As variáveis de ambiente estão corretas")
        print("   3. Você está executando com o ambiente virtual ativado")
        sys.exit(1)
