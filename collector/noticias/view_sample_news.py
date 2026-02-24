#!/usr/bin/env python3
"""
Script para visualizar uma notícia de exemplo do MongoDB.
"""

import os
import json
from pymongo import MongoClient

# Configurações do MongoDB
MONGO_HOST = os.getenv("HOST_MONGODB", "localhost")
MONGO_PORT = int(os.getenv("PORT_MONGODB", "27017"))
MONGO_USER = os.getenv("USERNAME_MONGODB", "local")
MONGO_PASS = os.getenv("SENHA_MONGODB", "locallocallocal")
MONGO_AUTH_DB = os.getenv("DATABASE_AUTENTICACAO_MONGODB", "admin")

def connect_mongodb():
    """Conecta ao MongoDB."""
    try:
        client = MongoClient(
            host=MONGO_HOST,
            port=MONGO_PORT,
            username=MONGO_USER,
            password=MONGO_PASS,
            authSource=MONGO_AUTH_DB,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command('ismaster')
        return client
    except Exception as e:
        print(f"❌ Erro ao conectar ao MongoDB: {e}")
        return None

def main():
    print("🔌 Conectando ao MongoDB...")
    client = connect_mongodb()
    if not client:
        return
    
    print("✅ Conectado!")
    print()
    
    # Listar databases
    print("📚 Databases disponíveis:")
    for db_name in client.list_database_names():
        print(f"   • {db_name}")
    print()
    
    # Verificar database noticias
    db = client['noticias']
    collections = db.list_collection_names()
    
    print("📁 Collections no database 'noticias':")
    if not collections:
        print("   ⚠️  Nenhuma collection encontrada!")
        print()
        print("💡 Isso significa que:")
        print("   - O collector ainda não salvou nenhuma notícia, OU")
        print("   - As notícias estão sendo salvas em outro database")
        print()
        
        # Verificar outros databases
        print("🔍 Procurando em outros databases...")
        for db_name in client.list_database_names():
            if db_name in ['admin', 'config', 'local']:
                continue
            db_temp = client[db_name]
            colls = db_temp.list_collection_names()
            if colls:
                print(f"\n   Database '{db_name}':")
                for coll in colls:
                    count = db_temp[coll].count_documents({})
                    print(f"      • {coll}: {count} documentos")
                    
                    if count > 0:
                        print(f"\n📰 Exemplo de notícia em '{db_name}.{coll}':")
                        print("="*70)
                        sample = db_temp[coll].find_one()
                        print(json.dumps(sample, indent=2, default=str, ensure_ascii=False))
                        print("="*70)
                        client.close()
                        return
    else:
        for coll_name in collections:
            count = db[coll_name].count_documents({})
            print(f"   • {coll_name}: {count} documentos")
        print()
        
        # Buscar uma notícia de exemplo
        for coll_name in collections:
            count = db[coll_name].count_documents({})
            if count > 0:
                print(f"📰 Exemplo de notícia da collection '{coll_name}':")
                print("="*70)
                sample = db[coll_name].find_one()
                print(json.dumps(sample, indent=2, default=str, ensure_ascii=False))
                print("="*70)
                
                print()
                print("📊 Campos disponíveis:")
                for key in sample.keys():
                    value = sample[key]
                    if isinstance(value, str) and len(value) > 50:
                        preview = value[:50] + "..."
                    else:
                        preview = value
                    print(f"   • {key}: {preview}")
                
                client.close()
                return
    
    print()
    print("⚠️  Nenhuma notícia encontrada no MongoDB ainda.")
    print("💡 O collector pode estar ainda coletando. Aguarde alguns minutos e tente novamente.")
    
    client.close()

if __name__ == "__main__":
    main()
