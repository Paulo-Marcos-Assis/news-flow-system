#!/usr/bin/env python3
import json
import os
import re
from datetime import datetime

def convert_br_number_to_float(value):
    """Convert Brazilian number format (comma as decimal) to float"""
    if isinstance(value, str):
        # Remove any whitespace
        value = value.strip()
        # Replace comma with dot
        value = value.replace(',', '.')
        try:
            return float(value)
        except ValueError:
            return value
    elif isinstance(value, (int, float)):
        return float(value)
    return value

def convert_date(date_str):
    """Convert date to YYYY-MM-DD format"""
    if not isinstance(date_str, str):
        return date_str
    
    date_str = date_str.strip()
    
    # Try DD/MM/YYYY HH:MM:SS format
    match = re.match(r'(\d{2})/(\d{2})/(\d{4})', date_str)
    if match:
        day, month, year = match.groups()
        return f"{year}-{month}-{day}"
    
    # Try YYYY-MM-DD HH:MM:SS format - remove time
    match = re.match(r'(\d{4}-\d{2}-\d{2})', date_str)
    if match:
        return match.group(1)
    
    return date_str

def fix_cotacao(cotacao):
    """Fix cotacao object types"""
    if 'valor_cotado' in cotacao:
        cotacao['valor_cotado'] = convert_br_number_to_float(cotacao['valor_cotado'])
    if 'qt_item_cotado' in cotacao:
        cotacao['qt_item_cotado'] = convert_br_number_to_float(cotacao['qt_item_cotado'])
    if 'classificacao' in cotacao:
        # Keep as string
        cotacao['classificacao'] = str(cotacao['classificacao'])
    # Add vencedor field if missing (default to false, will need manual correction for winners)
    if 'vencedor' not in cotacao:
        # Try to infer from classificacao
        if cotacao.get('classificacao') == '1':
            cotacao['vencedor'] = True
        else:
            cotacao['vencedor'] = False
    return cotacao

def fix_pessoa(pessoa):
    """Fix pessoa object types"""
    if 'processo_licitatorio_pessoa' in pessoa:
        plp = pessoa['processo_licitatorio_pessoa']
        if 'cnpj_consorcio' in plp:
            plp['cnpj_consorcio'] = str(plp['cnpj_consorcio'])
    
    if 'cotacao' in pessoa:
        for cotacao in pessoa['cotacao']:
            fix_cotacao(cotacao)
    
    return pessoa

def fix_item_licitacao(item):
    """Fix item_licitacao object types"""
    if 'valor_estimado_item' in item:
        item['valor_estimado_item'] = convert_br_number_to_float(item['valor_estimado_item'])
    if 'qtd_item_licitacao' in item:
        item['qtd_item_licitacao'] = convert_br_number_to_float(item['qtd_item_licitacao'])
    if 'numero_sequencial_item' in item:
        val = item['numero_sequencial_item']
        if isinstance(val, str):
            val = val.replace('.0', '')
        item['numero_sequencial_item'] = int(float(str(val)))
    
    if 'pessoa' in item:
        for pessoa in item['pessoa']:
            fix_pessoa(pessoa)
    
    return item

def fix_pagamento_empenho(pagamento):
    """Fix pagamento_empenho object types"""
    if 'data_exigibilidade' in pagamento:
        pagamento['data_exigibilidade'] = convert_date(pagamento['data_exigibilidade'])
    if 'data_pagamento' in pagamento:
        pagamento['data_pagamento'] = convert_date(pagamento['data_pagamento'])
    if 'valor_pagamento' in pagamento:
        pagamento['valor_pagamento'] = convert_br_number_to_float(pagamento['valor_pagamento'])
    if 'nro_ordem_bancaria' in pagamento:
        val = pagamento['nro_ordem_bancaria']
        if isinstance(val, str):
            val = val.replace('.0', '')
        pagamento['nro_ordem_bancaria'] = int(float(str(val)))
    if 'cod_agencia' in pagamento:
        val = pagamento['cod_agencia']
        if isinstance(val, str):
            val = val.replace('.0', '')
        pagamento['cod_agencia'] = int(float(str(val)))
    if 'cod_banco' in pagamento:
        val = pagamento['cod_banco']
        if isinstance(val, str):
            val = val.replace('.0', '')
        pagamento['cod_banco'] = int(float(str(val)))
    
    return pagamento

def fix_liquidacao(liquidacao):
    """Fix liquidacao object types"""
    if 'valor_liquidacao' in liquidacao:
        liquidacao['valor_liquidacao'] = convert_br_number_to_float(liquidacao['valor_liquidacao'])
    if 'data_liquidacao' in liquidacao:
        liquidacao['data_liquidacao'] = convert_date(liquidacao['data_liquidacao'])
    if 'nota_liquidacao' in liquidacao:
        # Convert to string
        val = liquidacao['nota_liquidacao']
        if isinstance(val, bool):
            liquidacao['nota_liquidacao'] = "0"
        else:
            liquidacao['nota_liquidacao'] = str(val)
    
    if 'pagamento_empenho' in liquidacao:
        # pagamento_empenho should be a dict, not a list
        if isinstance(liquidacao['pagamento_empenho'], dict):
            fix_pagamento_empenho(liquidacao['pagamento_empenho'])
        elif isinstance(liquidacao['pagamento_empenho'], list):
            # If it's a list, take the first element
            if len(liquidacao['pagamento_empenho']) > 0:
                liquidacao['pagamento_empenho'] = liquidacao['pagamento_empenho'][0]
                fix_pagamento_empenho(liquidacao['pagamento_empenho'])
    
    return liquidacao

