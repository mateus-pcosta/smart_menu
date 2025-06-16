import streamlit as st
import pandas as pd
import json
from datetime import datetime
from core.gerenciamento_pratos import carregar_todos_pratos, verificar_disponibilidade
from core.gerenciamento_pedidos import criar_pedido, atualizar_status_pedido, listar_pedidos_por_status
from core.gerenciamento_estoque import carregar_ingredientes, verificar_estoque_baixo
from utils.helpers import formatar_itens_pedido, normalizar_item_pedido

st.set_page_config(page_title="Smart Menu", layout="wide")
st.title("🍽️ Smart Menu - Sistema de Restaurante")

def mostrar_cardapio():
    st.subheader("📋 Cardápio")
    
    pratos = carregar_todos_pratos()
    if not pratos:
        st.warning("Nenhum prato cadastrado no cardápio.")
        return
    
    categorias = sorted(set(p['categoria'] for p in pratos))
    categoria_selecionada = st.selectbox("Filtrar por categoria:", ["Todas"] + categorias)
    
    pratos_filtrados = [
        p for p in pratos 
        if categoria_selecionada == "Todas" or p['categoria'] == categoria_selecionada
    ]
    
    for prato in pratos_filtrados:
        disponivel = verificar_disponibilidade(prato['nome'])
        status = "🟢 Disponível" if disponivel else "🔴 Indisponível"
        
        with st.expander(f"{prato['nome']} - R$ {prato['preco']:.2f} | {status}"):
            col1, col2 = st.columns([1, 3])
            with col1:
                emoji = {
                    "Massas": "🍝",
                    "Carnes": "🍖",
                    "Saladas": "🥗",
                    "Sobremesas": "🍰",
                    "Entradas": "🧆"
                }.get(prato['categoria'], "🍽️")
                st.header(emoji)
            
            with col2:
                st.write(prato['descricao'])
                st.write(f"⏱️ Tempo de preparo: {prato['tempo_preparo']} minutos")
                
                if disponivel:
                    if st.button(f"➕ Adicionar {prato['nome']}",
                               key=f"add_{prato['nome']}"):
                        if 'pedido_atual' not in st.session_state:
                            st.session_state.pedido_atual = []
                        
                        st.session_state.pedido_atual.append({
                            "prato": prato['nome'],
                            "preco": float(prato['preco'])
                        })
                        st.toast(f"'{prato['nome']}' foi adicionado ao pedido!", icon="✅")
                        st.rerun()
                else:
                    st.warning("Este item não está disponível no momento")

