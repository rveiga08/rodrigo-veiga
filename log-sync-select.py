import sys
import logging
import csv
from cryptography.fernet import Fernet
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, 
    QMessageBox, QTableWidget, QTableWidgetItem, QHBoxLayout, QCheckBox, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configurar logging
logging.basicConfig(filename='\sistema-python\Projetos\sync_error_logserros.log', level=logging.ERROR, format='%(asctime)s:%(levelname)s:%(message)s')

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Login')

        self.username_label = QLabel('Usuário:', self)
        self.username_input = QLineEdit(self)

        self.password_label = QLabel('Senha:', self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)

        self.remember_me = QCheckBox('Lembrar-me', self)

        self.login_button = QPushButton('Login', self)
        self.login_button.clicked.connect(self.handle_login)

        layout = QVBoxLayout()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.remember_me)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, 'Erro', 'Por favor, insira o nome de usuário e a senha.')
            return

        if self.remember_me.isChecked():
            self.save_credentials(username, password)

        self.open_main_window(username, password)

    def save_credentials(self, username, password):
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)

        encrypted_username = cipher_suite.encrypt(username.encode())
        encrypted_password = cipher_suite.encrypt(password.encode())

        with open('credentials.key', 'wb') as key_file:
            key_file.write(key)

        with open('credentials.enc', 'wb') as enc_file:
            enc_file.write(encrypted_username + b'\n' + encrypted_password)

    def load_credentials(self):
        try:
            with open('credentials.key', 'rb') as key_file:
                key = key_file.read()

            cipher_suite = Fernet(key)

            with open('credentials.enc', 'rb') as enc_file:
                encrypted_username, encrypted_password = enc_file.read().split(b'\n')

            username = cipher_suite.decrypt(encrypted_username).decode()
            password = cipher_suite.decrypt(encrypted_password).decode()

            return username, password

        except (FileNotFoundError, ValueError):
            return None, None

    def open_main_window(self, username, password):
        self.close()
        self.main_window = DatabaseApp(username, password)
        self.main_window.show()


