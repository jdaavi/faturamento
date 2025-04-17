import streamlit as st
import pandas as pd


st.set_page_config(page_title="Análise de Pedidos", layout="wide")

st.title("📊 Análise do faturamento")

uploaded_file = st.file_uploader("Faça o upload de um arquivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)

        # Padroniza os nomes das colunas
        df.columns = [col.strip().lower() for col in df.columns]

        # Remove registros com '######' na coluna de previsão de entrega, se existir
        col_entrega = 'previsão entrega'
        if col_entrega in df.columns:
            df = df[df[col_entrega] != '######']

        # Mapear 'Origem Pedido' para 'venda2'
        if 'origem pedido' in df.columns:
            def map_venda2(origem):
                if origem == "Ifood":
                    return "Ifood"
                elif origem == "AnotaAi":
                    return "Central de Atendimento"
                else:
                    return None

            df['venda2'] = df['origem pedido'].apply(map_venda2)

        # Tratar origem 'Local' usando o telefone
        if 'telefone' in df.columns and 'origem pedido' in df.columns:
            def tratar_local(row):
                telefone = str(row.get('telefone')).strip() if pd.notna(row.get('telefone')) else ""

                if telefone.startswith("100"):
                    return "Alimentação de Funcionáro"
                if telefone.startswith("101") or telefone == '':
                    return "Venda Balcão"
                if telefone.startswith("102"):
                    return "Teste"
                if telefone.startswith("103"):
                    return "Serviço"
                if telefone.startswith("104") or telefone.startswith("105") or telefone.startswith("106"):
                    return "Segunda Taxa"
                return None

            mascara_local = df['origem pedido'] == "Local"
            df.loc[mascara_local, 'venda2'] = df[mascara_local].apply(tratar_local, axis=1)

        st.success("Arquivo processado com sucesso!")
        st.write("Prévia do resultado processado:")
        st.dataframe(df)

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")

    