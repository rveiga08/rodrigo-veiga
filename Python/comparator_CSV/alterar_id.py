import csv

# Abra o arquivo CSV para leitura e crie uma lista com os dados
with open('diferencas.csv', mode='r', encoding='utf-8') as file:
    reader = csv.reader(file)
    data = list(reader)

# Inicialize um contador para o novo valor
novo_valor = 2779

# Modifique a primeira coluna para começar em 2779 e aumentar de 1 em 1
for row in data:
    row[0] = str(novo_valor)
    novo_valor += 1  # Aumente o valor em 1 para a próxima linha

# Abra o arquivo CSV para escrita e escreva os dados modificados de volta para o arquivo
with open('diferencas.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerows(data)

print("Alterações concluídas com sucesso!")
