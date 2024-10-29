import sys
import os
import json
import base64
import traceback
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QComboBox, QPushButton, 
                             QTableView, QMessageBox, QLineEdit, QLabel, QCheckBox, QFormLayout, 
                             QDialog, QHeaderView, QScrollArea, QHBoxLayout)
from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet

# Funções de criptografia
def generate_key():
    key = Fernet.generate_key()
    with open("./Projetos/system1/secret.key", "wb") as key_file:
        key_file.write(key)

def load_key():
    key_path = "./Projetos/system1/secret.key"  # Caminho relativo ajustado
    if not os.path.exists(key_path):
        generate_key()
    return open(key_path, "rb").read()

def encrypt_message(message, key):
    f = Fernet(key)
    return f.encrypt(message.encode())

def decrypt_message(encrypted_message, key):
    f = Fernet(key)
    return f.decrypt(encrypted_message).decode()

def log_error(message):
    log_path = './Projetos/system1/error_log.txt'  # Caminho relativo ajustado
    with open(log_path, 'a') as log_file:
        log_file.write(f"{datetime.now()} - ERROR: {message}\n")

def log_query(query):
    query_log_path = './Projetos/system1/query_history.txt'
    with open(query_log_path, 'a') as log_file:
        log_file.write(f"{datetime.now()} - QUERY: {query}\n")

class CredentialManager:
    def __init__(self, file_name='./Projetos/system1/credentials.enc'):
        self.file_name = file_name
        self.key = load_key()

    def save_credentials(self, username, password):
        credentials = {
            'username': base64.urlsafe_b64encode(encrypt_message(username, self.key)).decode(),
            'password': base64.urlsafe_b64encode(encrypt_message(password, self.key)).decode()
        }
        with open(self.file_name, 'w') as f:
            json.dump(credentials, f)

    def load_credentials(self):
        if os.path.exists(self.file_name):
            with open(self.file_name, 'r') as f:
                file_content = f.read()
                if file_content:  # Verifica se o arquivo não está vazio
                    try:
                        encrypted_credentials = json.loads(file_content)
                        username = decrypt_message(base64.urlsafe_b64decode(encrypted_credentials['username']), self.key)
                        password = decrypt_message(base64.urlsafe_b64decode(encrypted_credentials['password']), self.key)
                        return username, password
                    except json.JSONDecodeError:
                        log_error("O arquivo de credenciais está corrompido ou não é um JSON válido.")
                        QMessageBox.critical(None, "Erro", "O arquivo de credenciais está corrompido. Por favor, recrie as credenciais.")
                        return None, None
                else:
                    log_error("O arquivo de credenciais está vazio.")
                    return None, None  # Retorna None se o arquivo estiver vazio
        return None, None

class DBMapper:
    def __init__(self, db_url, cache_file='./Projetos/system1/db_mapping.json'):
        self.db_url = db_url
        self.cache_file = cache_file
        self.engine = create_engine(self.db_url)
        self.metadata = MetaData(bind=self.engine)
        self.metadata.reflect()

    def map_database(self):
        db_mapping = {
            'tables': {}
        }
        for table_name, table in self.metadata.tables.items():
            columns = []
            for column in table.columns:
                columns.append({
                    'name': column.name,
                    'type': str(column.type),
                    'nullable': column.nullable,
                    'primary_key': column.primary_key
                })
            db_mapping['tables'][table_name] = {
                'columns': columns,
                'constraints': [str(constraint) for constraint in table.constraints]
            }

        with open(self.cache_file, 'w') as f:
            json.dump(db_mapping, f)

    def load_mapping(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        else:
            self.map_database()
            return self.load_mapping()

class FilterDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Filtro")
        self.setFixedSize(400, 300)  # Define o tamanho fixo do diálogo

        self.layout = QVBoxLayout(self)
        
        self.filters = {}
        
        # Configuração do widget de rolagem
        self.scroll_area = QScrollArea(self)
        self.scroll_widget = QWidget()
        self.scroll_layout = QFormLayout(self.scroll_widget)
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        
        # Adiciona campos de filtro no layout de formulário
        for column in columns:
            self.filters[column['name']] = QLineEdit(self)
            self.scroll_layout.addRow(f"{column['name']} ({column['type']})", self.filters[column['name']])
        
        self.layout.addWidget(self.scroll_area)
        
        self.apply_button = QPushButton("Aplicar", self)
        self.layout.addWidget(self.apply_button)
        self.apply_button.clicked.connect(self.accept)

    def get_filters(self):
        filters = {}
        if self.filters:  # Verifica se filters não está vazio
            filters = {col: self.filters[col].text() for col in self.filters if self.filters[col].text()}
        return filters

class WorkerThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)  # Alterado para emitir um objeto

    def __init__(self, query, engine):
        super().__init__()
        self.query = query
        self.engine = engine

    def run(self):
        try:
            Session = sessionmaker(bind=self.engine)
            session = Session()
            result = session.execute(self.query)
            session.close()
            
            # Envia progresso e sinaliza término da execução com o resultado
            self.progress.emit(100)
            self.finished.emit(result.fetchall())
        except Exception as e:
            log_error(f"Erro ao executar a consulta: {str(e)}\n{traceback.format_exc()}")
            self.finished.emit([])  # Emite uma lista vazia em caso de erro

