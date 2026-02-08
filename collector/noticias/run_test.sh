#!/bin/bash
# Script para rodar o teste do coletor com as configurações corretas

# Ativar ambiente virtual e configurar PYTHONPATH
source /home/paulo/projects/main-server/.venv/bin/activate
export PYTHONPATH=/home/paulo/projects/main-server:$PYTHONPATH

# Rodar o teste
python3 test_collector.py