class DatabaseApp(QWidget):
    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password
        self.initUI()
        self.cache = {}

    def initUI(self):
        self.setWindowTitle('Consulta de Log de Erros')
        self.setWindowIcon(QIcon('icon.png'))  # Adicionar ícone ao aplicativo
        
        self.vpn_label = QLabel('Lembre-se de habilitar a VPN!', self)
        
        self.condo_id_label = QLabel('ID do Condomínio:', self)
        self.condo_id_input = QLineEdit(self)
        
        self.consult_button = QPushButton('Consultar', self)
        self.consult_button.clicked.connect(self.on_consult)
        
        self.export_csv_button = QPushButton('Exportar CSV', self)
        self.export_csv_button.clicked.connect(self.export_to_csv)
        
        self.id_consulta_label = QLabel('ID da Consulta (opcional):', self)
        self.id_consulta_input = QLineEdit(self)
        self.id_consulta_label.setVisible(False)
        self.id_consulta_input.setVisible(False)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['ID', 'Table Name', 'Entry_Id', 'Sentido', 'Operation', 'Error'])
        self.table.setSortingEnabled(True)

        # Filtros de texto
        self.filters = []
        header_layout = QHBoxLayout()
        for i in range(6):  # Para cada coluna
            filter_edit = QLineEdit(self)
            filter_edit.setPlaceholderText(f'Filtrar {self.table.horizontalHeaderItem(i).text()}')
            filter_edit.textChanged.connect(self.filter_table)
            self.filters.append(filter_edit)
            header_layout.addWidget(filter_edit)
        
        header_layout.addStretch()

        # Botão para limpar o cache
        self.clear_cache_button = QPushButton('Limpar Cache', self)
        self.clear_cache_button.clicked.connect(self.clear_cache)

        # Botão para limpar filtros
        self.clear_filters_button = QPushButton('Limpar Filtros', self)
        self.clear_filters_button.clicked.connect(self.clear_filters)

        # Label de contagem de linhas
        self.row_count_label = QLabel('Linhas listadas: 0', self)

        # Barra de progresso
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)  # Percentual de 0 a 100
        self.progress_bar.setTextVisible(True)  # Mostrar porcentagem
        self.progress_bar.setVisible(False)  # Inicialmente oculta

        # Layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.clear_cache_button)
        button_layout.addWidget(self.clear_filters_button)
        button_layout.addWidget(self.export_csv_button)

        layout = QVBoxLayout()
        layout.addWidget(self.vpn_label)
        layout.addWidget(self.condo_id_label)
        layout.addWidget(self.condo_id_input)
        layout.addWidget(self.consult_button)
        layout.addWidget(self.id_consulta_label)
        layout.addWidget(self.id_consulta_input)
        layout.addLayout(header_layout)
        layout.addWidget(self.table)
        layout.addWidget(self.row_count_label)
        layout.addLayout(button_layout)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        self.show()

    def on_consult(self):
        condo_id = self.condo_id_input.text().strip()
        id_consulta = self.id_consulta_input.text().strip()

        if not condo_id:
            QMessageBox.warning(self, 'Erro', 'Por favor, insira o ID do condomínio.')
            return

        self.progress_bar.setValue(0)  # Inicializa a barra de progresso
        self.progress_bar.setVisible(True)  # Mostra a barra de progresso

        if condo_id in self.cache and not id_consulta:
            result = self.cache[condo_id]
            self.update_table(result)
            self.id_consulta_label.setVisible(True)
            self.id_consulta_input.setVisible(True)
            self.progress_bar.setVisible(False)  # Oculta a barra de progresso
            return

        query = self.build_query(id_consulta)
        QTimer.singleShot(100, lambda: self.execute_query(condo_id, query))

    def execute_query(self, condo_id, query):
        self.progress_bar.setValue(50)  # Atualiza a barra de progresso para 50%
        result, error = self.run_query(condo_id, query)
        self.progress_bar.setValue(100)  # Atualiza a barra de progresso para 100%

        if error:
            QMessageBox.critical(self, 'Erro', error)
        else:
            if not self.id_consulta_input.text():
                self.cache[condo_id] = result
            self.update_table(result)
            self.id_consulta_label.setVisible(True)
            self.id_consulta_input.setVisible(True)

        self.progress_bar.setVisible(False)  # Oculta a barra de progresso

    def build_query(self, id_consulta, ignore_filters=False):
        if not id_consulta:
            return "SELECT id, table_name, entry_id, sentido, operation, error FROM log_sync_err ORDER BY id DESC;"
        else:
            return f"SELECT id, table_name, entry_id, sentido, operation, error FROM log_sync_err WHERE id > {id_consulta} ORDER BY id DESC;"

    def run_query(self, condo_id, query):
        db_url = f'mysql+pymysql://{self.username}:{self.password}@193.122.203.251:21286/{condo_id}'
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            result = session.execute(text(query)).fetchall()
            session.commit()
            return result, None
        except Exception as e:
            session.rollback()
            error_message = f'Erro ao executar a consulta: {e}'
            logging.error(error_message)
            return None, error_message
        finally:
            session.close()

    def update_table(self, result):
        self.table.setRowCount(len(result))
        for row_idx, row_data in enumerate(result):
            for col_idx, col_data in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))
        self.row_count_label.setText(f'Linhas listadas: {len(result)}')

    def filter_table(self):
        visible_rows = 0
        for i in range(self.table.rowCount()):
            self.table.setRowHidden(i, False)
            for j in range(self.table.columnCount()):
                if self.filters[j].text().lower() not in self.table.item(i, j).text().lower():
                    self.table.setRowHidden(i, True)
                    break
            if not self.table.isRowHidden(i):
                visible_rows += 1
        self.row_count_label.setText(f'Linhas listadas: {visible_rows}')

    def clear_cache(self):
        self.cache.clear()
        QMessageBox.information(self, 'Cache Limpo', 'O cache foi limpo com sucesso.')

    def clear_filters(self):
        for filter_edit in self.filters:
            filter_edit.clear()
            
    def export_to_csv(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, 'Salvar CSV', '', 'CSV Files (*.csv)', options=options)
        if file_name:
            try:
                with open(file_name, 'w', newline='') as file:
                    writer = csv.writer(file)
                    headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
                    writer.writerow(headers)

                    for row in range(self.table.rowCount()):
                        row_data = [self.table.item(row, col).text() if self.table.item(row, col) else '' for col in range(self.table.columnCount())]
                        writer.writerow(row_data)

                QMessageBox.information(self, 'Exportar CSV', f'Dados exportados com sucesso para {file_name}')
            except Exception as e:
                logging.error(f'Erro ao exportar para CSV: {e}')
                QMessageBox.critical(self, 'Erro', 'Ocorreu um erro ao exportar os dados para CSV.')

if __name__ == '__main__':
    app = QApplication(sys.argv)

    login_window = LoginWindow()
    stored_username, stored_password = login_window.load_credentials()
    if stored_username and stored_password:
        login_window.open_main_window(stored_username, stored_password)
    else:
        login_window.show()

    sys.exit(app.exec_())


# Proximas implementações
#Adicione a possibilidade de gerar um arquivo csv dos dados exibidos e que o usuario possa copiar mais de uma linha ao mesmo tempo em diferentes colunas
