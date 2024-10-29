import pandas as pd

# Função para comparar dois arquivos CSV considerando apenas as colunas 'NOME' e 'RG'
def comparar_csv(arquivo1, arquivo2, arquivo_saida):
    # Carregue os arquivos CSV em DataFrames do pandas
    df1 = pd.read_csv(arquivo1)
    df2 = pd.read_csv(arquivo2)

    # Encontre as diferenças nas colunas 'NOME' e 'RG'
    diff_df = pd.concat([df1, df2]).drop_duplicates(subset=['nome', 'RG'], keep=False)

    # Verifique se há diferenças
    if diff_df.empty:
        print("Os arquivos CSV são idênticos nas colunas 'NOME' ou 'RG'. Não há diferenças.")
    else:
        print("As seguintes diferenças nas colunas 'NOME' ou 'RG' foram encontradas:")
        print(diff_df)

        # Salve as diferenças em um arquivo CSV
        diff_df.to_csv(arquivo_saida, index=False)
        print(f"As diferenças foram salvas em '{arquivo_saida}'")


comparar_csv('FC_ERRADO.csv', 'FC_CORRETO.csv', 'diferencas.csv')
