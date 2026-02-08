#!/bin/sh
set -e

# Instala curl (necessário para autenticação HTTP)
apk add --no-cache curl > /dev/null 2>&1

# Configurações do OrientDB
ORIENTDB_HOST="${HOST_ORIENT:-localhost}"
ORIENTDB_PORT="${PORT_ORIENT:-2480}"
ORIENTDB_USER="${USERNAME_ORIENT:-admin}"
ORIENTDB_PASSWORD="${SENHA_ORIENT:-admin}"
DATABASE_NAME="${DATABASE_ORIENT:-teste}"

echo "Aguardando OrientDB iniciar em ${ORIENTDB_HOST}:${ORIENTDB_PORT}..."

# Aguarda o OrientDB estar pronto
MAX_RETRIES=30
RETRY_COUNT=0
until wget --spider --quiet --tries=1 --timeout=2 "http://${ORIENTDB_HOST}:${ORIENTDB_PORT}/listDatabases" 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERRO: OrientDB não respondeu após ${MAX_RETRIES} tentativas"
        exit 1
    fi
    echo "Tentativa ${RETRY_COUNT}/${MAX_RETRIES}: OrientDB ainda não está pronto..."
    sleep 2
done

echo "OrientDB está pronto!"

# Verifica se o banco de dados já existe
echo "Verificando se o banco de dados '${DATABASE_NAME}' existe..."
DATABASES=$(curl -s -u "${ORIENTDB_USER}:${ORIENTDB_PASSWORD}" \
    "http://${ORIENTDB_HOST}:${ORIENTDB_PORT}/listDatabases")

if echo "$DATABASES" | grep -q "\"${DATABASE_NAME}\""; then
    echo "Banco de dados '${DATABASE_NAME}' já existe. Nada a fazer."
else
    echo "Criando banco de dados '${DATABASE_NAME}'..."
    
    # Cria o banco de dados como graph database
    RESULT=$(curl -s -u "${ORIENTDB_USER}:${ORIENTDB_PASSWORD}" \
        -X POST \
        "http://${ORIENTDB_HOST}:${ORIENTDB_PORT}/database/${DATABASE_NAME}/plocal/graph")
    
    if [ $? -eq 0 ]; then
        echo "✓ Banco de dados '${DATABASE_NAME}' criado com sucesso!"
    else
        echo "✗ ERRO ao criar banco de dados '${DATABASE_NAME}'"
        exit 1
    fi
fi

echo "Inicialização do OrientDB concluída!"
