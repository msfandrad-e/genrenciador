# app_estoque.py
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# Configura a página para modo wide
st.set_page_config(layout="wide")

# Título do App
st.title("📦 Sistema de Gestão de Estoque - Mercearia")

# Instrução inicial
st.info("Use a barra lateral para adicionar ou retirar itens do estoque. A tabela e o gráfico abaixo são atualizados automaticamente.")

# 1. CARREGAR OS DADOS - VERSÃO ROBUSTA
try:
    # Primeiro carrega sem usecols para ver a estrutura atual
    df_temp = pd.read_excel("estoque_mercearia.xlsx", header=0)
    
    # Debug: mostra o que encontrou
    st.write("🔍 Estrutura atual do arquivo:")
    st.write(f"Colunas: {df_temp.columns.tolist()}")
    st.write(f"Número de colunas: {len(df_temp.columns)}")
    
    # Tenta encontrar as colunas que precisamos pelos nomes
    colunas_encontradas = []
    nomes_procurados = ['Produto', 'Preco', 'Medida', 'Estoque']
    
    for nome in nomes_procurados:
        for i, col_name in enumerate(df_temp.columns):
            if nome.lower() in str(col_name).lower():
                colunas_encontradas.append(i)
                break
    
    if len(colunas_encontradas) >= 3:  # Pelo menos Produto, Preco/Medida, Estoque
        df = pd.read_excel("estoque_mercearia.xlsx", header=0, usecols=colunas_encontradas)
        
        # Mapeia para os nomes padrão
        if len(colunas_encontradas) == 4:
            df.columns = ['Produto', 'Preco', 'Medida', 'Estoque']
        elif len(colunas_encontradas) == 3:
            df.columns = ['Produto', 'Preco', 'Estoque']  # ou ajuste conforme necessário
        else:
            df.columns = [f'Coluna_{i}' for i in range(len(colunas_encontradas))]
            
    else:
        # Fallback: pega as primeiras colunas disponíveis
        num_colunas = min(4, len(df_temp.columns))
        df = pd.read_excel("estoque_mercearia.xlsx", header=0, usecols=range(num_colunas))
        
        # Tenta adivinhar os nomes baseado na posição
        nomes_padrao = ['Produto', 'Preco', 'Medida', 'Estoque']
        df.columns = nomes_padrao[:num_colunas]
    
    # Remove linhas completamente vazias
    df = df.dropna(how='all')
    
    # Converte Estoque para numérico se a coluna existir
    if 'Estoque' in df.columns:
        df['Estoque'] = pd.to_numeric(df['Estoque'], errors='coerce')
    
    st.success("✅ Arquivo carregado com sucesso!")
    st.write(f"📊 Colunas sendo usadas: {df.columns.tolist()}")
    
except FileNotFoundError:
    st.error("Arquivo 'estoque_mercearia.xlsx' não encontrado.")
    st.stop()
except Exception as e:
    st.error(f"Erro ao carregar o arquivo: {e}")
    st.stop()

# 2. SEÇÃO PARA ATUALIZAR O ESTOQUE (BARRA LATERAL) - COM ENTRADA E SAÍDA
st.sidebar.header("🔄 Gerenciar Estoque")

# Mensagem preventiva
st.sidebar.info("💡 **Dica:** Feche o arquivo Excel antes de atualizar o estoque.")

# Pega a lista de produtos para o dropdown
lista_produtos = df['Produto'].dropna().tolist()

