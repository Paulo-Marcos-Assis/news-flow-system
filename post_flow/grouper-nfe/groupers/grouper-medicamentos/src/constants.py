# Arquivo: src/constants.py
import os

# 1. Encontrar a raiz do projeto de forma dinâmica e confiável
#    __file__ é o caminho para este arquivo (constants.py)
#    os.path.dirname(__file__) é a pasta onde ele está ('src/')
#    '..' sobe um nível para a raiz do projeto ('i2e/')
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# 2. Construir o caminho completo para o params.yaml a partir da raiz
PARAMS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../params.yaml"))
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../config.yaml"))

# Você pode definir outros caminhos importantes aqui também
# Exemplo:
# DATA_DIR = os.path.join(PROJECT_ROOT, 'data')