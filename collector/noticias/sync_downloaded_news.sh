#!/bin/bash

# Script para sincronizar arquivos de notícias do container para o host
# Uso: ./sync_downloaded_news.sh

CONTAINER_NAME="main-server-collector-noticias-1"
CONTAINER_PATH="/app/downloaded_news"
HOST_PATH="/home/paulo/projects/main-server/collector/noticias/downloaded_news"

echo "🔄 Sincronizando arquivos de notícias do container para o host..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verificar se o container está rodando
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Container $CONTAINER_NAME não está rodando!"
    exit 1
fi

# Listar pastas dentro do container
echo "📂 Verificando pastas no container..."
PORTALS=$(docker exec "$CONTAINER_NAME" ls -1 "$CONTAINER_PATH" 2>/dev/null | grep -v "README.md" | grep -v "RELATORIO" || echo "")

if [ -z "$PORTALS" ]; then
    echo "⚠️  Nenhuma pasta de portal encontrada no container."
    exit 0
fi

echo "📋 Portais encontrados:"
echo "$PORTALS" | while read portal; do
    echo "   - $portal"
done
echo ""

# Copiar cada pasta de portal
echo "$PORTALS" | while read portal; do
    if [ -d "$HOST_PATH/$portal" ]; then
        echo "🔄 Atualizando: $portal"
        rm -rf "$HOST_PATH/$portal"
    else
        echo "📥 Copiando novo portal: $portal"
    fi
    
    docker cp "$CONTAINER_NAME:$CONTAINER_PATH/$portal" "$HOST_PATH/" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        # Contar arquivos JSON
        COUNT=$(find "$HOST_PATH/$portal" -name "*.json" ! -name "*_all_articles.json" 2>/dev/null | wc -l)
        SIZE=$(du -sh "$HOST_PATH/$portal" 2>/dev/null | cut -f1)
        echo "   ✅ $COUNT notícias ($SIZE)"
    else
        echo "   ❌ Erro ao copiar $portal"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Sincronização concluída!"
echo ""
echo "📊 Resumo total:"
TOTAL_NOTICIAS=$(find "$HOST_PATH" -name "*.json" ! -name "*_all_articles.json" 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "$HOST_PATH" 2>/dev/null | cut -f1)
echo "   Total de notícias: $TOTAL_NOTICIAS"
echo "   Tamanho total: $TOTAL_SIZE"
echo ""
echo "📁 Localização: $HOST_PATH"
