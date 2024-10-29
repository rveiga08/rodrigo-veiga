import sys
import base64
import requests
import psycopg2
import logging
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QByteArray

# Determinar o diretório onde o executável está localizado
if getattr(sys, 'frozen', False):
    # Se estiver congelado (compilado via PyInstaller), usar o diretório do executável
    application_path = os.path.dirname(sys.executable)
else:
    # Se estiver rodando diretamente como script, usar o diretório do script
    application_path = os.path.dirname(os.path.abspath(__file__))

# Configuração do logging para criar arquivos de log no diretório do aplicativo
log_file_error = os.path.join(application_path, 'error_log.txt')
log_file_search_error = os.path.join(application_path, 'search_error_log.txt')

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_error),
        logging.FileHandler(log_file_search_error)
    ]
)

class Base64ImageViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_equipment_list()

    def initUI(self):
        self.setWindowTitle('Visualizador de Imagens Biometria - Intelbras')

        # Definir o tamanho fixo da janela
        self.setFixedSize(400, 600)  # Largura e altura fixas, ajuste conforme necessário

        # Layout
        layout = QVBoxLayout()

        # Campo para selecionar o equipamento
        self.equipment_list = QComboBox(self)
        self.equipment_list.currentIndexChanged.connect(self.auto_fill_fields)
        layout.addWidget(self.equipment_list)

        # Campos de entrada
        self.ip_input = QLineEdit(self)
        self.ip_input.setPlaceholderText('Digite o IP do equipamento')
        layout.addWidget(self.ip_input)

        self.user_input = QLineEdit(self)
        self.user_input.setPlaceholderText('Digite o usuário')
        layout.addWidget(self.user_input)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText('Digite a senha')
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.id_input = QLineEdit(self)
        self.id_input.setPlaceholderText('Digite o ID do acionador')
        layout.addWidget(self.id_input)

        self.search_button = QPushButton('Buscar Imagem', self)
        self.search_button.clicked.connect(self.search_image)
        layout.addWidget(self.search_button)

        # Área para exibir a imagem
        self.image_label = QLabel(self)
        layout.addWidget(self.image_label)

        # Texto "Developed by Rodrigo Veiga" na parte inferior
        self.developer_label = QLabel("Developed by Rodrigo Veiga", self)
        self.developer_label.setStyleSheet("font: italic;")
        layout.addWidget(self.developer_label)

        self.setLayout(layout)

    def load_equipment_list(self):
        try:
            # Conectando ao banco de dados PostgreSQL
            connection = psycopg2.connect(
                host="localhost",
                database="database-name",
                user="database-user",
                password="database-pass"
            )
            cursor = connection.cursor()

            # Consultar o id do tipo de equipamento
            cursor.execute("SELECT id FROM tipoequipamento WHERE \"tipoEquip\" = 'FACIAL INTELBRAS'")
            id_tipoequipamento = cursor.fetchone()

            if id_tipoequipamento:
                id_tipoequipamento = id_tipoequipamento[0]

                # Consultar os equipamentos disponíveis
                cursor.execute(f"SELECT descricao, ip, user AS user_equip, password FROM equipamento WHERE id_tipoequipamento = {id_tipoequipamento}")
                equipamentos = cursor.fetchall()

                for descricao, ip, user_equip, password in equipamentos:
                    self.equipment_list.addItem(descricao, (ip, user_equip, password))
            else:
                QMessageBox.critical(self, "Error", "Tipo de equipamento 'FACIAL INTELBRAS' não encontrado.")
        except psycopg2.Error as e:
            logging.error(f"Database Error: {str(e)}")
            QMessageBox.critical(self, "Database Error", f"Failed to connect or query database: {str(e)}")
        finally:
            if connection:
                cursor.close()
                connection.close()

    def auto_fill_fields(self):
        current_item = self.equipment_list.currentData()
        if current_item:
            ip, user_equip, password = current_item
            self.ip_input.setText(ip)
            self.user_input.setText("admin")  # Preenche o campo de usuário com o valor do equipamento
            self.password_input.setText(password)  # Preenche o campo de senha com o valor do equipamento

    def search_image(self):
        ip = self.ip_input.text()
        user = self.user_input.text()
        password = self.password_input.text()
        acionador_id = self.id_input.text()

        # Corrigir a URL para não codificar os colchetes
        url = f"http://{ip}/cgi-bin/AccessFace.cgi?action=list&UserIDList[0]={acionador_id}"
        
        try:
            # Autenticação Digest
            digest_auth = requests.auth.HTTPDigestAuth(user, password)
            
            # Enviar a requisição GET com autenticação
            response = requests.get(url, auth=digest_auth, stream=True, timeout=20, verify=False)

            if response.status_code == 400:
                # Mensagem personalizada para erro 400
                QMessageBox.critical(self, "Erro", "O ID Acionador consultado não consta no equipamento.")
                return

            response.raise_for_status()  # Levanta um erro para códigos de status HTTP 4xx/5xx

            base64_data = response.text
            # Limpar o início e o final da string base64
            start_index = base64_data.find("FaceDataList[0].PhotoData[0]=") + len("FaceDataList[0].PhotoData[0]=")
            end_index = base64_data.find("FaceDataList[0].UserID=", start_index)
            base64_string = base64_data[start_index:end_index]

            self.display_image(base64_string)
        except requests.RequestException as e:
            logging.error(f"Request Error: {str(e)}")
            QMessageBox.critical(self, "Request Error", f"Failed to fetch image data: {str(e)}")
        except Exception as e:
            logging.error(f"Error in search_image: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def display_image(self, base64_string):
        # Converter base64 para imagem e exibir
        try:
            image_data = QByteArray.fromBase64(base64_string.encode('utf-8'))
            image = QImage.fromData(image_data)
            if image.isNull():
                self.image_label.setText("Imagem inválida.")
            else:
                pixmap = QPixmap.fromImage(image)
                self.image_label.setPixmap(pixmap)
                self.image_label.setScaledContents(True)
        except Exception as e:
            logging.error(f"Error in display_image: {str(e)}")
            self.image_label.setText(f"Erro ao exibir imagem: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = Base64ImageViewer()
    viewer.show()
    sys.exit(app.exec_())
