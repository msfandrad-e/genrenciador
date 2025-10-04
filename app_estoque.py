# app_estoque.py
import streamlit as st
import pandas as pd
import plotly.express as px

# Configura a página para modo wide
st.set_page_config(layout="wide")

# Título do App
st.title("📦 Sistema de Gestão de Estoque - Mercearia")

# Instrução inicial
st.info(
    "Use a barra lateral para adicionar itens ao estoque. A tabela e o gráfico abaixo são atualizados automaticamente.")

# 1. CARREGAR OS DADOS - VERSÃO ROBUSTA ADICIONADA
try:
    # Primeiro carrega sem usecols para ver a estrutura atual
    df_temp = pd.read_excel("estoque_mercearia.xlsx", header=0)

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

except FileNotFoundError:
    st.error("Arquivo 'estoque_mercearia.xlsx' não encontrado.")
    st.stop()
except Exception as e:
    st.error(f"Erro ao carregar o arquivo: {e}")
    st.stop()

# 2. SEÇÃO PARA ATUALIZAR O ESTOQUE (BARRA LATERAL) - COM PESQUISA
st.sidebar.header("➕ Adicionar ao Estoque")

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

        # Campo para a quantidade a ser adicionada
        quantidade_adicionada = st.sidebar.number_input(
            "Quantidade Comprada",
            min_value=1,
            value=1,
            step=1
        )

        # Botão para executar a atualização
        if st.sidebar.button("Atualizar Estoque", type="primary"):
            # Encontra o índice do produto selecionado
            mask = df['Produto'] == produto_selecionado
            if mask.any():
                indice_produto = df[mask].index[0]
                # Soma a quantidade ao estoque atual
                df.loc[indice_produto, 'Estoque'] += quantidade_adicionada
                # Salva a planilha com a alteração
                try:
                    df.to_excel("estoque_mercearia.xlsx", index=False)
                    st.sidebar.success(f"Estoque de **{produto_selecionado}** atualizado! ✅")
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

# 3. CAIXA DE PESQUISA - MANTIDO DO CÓDIGO ANTERIOR
filtro_produto = st.text_input("🔍 Pesquisar produto pelo nome:")
if filtro_produto:
    df_filtrado = df[df['Produto'].str.contains(filtro_produto, case=False, na=False)]
else:
    df_filtrado = df

# 4. EXIBIR A TABELA PRINCIPAL - MANTIDO DO CÓDIGO ANTERIOR
st.subheader("Tabela de Estoque Atual")
with st.container():
    st.dataframe(df_filtrado, use_container_width=True)

# 5. CRIAR E EXIBIR O GRÁFICO DE BARRAS - MANTIDO DO CÓDIGO ANTERIOR
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