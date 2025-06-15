import json
from typing import Union, List, Dict

def normalizar_item_pedido(item: Union[str, Dict]) -> Dict:
    if isinstance(item, str):
        try:
            item = json.loads(item.replace("'", '"'))
        except json.JSONDecodeError:
            item = {"prato": item, "preco": 0.0}
    
    return {
        "prato": str(item.get("prato", "Item sem nome")),
        "preco": float(item.get("preco", 0.0))
    }

def parse_pratos(pratos: Union[str, List]) -> List[Dict]:
    if isinstance(pratos, str):
        try:
            pratos = json.loads(pratos.replace("'", '"'))
        except json.JSONDecodeError:
            pratos = [{"prato": "Item inválido", "preco": 0.0}]
    
    return [normalizar_item_pedido(item) for item in pratos]

def formatar_itens_pedido(itens: Union[str, List]) -> str:
    itens_normalizados = parse_pratos(itens)
    return "\n".join([f"- {item['prato']} (R$ {item['preco']:.2f})" for item in itens_normalizados])