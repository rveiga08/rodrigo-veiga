from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QDialog, QLabel
import sys
import csv
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.units import inch
from database_manager import DatabaseManager
from scheduler import run_scheduled_task

class UiManager(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.db_manager.create_local_table()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Consulta de Informações')
        self.setGeometry(100, 100, 800, 600)
        
        # Layout principal
        main_layout = QVBoxLayout()
        
        # Tabela para exibir os resultados
        self.table = QtWidgets.QTableWidget(self)
        self.table.setGeometry(50, 50, 700, 400)
        self.table.setSortingEnabled(True)  # Habilita a ordenação por colunas
        main_layout.addWidget(self.table)
        
        # Layout para os botões
        button_layout = QHBoxLayout()
        
        # Botão de atualizar
        self.refresh_button = QPushButton('Atualizar', self)
        self.refresh_button.setGeometry(350, 500, 100, 30)
        self.refresh_button.clicked.connect(self.update_table)
        button_layout.addWidget(self.refresh_button)

        # Botão para consulta manual
        self.manual_query_button = QPushButton('Executar Consulta Manual', self)
        self.manual_query_button.clicked.connect(self.run_manual_query)
        button_layout.addWidget(self.manual_query_button)

        # Botão para exportar para CSV
        self.export_csv_button = QPushButton('Exportar para CSV', self)
        self.export_csv_button.clicked.connect(self.export_to_csv)
        button_layout.addWidget(self.export_csv_button)

        # Botão para exportar para PDF
        self.export_pdf_button = QPushButton('Exportar para PDF', self)
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        button_layout.addWidget(self.export_pdf_button)

        main_layout.addLayout(button_layout)
        
        # Configura o layout principal
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Atualiza a tabela com dados ao iniciar
        self.update_table(first_run=True)

    def update_table(self, first_run=False):
        old_results = self.db_manager.get_previous_results()
        new_results = self.db_manager.execute_query()

        # Verifica se há novos dados
        new_entries = self.db_manager.get_new_entries(old_results, new_results)

        # Armazena os novos resultados no banco de dados
        self.db_manager.store_query_results(new_results)

        # Atualiza a tabela principal
        results = self.db_manager.get_previous_results()
        self.table.setRowCount(len(results))
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['idControlCondo', 'key', 'Nome', 'CNPJ', 'Data de Registro', 'Versão'])

        for i, row in enumerate(results):
            for j, value in enumerate(row):
                cell = QtWidgets.QTableWidgetItem(str(value))

                # Se este registro for um novo dado, marcar com cor de fundo diferente
                if row in new_entries:
                    cell.setBackground(QtGui.QColor(144, 238, 144))  # Cor verde clara
                self.table.setItem(i, j, cell)

    def run_manual_query(self):
        try:
            self.update_table()  # Atualiza a tabela após a consulta
        except Exception as e:
            print(f"Erro ao executar consulta manual: {e}")

    def display_new_entries(self, new_entries):
        dialog = QDialog(self)
        dialog.setWindowTitle("Novos Dados Encontrados")
        dialog.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        if not new_entries:
            label = QLabel("Nenhuma nova informação encontrada.", dialog)
            layout.addWidget(label)
        else:
            table = QtWidgets.QTableWidget(dialog)
            table.setRowCount(len(new_entries))
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(['idControlCondo', 'key', 'Nome', 'CNPJ', 'Data de Registro'])

            for i, row in enumerate(new_entries):
                for j, value in enumerate(row):
                    cell = QtWidgets.QTableWidgetItem(str(value))
                    table.setItem(i, j, cell)

            layout.addWidget(table)

        dialog.setLayout(layout)
        dialog.exec_()

    def export_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar como", "", "CSV Files (*.csv);;All Files (*)")
        if path:
            with open(path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Escreve os cabeçalhos
                headers = ['idControlCondo', 'key', 'Nome', 'CNPJ', 'Data de Registro', 'Versão']
                writer.writerow(headers)
                # Escreve os dados da tabela
                for row in range(self.table.rowCount()):
                    row_data = [self.table.item(row, col).text() for col in range(self.table.columnCount())]
                    writer.writerow(row_data)

    def export_to_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar como", "", "PDF Files (*.pdf);;All Files (*)")
        if path:
            doc = SimpleDocTemplate(path, pagesize=landscape(letter))
            elements = []

            # Adiciona título ao documento
            styles = getSampleStyleSheet()
            title = Paragraph("Relatório de Dados Exportados", styles['Title'])
            elements.append(title)
            elements.append(Paragraph("<br/><br/>", styles['Normal']))

            # Cabeçalhos e dados
            headers = ['idControlCondo', 'key', 'Nome', 'CNPJ', 'Data de Registro', 'Versão']
            data = [headers]
            for row in range(self.table.rowCount()):
                row_data = [self.table.item(row, col).text() for col in range(self.table.columnCount())]
                data.append(row_data)

            # Ajuste das larguras das colunas para evitar sobreposição
            col_widths = [1*inch, 2.6*inch, 4*inch, 1.6*inch, 1.5*inch, 1*inch]

            # Criação da tabela
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)

            # Geração do PDF
            doc.build(elements)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = UiManager()
    ui.show()
    sys.exit(app.exec_())
