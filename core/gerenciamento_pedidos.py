import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path
from utils.helpers import parse_pratos

PEDIDOS_PATH = "data/processed/pedidos.csv"

def criar_pedido(pratos, mesa, observacoes=""):
    pedidos = carregar_pedidos()
    
    # Garante que os pratos são serializáveis
    pratos_serializados = []
    for prato in pratos:
        if isinstance(prato, dict):
            pratos_serializados.append(prato)
        else:
            pratos_serializados.append({"prato": str(prato)})
    
    novo_id = pedidos['id_pedido'].max() + 1 if not pedidos.empty else 1
    
    novo_pedido = pd.DataFrame([{
        "id_pedido": novo_id,
        "pratos": json.dumps(pratos_serializados),  # Serializa corretamente
        "mesa": mesa,
        "status": "recebido",
        "data_criacao": datetime.now().isoformat(),
        "data_atualizacao": datetime.now().isoformat(),
        "observacoes": observacoes
    }])
    
    pedidos = pd.concat([pedidos, novo_pedido], ignore_index=True)
    salvar_pedidos(pedidos)
    
    return novo_id

def atualizar_status_pedido(id_pedido, novo_status):
    pedidos = carregar_pedidos()
    
    if id_pedido not in pedidos['id_pedido'].values:
        raise ValueError("Pedido não encontrado")
    
    pedidos.loc[pedidos['id_pedido'] == id_pedido, 'status'] = novo_status
    pedidos.loc[pedidos['id_pedido'] == id_pedido, 'data_atualizacao'] = datetime.now().isoformat()
    
    salvar_pedidos(pedidos)
    
    # Se o pedido foi entregue, atualiza o estoque
    if novo_status == 'entregue':
        from core.gerenciamento_estoque import atualizar_estoque_pedido
        atualizar_estoque_pedido(id_pedido)
    
    return True

def listar_pedidos_por_status(status=None):
    pedidos = carregar_pedidos()
    
    if not pedidos.empty:
        if status:
            return pedidos[pedidos['status'] == status]
        return pedidos
    return pd.DataFrame()  # Retorna DataFrame vazio se não houver pedidos

def carregar_pedidos():
    os.makedirs(os.path.dirname(PEDIDOS_PATH), exist_ok=True)
    if os.path.exists(PEDIDOS_PATH):
        df = pd.read_csv(PEDIDOS_PATH)
        df['pratos'] = df['pratos'].apply(parse_pratos)
        return df
    return pd.DataFrame(columns=["id_pedido", "pratos", "mesa", "status", "data_criacao", "data_atualizacao", "observacoes"])

def parse_pratos(pratos_str):
    try:
        pratos = json.loads(pratos_str)
        # Garante que cada item seja um dicionário com as chaves corretas
        return [normalizar_item_prato(item) for item in pratos]
    except:
        return [{"prato": "Item inválido", "preco": 0.0}]

def normalizar_item_prato(item):
    if isinstance(item, dict):
        return {
            "prato": item.get("prato", "Item sem nome"),
            "preco": float(item.get("preco", 0.0))
        }
    return {"prato": str(item), "preco": 0.0}

def criar_dataframe_vazio():
    return pd.DataFrame(columns=[
        "id_pedido", "pratos", "mesa", "status", 
        "data_criacao", "data_atualizacao", "observacoes"
    ])

def salvar_pedidos(df):
    os.makedirs(os.path.dirname(PEDIDOS_PATH), exist_ok=True)
    # Converte a lista de pratos para string JSON antes de salvar
    df['pratos'] = df['pratos'].apply(lambda x: json.dumps(x))
    df.to_csv(PEDIDOS_PATH, index=False)