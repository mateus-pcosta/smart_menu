import json
import os
import pandas as pd
from pathlib import Path

PRATOS_PATH = "data/raw/pratos/"
CARDAPIO_PATH = "data/raw/cardapio.json"
INGREDIENTES_PATH = "data/raw/ingredientes.csv"

def carregar_cardapio():
    if os.path.exists(CARDAPIO_PATH):
        with open(CARDAPIO_PATH, 'r', encoding='utf-8-sig') as f:  # Alterado para utf-8-sig
            return json.load(f)
    return {"pratos": [], "atualizado_em": None}

def carregar_prato(nome_arquivo):
    caminho = os.path.join(PRATOS_PATH, nome_arquivo)
    if os.path.exists(caminho):
        with open(caminho, 'r', encoding='utf-8-sig') as f:  # Alterado para utf-8-sig
            return json.load(f)
    return None

def carregar_todos_pratos():
    cardapio = carregar_cardapio()
    pratos = []
    for item in cardapio['pratos']:
        prato = carregar_prato(item['arquivo'])
        if prato:
            pratos.append(prato)
    return pratos

def adicionar_prato_ao_cardapio(nome_arquivo, dados_prato):
    # Salva o arquivo do prato
    caminho_prato = os.path.join(PRATOS_PATH, nome_arquivo)
    os.makedirs(PRATOS_PATH, exist_ok=True)
    
    with open(caminho_prato, 'w', encoding='utf-8') as f:
        json.dump(dados_prato, f, ensure_ascii=False, indent=2)
    
    # Atualiza o cardápio
    cardapio = carregar_cardapio()
    cardapio['pratos'].append({
        "nome": dados_prato['nome'],
        "arquivo": nome_arquivo,
        "categoria": dados_prato['categoria']
    })
    cardapio['atualizado_em'] = pd.Timestamp.now().isoformat()
    
    with open(CARDAPIO_PATH, 'w', encoding='utf-8') as f:
        json.dump(cardapio, f, ensure_ascii=False, indent=2)
    
    return True

def calcular_ingredientes_necessarios(pedidos):
    ingredientes_totais = {}
    
    for pedido in pedidos:
        prato = carregar_prato(pedido['prato'])
        if not prato:
            continue
            
        for ingrediente in prato['ingredientes']:
            nome = ingrediente['nome']
            quantidade = ingrediente['quantidade'] * pedido['quantidade']
            
            if nome in ingredientes_totais:
                ingredientes_totais[nome] += quantidade
            else:
                ingredientes_totais[nome] = quantidade
                
    return ingredientes_totais

def verificar_disponibilidade(prato_nome):
    prato = next((p for p in carregar_todos_pratos() if p['nome'] == prato_nome), None)
    if not prato:
        return False
        
    estoque = pd.read_csv(INGREDIENTES_PATH)
    
    for ingrediente in prato['ingredientes']:
        item_estoque = estoque[estoque['nome'] == ingrediente['nome']]
        if item_estoque.empty or item_estoque.iloc[0]['quantidade'] < ingrediente['quantidade']:
            return False
            
    return True