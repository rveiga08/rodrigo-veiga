import pymysql
import sqlite3
from datetime import datetime
import pytz

class DatabaseManager:
    def __init__(self):
        self.cloud_db = self.connect_to_cloud_db()
        self.local_db = sqlite3.connect('./Python/view_licenses_duplicate_system/data/query_results.db')
        self.create_local_table()

    def connect_to_cloud_db(self):
        return pymysql.connect(
            host='database-host',
            port=21286,
            user='database-user',
            password='database-pass',
            database='database-name'
        )

    def create_local_table(self):
        cursor = self.local_db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_results (
                idControlCondo INT,
                `key` VARCHAR(255),
                nome VARCHAR(255),
                cnpj VARCHAR(255),
                version VARCHAR(255),
                date_recorded TEXT,
                version TEXT,
                PRIMARY KEY (idControlCondo, `key`)
            )
        ''')
        self.local_db.commit()

    def execute_query(self):
        query = '''
        SELECT t.idControlCondo, t.`key`, c.nome, c.cnpj
        FROM (
            SELECT leh.*, l.idControlCondo, l.`key`
            FROM fcaccess_license.licenseErrorHardwareId leh
            LEFT JOIN fcaccess_license.licenses l 
            ON l.id_client = leh.id_client 
            ORDER BY leh.id DESC 
            LIMIT 4000 
        ) AS t 
        LEFT JOIN controlcondo.condominio c 
        ON c.id_condominio = t.idControlCondo 
        GROUP BY t.idControlCondo, t.`key`, c.nome, c.cnpj
        HAVING COUNT(t.event_time) > 10 
        ORDER BY t.idControlCondo;
        '''
        with self.cloud_db.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
        return results

    def store_query_results(self, results):
        cursor = self.local_db.cursor()

        # Obter a data atual no fuso horário GMT -3
        timezone = pytz.timezone('America/Sao_Paulo')
        now = datetime.now(timezone).strftime('%d-%m-%Y %H:%M:%S')

        for row in results:
            # Tentar inserir, mas ignorar se já existir
            cursor.execute('''
                INSERT OR IGNORE INTO query_results (idControlCondo, `key`, nome, cnpj, version, date_recorded)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (row[0], row[1], row[2], row[3], row[4], now))

        # Após inserir novos dados, limpar duplicatas existentes (se houver alguma lógica adicional)
        self.remove_duplicates()

        self.local_db.commit()

    def remove_duplicates(self):
        cursor = self.local_db.cursor()

        # Encontra entradas duplicadas baseadas em idControlCondo e nome
        cursor.execute('''
            SELECT idControlCondo, nome, MIN(date_recorded) as oldest_record
            FROM query_results
            GROUP BY idControlCondo, nome
            HAVING COUNT(*) > 1
        ''')

        duplicates = cursor.fetchall()

        # Remove entradas duplicadas, mantendo a mais antiga
        for idControlCondo, nome, oldest_record in duplicates:
            cursor.execute('''
                DELETE FROM query_results 
                WHERE idControlCondo = ? 
                AND nome = ? 
                AND date_recorded > ?
            ''', (idControlCondo, nome, oldest_record))
        
        self.local_db.commit()

    def get_previous_results(self):
        cursor = self.local_db.cursor()
        cursor.execute('SELECT * FROM query_results')
        return cursor.fetchall()

    def get_new_entries(self, old_results, new_results):
        old_ids = set((row[0], row[1]) for row in old_results)  # Conjunto de ids antigos
        new_entries = [row for row in new_results if (row[0], row[1]) not in old_ids]
        return new_entries