if lista_produtos:
    # CAIXA DE PESQUISA NO SIDEBAR
    pesquisa_sidebar = st.sidebar.text_input("🔍 Pesquisar produto no sidebar:", key="sidebar_search")
    
    if pesquisa_sidebar:
        # Filtra produtos que contêm o texto da pesquisa
        produtos_filtrados = [produto for produto in lista_produtos 
                            if pesquisa_sidebar.lower() in str(produto).lower()]
    else:
        produtos_filtrados = lista_produtos
    
    # Selectbox com os produtos (filtrados ou não)
    if produtos_filtrados:
        produto_selecionado = st.sidebar.selectbox(
            "Selecione o Produto", 
            produtos_filtrados,
            key="sidebar_selectbox"
        )
        
        # Mostra quantos produtos foram encontrados
        if pesquisa_sidebar:
            st.sidebar.caption(f"📋 {len(produtos_filtrados)} produto(s) encontrado(s)")
        
        # MOSTRAR ESTOQUE ATUAL DO PRODUTO SELECIONADO
        if produto_selecionado:
            estoque_atual = df.loc[df['Produto'] == produto_selecionado, 'Estoque'].iloc[0]
            st.sidebar.metric(f"Estoque Atual - {produto_selecionado}", f"{estoque_atual} unidades")
        
        # SELEÇÃO DO TIPO DE MOVIMENTAÇÃO
        tipo_movimentacao = st.sidebar.radio(
            "Tipo de Movimentação:",
            ["Entrada (Compra)", "Saída (Venda)"],
            key="tipo_mov"
        )
        
        # Campo para a quantidade
        if tipo_movimentacao == "Entrada (Compra)":
            quantidade = st.sidebar.number_input("Quantidade Comprada", min_value=1, value=1, step=1)
        else:
            quantidade = st.sidebar.number_input("Quantidade Vendida", min_value=1, value=1, step=1)

        # Botão para executar a atualização
        if st.sidebar.button("Atualizar Estoque", type="primary"):
            # Encontra o índice do produto selecionado
            mask = df['Produto'] == produto_selecionado
            if mask.any():
                indice_produto = df[mask].index[0]
                
                # Soma ou subtrai a quantidade dependendo do tipo
                if tipo_movimentacao == "Entrada (Compra)":
                    df.loc[indice_produto, 'Estoque'] += quantidade
                    mensagem = f"✅ **{quantidade} unidade(s)** adicionada(s) ao estoque de **{produto_selecionado}**"
                else:
                    # Verifica se há estoque suficiente
                    estoque_atual = df.loc[indice_produto, 'Estoque']
                    if estoque_atual >= quantidade:
                        df.loc[indice_produto, 'Estoque'] -= quantidade
                        mensagem = f"✅ **{quantidade} unidade(s)** retirada(s) do estoque de **{produto_selecionado}**"
                    else:
                        st.sidebar.error(f"❌ Estoque insuficiente! Disponível: {estoque_atual} unidades")
                        mensagem = None
                
                # Salva a planilha se a operação foi bem sucedida
                if mensagem:
                    try:
                        df.to_excel("estoque_mercearia.xlsx", index=False)
                        st.sidebar.success(mensagem)
                        st.rerun()
                    except PermissionError:
                        st.sidebar.error("❌ Erro: Feche o arquivo Excel para permitir a atualização.")
                    except Exception as e:
                        st.sidebar.error(f"Erro ao salvar: {e}")
            else:
                st.sidebar.error("Produto não encontrado.")
    else:
        st.sidebar.warning("Nenhum produto encontrado com essa pesquisa.")
        
else:
    st.sidebar.warning("Nenhum produto encontrado na planilha.")

# 3. BOTÃO PARA BAIXAR EXCEL ATUALIZADO
st.sidebar.markdown("---")
st.sidebar.header("📥 Exportar Dados")

# Criar arquivo Excel em memória para download
def criar_excel_download(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Estoque')
    processed_data = output.getvalue()
    return processed_data

excel_data = criar_excel_download(df)

st.sidebar.download_button(
    label="📥 Baixar Planilha Atualizada",
    data=excel_data,
    file_name="estoque_mercearia_atualizado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    help="Clique para baixar a planilha atualizada em Excel"
)

# 4. CAIXA DE PESQUISA
filtro_produto = st.text_input("🔍 Pesquisar produto pelo nome:")
if filtro_produto:
    df_filtrado = df[df['Produto'].str.contains(filtro_produto, case=False, na=False)]
else:
    df_filtrado = df

# 5. EXIBIR A TABELA PRINCIPAL
st.subheader("Tabela de Estoque Atual")
with st.container():
    st.dataframe(df_filtrado, use_container_width=True)

# 6. CRIAR E EXIBIR O GRÁFICO DE BARRAS
st.subheader("Produtos com Menor Estoque")

# Filtra produtos com estoque válido
df_com_estoque = df[df['Estoque'].notna()]

if len(df_com_estoque) > 0:
    # Ordena pelo estoque (menor para maior) e pega os 10 primeiros
    df_para_grafico = df_com_estoque.nsmallest(10, 'Estoque')
    
    # Cria o gráfico de barras
    fig = px.bar(
        df_para_grafico, 
        x='Produto', 
        y='Estoque', 
        title="Top 10 Produtos para Repor",
        color='Estoque',
        color_continuous_scale='reds'
    )
    
    # Melhora a aparência do gráfico
    fig.update_layout(
        xaxis_tickangle=-45,
        showlegend=False
    )
    
    # Exibe o gráfico no app
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Não há dados de estoque suficientes para gerar o gráfico.")