class MainWindow(QMainWindow):
    def __init__(self, db_mapper):
        super().__init__()
        self.db_mapper = db_mapper
        self.setWindowTitle("Consulta em Nuvem - MariaDB")

        # Layout da interface
        self.widget = QWidget()
        self.layout = QVBoxLayout()
        self.table_select = QComboBox()
        self.table_select.addItems(self.db_mapper.metadata.tables.keys())
        self.query_button = QPushButton("Consultar")
        self.filter_button = QPushButton("Adicionar Filtro")
        self.sort_column_select = QComboBox()  # Novo widget para seleção de coluna
        self.sort_order_select = QComboBox()  # Novo widget para seleção de ordem
        self.table_view = QTableView()
        self.progress_bar = QProgressBar(self)

        # Configuração dos widgets de ordenação
        self.sort_order_select.addItems(["Ascendente", "Descendente"])

        # Adiciona ao layout
        self.layout.addWidget(self.table_select)
        self.layout.addWidget(self.filter_button)
        self.layout.addWidget(self.query_button)
        
        self.layout.addWidget(self.table_view)
        self.layout.addWidget(self.progress_bar)
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)
        
        # Habilita a ordenação no QTableView
        self.table_view.setSortingEnabled(True)

        # Conecta os botões às funções
        self.query_button.clicked.connect(self.run_query)
        self.filter_button.clicked.connect(self.open_filter_dialog)

        self.filters = {}

    def open_filter_dialog(self):
        table_name = self.table_select.currentText()
        table_info = self.db_mapper.metadata.tables[table_name]

        columns = [{'name': col.name, 'type': str(col.type)} for col in table_info.columns]
        dialog = FilterDialog(columns, self)
        if dialog.exec_() == QDialog.Accepted:
            self.filters = dialog.get_filters()
            self.run_query()  # Aplica os filtros e realiza a consulta imediatamente

    def run_query(self):
        table_name = self.table_select.currentText()
        table_info = self.db_mapper.metadata.tables[table_name]

        columns = ', '.join([col.name for col in table_info.columns])
        query = f"SELECT {columns} FROM {table_name}"

        if self.filters:
            filter_conditions = ' AND '.join([f"{col} LIKE '%{value}%'" for col, value in self.filters.items() if value])
            if filter_conditions:
                query += f" WHERE {filter_conditions}"

        # Adiciona a lógica de ordenação
        sort_column = self.sort_column_select.currentText()
        sort_order = 'ASC' if self.sort_order_select.currentText() == 'Ascendente' else 'DESC'
        if sort_column:
            query += f" ORDER BY {sort_column} {sort_order}"

        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        # Executa a consulta em um thread separado
        self.worker = WorkerThread(query, self.db_mapper.engine)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()


    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_finished(self, result):
        self.progress_bar.setVisible(False)
        model = QStandardItemModel()

        if result:
            table_name = self.table_select.currentText()
            columns = [col.name for col in self.db_mapper.metadata.tables[table_name].columns]

            # Configura os nomes das colunas
            model.setColumnCount(len(columns))
            model.setHorizontalHeaderLabels(columns)
            
            for row in result:
                items = [QStandardItem(str(cell)) for cell in row]
                model.appendRow(items)

            self.table_view.setModel(model)

            # Habilita a ordenação de colunas ao clicar nos cabeçalhos
            self.table_view.setSortingEnabled(True)

            # Ajusta automaticamente o tamanho das colunas e adiciona uma barra de rolagem horizontal
            self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # Ajusta a largura das colunas automaticamente
            self.table_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Adiciona a barra de rolagem horizontal
            self.table_view.resizeColumnsToContents()  # Garante que todas as colunas sejam redimensionadas
            
            # Atualiza o combobox de colunas para ordenação
            self.sort_column_select.clear()
            self.sort_column_select.addItems(columns)
            
            QMessageBox.information(self, "Consulta", f"Consulta realizada com sucesso na tabela {self.table_select.currentText()}")
        else:
            QMessageBox.information(self, "Consulta", "Nenhum resultado encontrado ou erro durante a execução.")