def fix_empenho(empenho):
    """Fix empenho object types"""
    if 'valor_empenho' in empenho:
        empenho['valor_empenho'] = convert_br_number_to_float(empenho['valor_empenho'])
    if 'data_empenho' in empenho:
        empenho['data_empenho'] = convert_date(empenho['data_empenho'])
    if 'num_empenho' in empenho:
        val = empenho['num_empenho']
        if isinstance(val, str):
            val = val.replace('.0', '')
        empenho['num_empenho'] = int(float(str(val)))
    
    # prestacao_contas should be string "0", not boolean
    if 'prestacao_contas' in empenho:
        val = empenho['prestacao_contas']
        if isinstance(val, bool):
            empenho['prestacao_contas'] = "0"
        else:
            empenho['prestacao_contas'] = str(val)
    else:
        empenho['prestacao_contas'] = "0"
    
    # regularizacao_orcamentaria should be boolean
    if 'regularizacao_orcamentaria' not in empenho:
        empenho['regularizacao_orcamentaria'] = False
    elif not isinstance(empenho['regularizacao_orcamentaria'], bool):
        empenho['regularizacao_orcamentaria'] = False
    
    # Handle pagamento_empenho at empenho level (should be moved to liquidacao)
    if 'pagamento_empenho' in empenho:
        pagamentos = empenho['pagamento_empenho']
        if isinstance(pagamentos, list):
            # Move to liquidacao
            if 'liquidacao' not in empenho:
                empenho['liquidacao'] = []
            
            # If there's already liquidacao, add pagamento to first one
            if len(empenho['liquidacao']) > 0:
                if 'pagamento_empenho' not in empenho['liquidacao'][0]:
                    if len(pagamentos) > 0:
                        empenho['liquidacao'][0]['pagamento_empenho'] = pagamentos[0]
                        fix_pagamento_empenho(empenho['liquidacao'][0]['pagamento_empenho'])
            
            # Remove from empenho level
            del empenho['pagamento_empenho']
    
    if 'liquidacao' in empenho:
        for liquidacao in empenho['liquidacao']:
            fix_liquidacao(liquidacao)
    
    return empenho

def fix_contrato(contrato):
    """Fix contrato object types"""
    if 'valor_contrato' in contrato:
        contrato['valor_contrato'] = convert_br_number_to_float(contrato['valor_contrato'])
    if 'valor_garantia' in contrato:
        contrato['valor_garantia'] = convert_br_number_to_float(contrato['valor_garantia'])
    if 'data_assinatura' in contrato:
        contrato['data_assinatura'] = convert_date(contrato['data_assinatura'])
    if 'data_vencimento' in contrato:
        contrato['data_vencimento'] = convert_date(contrato['data_vencimento'])
    
    return contrato

def fix_processo_licitatorio(processo):
    """Fix processo_licitatorio object types"""
    if 'valor_total_previsto' in processo:
        processo['valor_total_previsto'] = convert_br_number_to_float(processo['valor_total_previsto'])
    if 'data_abertura_certame' in processo:
        processo['data_abertura_certame'] = convert_date(processo['data_abertura_certame'])
    
    if 'item_licitacao' in processo:
        for item in processo['item_licitacao']:
            fix_item_licitacao(item)
    
    if 'empenho' in processo:
        for empenho in processo['empenho']:
            fix_empenho(empenho)
    
    if 'contrato' in processo:
        for contrato in processo['contrato']:
            fix_contrato(contrato)
    
    return processo

def fix_json_file(filepath):
    """Fix data types in a JSON file"""
    print(f"Processing {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'processo_licitatorio' in data:
        fix_processo_licitatorio(data['processo_licitatorio'])
    
    # Write back with proper formatting
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Fixed {filepath}")

def main():
    # Directory containing the files to fix
    directory = '/home/gabriel/ceos/linha1/main2/main-server/inserter-updater/esfinge_tests/sfinge_examples'
    
    # Get all JSON files
    json_files = [f for f in os.listdir(directory) if f.endswith('.json')]
    json_files.sort()
    
    print(f"Found {len(json_files)} JSON files to process\n")
    
    for filename in json_files:
        filepath = os.path.join(directory, filename)
        try:
            fix_json_file(filepath)
        except Exception as e:
            print(f"✗ Error processing {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✓ Completed processing {len(json_files)} files")

if __name__ == '__main__':
    main()