def gerenciar_pedidos():
    st.subheader("📝 Pedidos")
    
    # Inicialização segura do session_state
    if 'pedido_atual' not in st.session_state:
        st.session_state.pedido_atual = []
    if 'mesa' not in st.session_state:
        st.session_state.mesa = 1
    if 'observacoes' not in st.session_state:
        st.session_state.observacoes = ""
    
    tab1, tab2, tab3 = st.tabs(["Novo Pedido", "Pedidos em Andamento", "Histórico"])
    
    with tab1:
        st.subheader("➕ Novo Pedido")
        
        if st.session_state.pedido_atual:
            st.write("**Seu pedido:**")
            total = 0
            
            for idx, item in enumerate(st.session_state.pedido_atual):
                col1, col2, col3 = st.columns([4, 2, 1])
                with col1:
                    st.write(f"- {item['prato']}")
                with col2:
                    st.write(f"R$ {item['preco']:.2f}")
                with col3:
                    if st.button("❌", key=f"remover_{idx}"):
                        st.session_state.pedido_atual.pop(idx)
                        st.rerun()
                
                total += item['preco']
            
            st.write(f"**Total: R$ {total:.2f}**")
            
            # Atualiza os valores da session_state
            st.session_state.mesa = st.number_input(
                "Número da Mesa:", 
                min_value=1, 
                max_value=50,
                value=st.session_state.mesa
            )
            
            st.session_state.observacoes = st.text_area(
                "Observações:", 
                value=st.session_state.observacoes
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar Pedido"):
                    try:
                        pedido_id = criar_pedido(
                            pratos=st.session_state.pedido_atual,
                            mesa=st.session_state.mesa,
                            observacoes=st.session_state.observacoes
                        )
                        st.success(f"Pedido #{pedido_id} criado com sucesso!")
                        st.session_state.pedido_atual = []
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao criar pedido: {str(e)}")
            
            with col2:
                if st.button("🗑️ Limpar Pedido"):
                    st.session_state.pedido_atual = []
                    st.rerun()
        
        else:
            st.info("Adicione itens ao pedido no cardápio.")
    
    with tab2:
        st.subheader("🔄 Pedidos em Andamento")
        
        try:
            pedidos_andamento = listar_pedidos_por_status().query("status != 'entregue'")
            
            if not pedidos_andamento.empty:
                for _, pedido in pedidos_andamento.iterrows():
                    with st.expander(f"📌 Pedido #{pedido['id_pedido']} - Mesa {pedido['mesa']}"):
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.write(f"**Status:** {pedido['status'].capitalize()}")
                            st.write(f"**Data:** {pd.to_datetime(pedido['data_criacao']).strftime('%d/%m/%Y %H:%M')}")
                        
                        with col2:
                            st.write("**Itens:**")
                            # Garante que temos uma lista de itens
                            itens = pedido['pratos'] if isinstance(pedido['pratos'], list) else []
                            for item in itens:
                                st.write(f"- {item.get('prato', 'Item sem nome')} (R$ {item.get('preco', 0):.2f})")
                        
                        st.write("**Alterar Status:**")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if pedido['status'] == 'recebido':
                                if st.button("⏳ Iniciar Preparo", key=f"preparar_{pedido['id_pedido']}"):
                                    atualizar_status_pedido(pedido['id_pedido'], "preparo")
                                    st.rerun()
                        
                        with col2:
                            if pedido['status'] == 'preparo':
                                if st.button("✅ Pronto", key=f"pronto_{pedido['id_pedido']}"):
                                    atualizar_status_pedido(pedido['id_pedido'], "pronto")
                                    st.rerun()
                        
                        with col3:
                            if pedido['status'] == 'pronto':
                                if st.button("🛎️ Entregue", key=f"entregue_{pedido['id_pedido']}"):
                                    atualizar_status_pedido(pedido['id_pedido'], "entregue")
                                    st.rerun()
            else:
                st.info("Nenhum pedido em andamento no momento.")
        
        except Exception as e:
            st.error(f"Erro ao carregar pedidos: {str(e)}")
    
    with tab3:
        st.subheader("📜 Histórico de Pedidos")
        pedidos_entregues = listar_pedidos_por_status("entregue")
        
        if not pedidos_entregues.empty:
            for _, pedido in pedidos_entregues.iterrows():
                with st.expander(f"✅ Pedido #{pedido['id_pedido']} - Mesa {pedido['mesa']} ({pedido['data_criacao'][:10]})"):
                    st.write(f"**Itens:**")
                    itens = pedido['pratos'] if isinstance(pedido['pratos'], list) else []
                    for item in itens:
                        st.write(f"- {item.get('prato', 'Item sem nome')} (R$ {item.get('preco', 0):.2f})")
                    
                    if pedido['observacoes'] and str(pedido['observacoes']) != 'nan':
                        st.write(f"**Observações:** {pedido['observacoes']}")
        else:
            st.info("Nenhum pedido finalizado ainda.")
            
def normalizar_item_pedido(item):
    if isinstance(item, str):
        try:
            item = json.loads(item.replace("'", '"'))
        except:
            item = {"prato": item, "preco": 0.0}
    
    return {
        "prato": str(item.get("prato", "Item sem nome")),
        "preco": float(item.get("preco", 0.0))
    }

def gerenciar_estoque():
    st.subheader("📦 Gerenciamento de Estoque")
    
    ingredientes = carregar_ingredientes()
    estoque_baixo = verificar_estoque_baixo()
    
    if not estoque_baixo.empty:
        st.warning("⚠️ Alguns ingredientes estão com estoque baixo:")
        st.dataframe(estoque_baixo)
    else:
        st.success("✅ Todos os ingredientes com estoque suficiente.")
    
    st.write("**Estoque completo:**")
    st.dataframe(ingredientes)

def main():
    menu = {
        "Cardápio": mostrar_cardapio,
        "Pedidos": gerenciar_pedidos,
        "Estoque": gerenciar_estoque
    }
    
    opcao = st.sidebar.selectbox("Menu", list(menu.keys()))
    menu[opcao]()

if __name__ == "__main__":
    main()