class CondoIDWindow(QMainWindow):
    def __init__(self, db_url, username, password):
        super().__init__()
        self.setWindowTitle("ID do Condomínio")
        self.db_url = db_url
        self.db_url_with_condo_id = db_url
        self.widget = QWidget()
        self.layout = QVBoxLayout()

        self.condo_id_label = QLabel("ID do Condomínio:")
        self.condo_id_input = QLineEdit()
        self.confirm_button = QPushButton("Confirmar")

        self.layout.addWidget(self.condo_id_label)
        self.layout.addWidget(self.condo_id_input)
        self.layout.addWidget(self.confirm_button)

        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        self.confirm_button.clicked.connect(self.handle_confirm)

    def handle_confirm(self):
        condo_id = self.condo_id_input.text()
        if not condo_id:
            QMessageBox.warning(self, "Erro", "O ID do condomínio é obrigatório!")
            return

        # Atualiza a URL de conexão com o nome do banco de dados
        self.db_url_with_condo_id = f"{self.db_url}{condo_id}"

        # Atualize o mapeamento de banco de dados com o novo condo_id
        try:
            self.db_mapper = DBMapper(self.db_url_with_condo_id)
            self.db_mapper.map_database()

            self.main_window = MainWindow(self.db_mapper)
            self.main_window.show()
            self.close()
        except Exception as e:
            error_message = f"Erro ao selecionar o banco de dados: {str(e)}\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Erro", error_message)
            log_error(error_message)

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - MariaDB")
        self.widget = QWidget()
        self.layout = QVBoxLayout()

        self.username_label = QLabel("Usuário:")
        self.username_input = QLineEdit()
        self.password_label = QLabel("Senha:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.remember_me_checkbox = QCheckBox("Lembrar credenciais")
        self.login_button = QPushButton("Login")

        self.layout.addWidget(self.username_label)
        self.layout.addWidget(self.username_input)
        self.layout.addWidget(self.password_label)
        self.layout.addWidget(self.password_input)
        self.layout.addWidget(self.remember_me_checkbox)
        self.layout.addWidget(self.login_button)

        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        self.login_button.clicked.connect(self.handle_login)

        self.credential_manager = CredentialManager()

        # Carrega credenciais salvas
        saved_username, saved_password = self.credential_manager.load_credentials()
        if saved_username and saved_password:
            self.username_input.setText(saved_username)
            self.password_input.setText(saved_password)
            self.remember_me_checkbox.setChecked(True)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Erro", "Usuário e senha são obrigatórios!")
            return

        # Corrigindo a formatação do db_url
        db_url = f"mysql+pymysql://{username}:{password}@193.122.203.251:21286/"

        try:
            self.condo_id_window = CondoIDWindow(db_url, username, password)
            self.condo_id_window.show()
            self.close()
        except Exception as e:
            error_message = f"Erro ao fazer login: {str(e)}\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Erro", error_message)
            log_error(error_message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_())
