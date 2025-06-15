import pandas as pd
import os
from datetime import datetime
from pathlib import Path

INGREDIENTES_PATH = "data/raw/ingredientes.csv"
PEDIDOS_PATH = "data/processed/pedidos.csv"

def carregar_ingredientes():
    if os.path.exists(INGREDIENTES_PATH):
        df = pd.read_csv(INGREDIENTES_PATH)
        return df
    return pd.DataFrame(columns=["nome", "quantidade", "unidade", "estoque_minimo", "fornecedor"])

def salvar_ingredientes(df):
    os.makedirs(os.path.dirname(INGREDIENTES_PATH), exist_ok=True)
    df.to_csv(INGREDIENTES_PATH, index=False)

def carregar_pedidos():
    if os.path.exists(PEDIDOS_PATH):
        return pd.read_csv(PEDIDOS_PATH)
    return pd.DataFrame(columns=[
        "id_pedido", "pratos", "mesa", "status", 
        "data_criacao", "data_atualizacao", "observacoes"
    ])

def salvar_pedidos(df):
    os.makedirs(os.path.dirname(PEDIDOS_PATH), exist_ok=True)
    df.to_csv(PEDIDOS_PATH, index=False)

def atualizar_estoque_pedido(id_pedido):
    pedidos = carregar_pedidos()
    ingredientes = carregar_ingredientes()
    
    pedido = pedidos[pedidos['id_pedido'] == id_pedido].iloc[0]
    if pedido['status'] != 'entregue':
        raise ValueError("Só pode atualizar estoque de pedidos entregues")
    
    # Implementar a lógica para baixar os ingredientes
    # Integrando com o gerenciamento_pratos.py
    
    salvar_ingredientes(ingredientes)
    return True

def adicionar_ingrediente(ingrediente):
    df = carregar_ingredientes()
    novo_item = pd.DataFrame([ingrediente])
    df = pd.concat([df, novo_item], ignore_index=True)
    salvar_ingredientes(df)
    return True

def verificar_estoque_baixo(limite=None):
    df = carregar_ingredientes()
    if limite:
        return df[df['quantidade'] < limite]
    return df[df['quantidade'] < df['estoque_minimo']]