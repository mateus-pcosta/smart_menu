import pandas as pd
import json
import os
from datetime import datetime

PEDIDOS_PATH = "data/processed/pedidos.csv"

def criar_pedido(pratos, mesa, observacoes=""):
    pedidos = carregar_pedidos()
    
    pratos_normalizados = []
    for item in pratos:
        if isinstance(item, dict):
            pratos_normalizados.append({
                "prato": item.get("prato", item.get("nome", "Item sem nome")),
                "preco": float(item.get("preco", 0))
            })
        else:
            pratos_normalizados.append({
                "prato": str(item),
                "preco": 0.0
            })
    
    novo_id = pedidos['id_pedido'].max() + 1 if not pedidos.empty else 1
    
    novo_pedido = pd.DataFrame([{
        "id_pedido": novo_id,
        "pratos": json.dumps(pratos_normalizados, ensure_ascii=False),
        "mesa": mesa,
        "status": "recebido",
        "data_criacao": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "data_atualizacao": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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
    pedidos.loc[pedidos['id_pedido'] == id_pedido, 'data_atualizacao'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    salvar_pedidos(pedidos)
    
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
    return pd.DataFrame()

def carregar_pedidos():
    os.makedirs(os.path.dirname(PEDIDOS_PATH), exist_ok=True)
    
    if os.path.exists(PEDIDOS_PATH):
        try:
            df = pd.read_csv(PEDIDOS_PATH)
            
            def parse_pratos(pratos_str):
                if not isinstance(pratos_str, str):
                    return []
                try:
                    return json.loads(pratos_str)
                except json.JSONDecodeError:
                    # Tenta limpar a string para consertar problemas simples
                    try:
                        s = pratos_str.strip()
                        if s.startswith('"') and s.endswith('"'):
                            s = s[1:-1]
                        s = s.replace('\\"', '"').replace('""', '"')
                        return json.loads(s)
                    except Exception:
                        return [{"prato": "Item inválido", "preco": 0.0}]
                except Exception:
                    return [{"prato": "Item inválido", "preco": 0.0}]
            
            df['pratos'] = df['pratos'].apply(parse_pratos)
            return df
        except Exception as e:
            print(f"Erro ao carregar pedidos: {str(e)}")
            return criar_dataframe_vazio()
    
    return criar_dataframe_vazio()

def salvar_pedidos(df):
    try:
        def to_json_safe(x):
            if isinstance(x, list):
                return json.dumps(x, ensure_ascii=False)
            elif isinstance(x, str):
                try:
                    json.loads(x)
                    return x
                except:
                    return json.dumps(x, ensure_ascii=False)
            else:
                return '[]'

        df['pratos'] = df['pratos'].apply(to_json_safe)
        os.makedirs(os.path.dirname(PEDIDOS_PATH), exist_ok=True)
        df.to_csv(PEDIDOS_PATH, index=False)
    except Exception as e:
        print(f"Erro ao salvar pedidos: {str(e)}")
        raise

def criar_dataframe_vazio():
    return pd.DataFrame(columns=[
        "id_pedido", "pratos", "mesa", "status",
        "data_criacao", "data_atualizacao", "observacoes"
    ])
