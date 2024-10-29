import psycopg2

# Configurações de conexão com banco1
db1_config = {
    "dbname": "nome-banco-dados-1", #nome do banco de dados 1
    "user": "seu-usuario", #usuario do banco de dados 1
    "password": "sua-senha", #senha do banco de dados 1
    "host": "localhost",  # ou o host do banco
    "port": "5432",       # a porta padrão do PostgreSQL é 5432
}

# Configurações de conexão com banco2
db2_config = {
    "dbname": "nome-banco-dados-2", #nome do banco de dados 2
    "user": "seu-usuario", #usuario do banco de dados 2
    "password": "sua-senha", #senha do banco de dados 2
    "host": "localhost",  # ou o host do banco2
    "port": "5432",       # a porta padrão do PostgreSQL é 5432
}


# Mapeamento de id_antigo para id_novo
id_mapping = {
    110: 6700,
    130: 6701,
    144: 6702,
    148: 6703,
    234: 6704,
    308: 6705,
    320: 6706,
    434: 6707,
    460: 6708,
    464: 6709,
    468: 6710,
    470: 6711,
    518: 6712,
    816: 6713,
    848: 6714,
    1030: 6715,
    1098: 6716,
    1132: 6717,
    1360: 6718,
    1376: 6719,
    1388: 6720,
    1402: 6721,
    1404: 6722,
    1444: 6723,
    1522: 6724,
    1546: 6725,
    1560: 6726,
    1568: 6727,
    1570: 6728,
    1642: 6729,
    1708: 6730,
    1720: 6731,
    1792: 6732,
    1892: 6733,
    1998: 6734,
    2046: 6735,
    2064: 6736,
    2104: 6737,
    2140: 6738,
    2188: 6739,
    2246: 6740,
    2462: 6741,
    2464: 6742,
    2472: 6743,
    2478: 6744,
    2492: 6745,
    2502: 6746,
    2512: 6747,
    2558: 6748,
    2636: 6749,
    2650: 6750,
}

try:
    # Conectando-se ao banco1
    conn1 = psycopg2.connect(**db1_config)
    cursor1 = conn1.cursor()

    # Conectando-se ao banco2
    conn2 = psycopg2.connect(**db2_config)
    cursor2 = conn2.cursor()

    # Consulta para extrair os dados da tabela fotos_visitante no banco1
    query = "SELECT * FROM firstcontrol-antiga.public.fotos_visitante"

    # Executar a consulta no banco1
    cursor1.execute(query)

    # Obter os resultados da consulta
    dados = cursor1.fetchall()

    # Inserir os dados na tabela fotos_visitante no banco2, atualizando o idVisitante
    for registro in dados:
        id_antigo, outros_campos = registro[0], registro[1:]
        novo_idVisitante = id_mapping.get(id_antigo, id_antigo)
        cursor2.execute("INSERT INTO firstcontrol.public.fotos_visitante (idVisitante, outros_campos) VALUES (%s, %s)",
                        (novo_idVisitante, outros_campos))

    # Commit das alterações no banco2
    conn2.commit()

    print("Dados transferidos com sucesso, com idVisitante atualizado!")

except psycopg2.Error as e:
    print(f"Ocorreu um erro durante a transferência de dados e a atualização do idVisitante: {e}")

finally:
    # Fechar as conexões com ambos os bancos
    cursor1.close()
    cursor2.close()
    conn1.close()
    conn2.close()
