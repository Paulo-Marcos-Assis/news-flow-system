#!/usr/bin/env python3
"""
Script para exportar estatísticas da coleta de notícias do MongoDB.

Uso:
    python3 export_statistics.py                    # Estatísticas gerais
    python3 export_statistics.py --portal nsc       # Estatísticas de um portal específico
    python3 export_statistics.py --export stats.json # Exportar para arquivo JSON
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pymongo import MongoClient
from collections import defaultdict

# Configurações do MongoDB (do .env)
MONGO_HOST = os.getenv("HOST_MONGODB", "localhost")
MONGO_PORT = int(os.getenv("PORT_MONGODB", "27017"))
MONGO_USER = os.getenv("USERNAME_MONGODB", "admin")
MONGO_PASS = os.getenv("SENHA_MONGODB", "admin")
MONGO_AUTH_DB = os.getenv("DATABASE_AUTENTICACAO_MONGODB", "admin")

# Collection de notícias
DATABASE = "noticias"
COLLECTION = "noticias.noticias_sc"

def connect_mongodb():
    """Conecta ao MongoDB e retorna o cliente."""
    try:
        client = MongoClient(
            host=MONGO_HOST,
            port=MONGO_PORT,
            username=MONGO_USER,
            password=MONGO_PASS,
            authSource=MONGO_AUTH_DB,
            serverSelectionTimeoutMS=5000
        )
        # Testa a conexão
        client.admin.command('ismaster')
        return client
    except Exception as e:
        print(f"❌ Erro ao conectar ao MongoDB: {e}")
        print(f"   Host: {MONGO_HOST}:{MONGO_PORT}")
        print(f"   User: {MONGO_USER}")
        sys.exit(1)

def get_general_statistics(collection):
    """Obtém estatísticas gerais da coleta."""
    
    # Total de notícias
    total_noticias = collection.count_documents({})
    
    # Estatísticas por portal
    pipeline_portal = [
        {
            "$group": {
                "_id": "$portal_name",
                "total": {"$sum": 1},
                "primeira_data": {"$min": "$date"},
                "ultima_data": {"$max": "$date"}
            }
        },
        {"$sort": {"total": -1}}
    ]
    stats_por_portal = list(collection.aggregate(pipeline_portal))
    
    # Estatísticas por data
    pipeline_data = [
        {
            "$group": {
                "_id": "$date",
                "total": {"$sum": 1}
            }
        },
        {"$sort": {"_id": -1}},
        {"$limit": 10}
    ]
    stats_por_data = list(collection.aggregate(pipeline_data))
    
    # Estatísticas por collect_id (coletas realizadas)
    pipeline_collect = [
        {
            "$match": {"collect_id": {"$exists": True}}
        },
        {
            "$group": {
                "_id": "$collect_id",
                "portal": {"$first": "$portal_name"},
                "total": {"$sum": 1},
                "data_coleta": {"$first": "$timestamp"}
            }
        },
        {"$sort": {"data_coleta": -1}}
    ]
    stats_por_coleta = list(collection.aggregate(pipeline_collect))
    
    return {
        "total_noticias": total_noticias,
        "total_portais": len(stats_por_portal),
        "total_coletas": len(stats_por_coleta),
        "por_portal": stats_por_portal,
        "ultimas_datas": stats_por_data,
        "coletas_realizadas": stats_por_coleta,
        "data_geracao": datetime.now().isoformat()
    }

def get_portal_statistics(collection, portal_name):
    """Obtém estatísticas de um portal específico."""
    
    # Total de notícias do portal
    total = collection.count_documents({"portal_name": portal_name})
    
    if total == 0:
        return None
    
    # Estatísticas por data
    pipeline_data = [
        {"$match": {"portal_name": portal_name}},
        {
            "$group": {
                "_id": "$date",
                "total": {"$sum": 1}
            }
        },
        {"$sort": {"_id": -1}}
    ]
    stats_por_data = list(collection.aggregate(pipeline_data))
    
    # Primeira e última notícia
    primeira = collection.find_one(
        {"portal_name": portal_name},
        sort=[("date", 1)]
    )
    ultima = collection.find_one(
        {"portal_name": portal_name},
        sort=[("date", -1)]
    )
    
    # Coletas realizadas para este portal
    pipeline_collect = [
        {"$match": {"portal_name": portal_name, "collect_id": {"$exists": True}}},
        {
            "$group": {
                "_id": "$collect_id",
                "total": {"$sum": 1},
                "data_coleta": {"$first": "$timestamp"}
            }
        },
        {"$sort": {"data_coleta": -1}}
    ]
    coletas = list(collection.aggregate(pipeline_collect))
    
    return {
        "portal_name": portal_name,
        "total_noticias": total,
        "primeira_noticia": {
            "data": primeira.get("date") if primeira else None,
            "titulo": primeira.get("title") if primeira else None,
            "url": primeira.get("url") if primeira else None
        },
        "ultima_noticia": {
            "data": ultima.get("date") if ultima else None,
            "titulo": ultima.get("title") if ultima else None,
            "url": ultima.get("url") if ultima else None
        },
        "distribuicao_por_data": stats_por_data,
        "coletas_realizadas": coletas,
        "data_geracao": datetime.now().isoformat()
    }

def print_statistics(stats, portal_name=None):
    """Imprime estatísticas de forma formatada."""
    
    if portal_name:
        # Estatísticas de portal específico
        if not stats:
            print(f"❌ Nenhuma notícia encontrada para o portal '{portal_name}'")
            return
        
        print("=" * 70)
        print(f"📊 ESTATÍSTICAS DO PORTAL: {stats['portal_name'].upper()}")
        print("=" * 70)
        print()
        print(f"📰 Total de notícias coletadas: {stats['total_noticias']:,}")
        print()
        
        if stats['primeira_noticia']['data']:
            print("📅 Primeira notícia:")
            print(f"   Data: {stats['primeira_noticia']['data']}")
            print(f"   Título: {stats['primeira_noticia']['titulo'][:80]}...")
            print()
        
        if stats['ultima_noticia']['data']:
            print("📅 Última notícia:")
            print(f"   Data: {stats['ultima_noticia']['data']}")
            print(f"   Título: {stats['ultima_noticia']['titulo'][:80]}...")
            print()
        
        print(f"🔄 Coletas realizadas: {len(stats['coletas_realizadas'])}")
        if stats['coletas_realizadas']:
            print()
            print("   Últimas 5 coletas:")
            for i, coleta in enumerate(stats['coletas_realizadas'][:5], 1):
                data_coleta = coleta.get('data_coleta', 'N/A')
                print(f"   {i}. {coleta['total']:,} notícias - {data_coleta}")
        
        print()
        print(f"📊 Distribuição por data (últimas 10):")
        for item in stats['distribuicao_por_data'][:10]:
            print(f"   {item['_id']}: {item['total']:,} notícias")
        
    else:
        # Estatísticas gerais
        print("=" * 70)
        print("📊 ESTATÍSTICAS GERAIS DA COLETA DE NOTÍCIAS")
        print("=" * 70)
        print()
        print(f"📰 Total de notícias: {stats['total_noticias']:,}")
        print(f"🌐 Total de portais: {stats['total_portais']}")
        print(f"🔄 Total de coletas: {stats['total_coletas']}")
        print()
        
        print("📊 Notícias por portal:")
        print()
        for portal in stats['por_portal']:
            nome = portal['_id'] or 'Desconhecido'
            total = portal['total']
            primeira = portal.get('primeira_data', 'N/A')
            ultima = portal.get('ultima_data', 'N/A')
            print(f"   • {nome:20} {total:6,} notícias  ({primeira} → {ultima})")
        
        print()
        print("📅 Notícias por data (últimas 10):")
        print()
        for item in stats['ultimas_datas']:
            data = item['_id']
            total = item['total']
            print(f"   • {data}: {total:,} notícias")
        
        if stats['coletas_realizadas']:
            print()
            print(f"🔄 Últimas 5 coletas realizadas:")
            print()
            for i, coleta in enumerate(stats['coletas_realizadas'][:5], 1):
                portal = coleta.get('portal', 'N/A')
                total = coleta['total']
                data_coleta = coleta.get('data_coleta', 'N/A')
                print(f"   {i}. {portal:15} {total:5,} notícias - {data_coleta}")
    
    print()
    print("=" * 70)
    print(f"📅 Gerado em: {stats['data_geracao']}")
    print("=" * 70)

def main():
    parser = argparse.ArgumentParser(
        description="Exporta estatísticas da coleta de notícias",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--portal",
        help="Nome do portal para estatísticas específicas"
    )
    parser.add_argument(
        "--export",
        help="Exportar estatísticas para arquivo JSON"
    )
    parser.add_argument(
        "--list-portals",
        action="store_true",
        help="Listar todos os portais disponíveis"
    )
    
    args = parser.parse_args()
    
    # Conectar ao MongoDB
    print("🔌 Conectando ao MongoDB...")
    client = connect_mongodb()
    db = client[DATABASE]
    collection = db[COLLECTION]
    print("✅ Conectado com sucesso!")
    print()
    
    # Listar portais
    if args.list_portals:
        portals = collection.distinct("portal_name")
        print("📋 Portais disponíveis:")
        for portal in sorted(portals):
            count = collection.count_documents({"portal_name": portal})
            print(f"   • {portal}: {count:,} notícias")
        client.close()
        return
    
    # Obter estatísticas
    if args.portal:
        stats = get_portal_statistics(collection, args.portal)
    else:
        stats = get_general_statistics(collection)
    
    # Imprimir estatísticas
    print_statistics(stats, args.portal)
    
    # Exportar para JSON se solicitado
    if args.export:
        with open(args.export, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2, default=str)
        print()
        print(f"✅ Estatísticas exportadas para: {args.export}")
    
    client.close()

if __name__ == "__main__":
    main()
