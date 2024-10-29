import csv

def validar_csv(arquivo_csv, num_colunas_esperadas):
    with open(arquivo_csv, 'r') as file:
        leitor = csv.reader(file)
        for i, linha in enumerate(leitor):
            # Verifica o número de colunas
            if len(linha) != num_colunas_esperadas:
                print(f"Erro na linha {i + 1}: Esperado {num_colunas_esperadas} colunas, mas encontrado {len(linha)}.")
            
            # Verifica se os valores estão entre aspas simples
            for valor in linha:
                if isinstance(valor, str) and (valor.startswith("'") and valor.endswith("'")):
                    continue
                else:
                    print(f"Erro na linha {i + 1}: O valor '{valor}' não está entre aspas simples.")

# Uso da função
validar_csv('dados.csv', 3)  # Exemplo: espera 3 colunas
