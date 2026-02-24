#!/usr/bin/env python3
"""
Script para testar o coletor de notícias de forma standalone
Autor: Paulo (iniciante em Python)
Data: 22/01/2026

Este script permite testar o coletor sem executar todo o fluxo de classificação.
Os resultados são salvos em arquivos JSON para inspeção.
"""

import sys
import os
import json
from datetime import datetime

# Adicionar o diretório pai ao path para importar o main.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import CollectorNoticias

def test_single_portal(portal_name, target_date=None):
    """
    Testa um único portal e salva o resultado em JSON
    
    Args:
        portal_name: Nome do portal (ex: 'ndmais', 'nsc', 'g1sc')
        target_date: Data alvo no formato 'DD/MM/YYYY' ou None para hoje
    """
    print("="*70)
    print(f"🔍 TESTANDO PORTAL: {portal_name}")
    print("="*70)
    
    # Criar instância do coletor
    collector = CollectorNoticias()
    
    # Configurar data alvo
    if target_date:
        collector.target_date = datetime.strptime(target_date, '%d/%m/%Y').date()
        print(f"📅 Data alvo: {target_date}")
    else:
        collector.target_date = datetime.now().date()
        print(f"📅 Data alvo: hoje ({collector.target_date})")
    
    # Coletar notícias
    print(f"\n🚀 Iniciando coleta...\n")
    articles = collector.collect_data(portal_name)
    
    # Resultados
    print(f"\n{'='*70}")
    print(f"📊 RESULTADOS")
    print(f"{'='*70}")
    print(f"✅ Total de artigos coletados: {len(articles)}")
    
    if articles:
        # Salvar em JSON
        output_file = f"resultado_{portal_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"💾 Resultados salvos em: {output_file}")
        
        # Mostrar primeiros 3 artigos
        print(f"\n📰 Primeiros 3 artigos:")
        for i, article in enumerate(articles[:3], 1):
            print(f"\n   [{i}] {article.get('title', 'Sem título')[:60]}")
            print(f"       Data: {article.get('date', 'Sem data')}")
            print(f"       URL: {article.get('url', 'Sem URL')[:70]}")
    else:
        print(f"⚠️  Nenhum artigo encontrado para a data especificada")
    
    print(f"{'='*70}\n")
    return articles

def test_multiple_portals(portal_list, target_date=None):
    """
    Testa múltiplos portais e salva resultados consolidados
    
    Args:
        portal_list: Lista de nomes de portais
        target_date: Data alvo no formato 'DD/MM/YYYY' ou None para hoje
    """
    print("="*70)
    print(f"🔍 TESTANDO {len(portal_list)} PORTAIS")
    print("="*70)
    
    all_results = {}
    total_articles = 0
    
    for portal_name in portal_list:
        print(f"\n📰 Portal: {portal_name}")
        print("-"*70)
        
        try:
            collector = CollectorNoticias()
            
            if target_date:
                collector.target_date = datetime.strptime(target_date, '%d/%m/%Y').date()
            else:
                collector.target_date = datetime.now().date()
            
            articles = collector.collect_data(portal_name)
            
            all_results[portal_name] = {
                'success': True,
                'article_count': len(articles),
                'articles': articles
            }
            
            total_articles += len(articles)
            print(f"✅ {portal_name}: {len(articles)} artigos")
            
        except Exception as e:
            print(f"❌ {portal_name}: ERRO - {str(e)}")
            all_results[portal_name] = {
                'success': False,
                'error': str(e),
                'article_count': 0
            }
    
    # Salvar resultados consolidados
    output_file = f"resultado_multiplos_portais_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    
    # Resumo
    print(f"\n{'='*70}")
    print(f"📊 RESUMO FINAL")
    print(f"{'='*70}")
    print(f"✅ Portais testados: {len(portal_list)}")
    print(f"📰 Total de artigos: {total_articles}")
    print(f"💾 Resultados salvos em: {output_file}")
    
    successful = [p for p, r in all_results.items() if r['success']]
    print(f"\n✅ Portais com sucesso: {len(successful)}/{len(portal_list)}")
    for portal in successful:
        print(f"   • {portal}: {all_results[portal]['article_count']} artigos")
    
    failed = [p for p, r in all_results.items() if not r['success']]
    if failed:
        print(f"\n❌ Portais com erro: {len(failed)}")
        for portal in failed:
            print(f"   • {portal}: {all_results[portal]['error'][:50]}")
    
    print(f"{'='*70}\n")
    return all_results

def main():
    """
    Função principal - exemplos de uso
    """
    print("\n" + "="*70)
    print("🚀 TESTE DO COLETOR DE NOTÍCIAS")
    print("="*70)
    print("\nEscolha uma opção:")
    print("\n1. Testar um único portal")
    print("2. Testar todos os 9 portais funcionais")
    print("3. Testar portais específicos")
    print("\n" + "="*70)
    
    choice = input("\nDigite o número da opção (1, 2 ou 3): ").strip()
    
    if choice == '1':
        # Opção 1: Testar um único portal
        print("\nPortais disponíveis:")
        portals = ['ndmais', 'nsc', 'jornalconexao', 'olharsc', 'agoralaguna', 
                   'ocpnews', 'jornalsulbrasil', 'iclnoticias', 'g1sc']
        for i, p in enumerate(portals, 1):
            print(f"  {i}. {p}")
        
        portal_choice = input("\nDigite o nome do portal: ").strip()
        date_input = input("Data alvo (DD/MM/YYYY) ou Enter para hoje: ").strip()
        
        target_date = date_input if date_input else None
        test_single_portal(portal_choice, target_date)
    
    elif choice == '2':
        # Opção 2: Testar todos os 9 portais
        portals = ['ndmais', 'nsc', 'jornalconexao', 'olharsc', 'agoralaguna', 
                   'ocpnews', 'jornalsulbrasil', 'iclnoticias', 'g1sc']
        
        date_input = input("\nData alvo (DD/MM/YYYY) ou Enter para hoje: ").strip()
        target_date = date_input if date_input else None
        
        test_multiple_portals(portals, target_date)
    
    elif choice == '3':
        # Opção 3: Testar portais específicos
        print("\nDigite os nomes dos portais separados por vírgula")
        print("Exemplo: ndmais, nsc, g1sc")
        portals_input = input("\nPortais: ").strip()
        portals = [p.strip() for p in portals_input.split(',')]
        
        date_input = input("Data alvo (DD/MM/YYYY) ou Enter para hoje: ").strip()
        target_date = date_input if date_input else None
        
        test_multiple_portals(portals, target_date)
    
    else:
        print("\n❌ Opção inválida!")

if __name__ == '__main__':
    main()
