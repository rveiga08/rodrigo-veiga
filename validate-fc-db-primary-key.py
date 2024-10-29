import sys
import psycopg2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QMessageBox
)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.connect_to_db()

    def init_ui(self):
        self.setWindowTitle('Tabelas Sem Chave Primária')
        layout = QVBoxLayout()
        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)
    
    def connect_to_db(self):
        config = {
            'host': 'localhost',
            'port': '5432',
            'database': 'database-name',
            'user': 'database-user',
            'password': 'database-password'
        }

        try:
            connection = psycopg2.connect(**config)
            cursor = connection.cursor()
            self.show_table_list(cursor)
        except Exception as e:
            QMessageBox.critical(self, "Erro de Conexão", f"Erro na conexão: {e}")

    def show_table_list(self, cursor):
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables t
            WHERE table_schema='public'
            AND NOT EXISTS (
                SELECT 1
                FROM information_schema.table_constraints tc
                WHERE t.table_name = tc.table_name
                AND tc.constraint_type = 'PRIMARY KEY'
            )
        """)
        tables = cursor.fetchall()

        table_info = [(table[0], False) for table in tables]

        self.progress_bar.setMaximum(len(tables))
        for idx, table in enumerate(table_info):
            self.progress_bar.setValue(idx + 1)

        self.update_table_display(table_info)

    def update_table_display(self, table_info):
        table_widget = QTableWidget()
        table_widget.setRowCount(len(table_info))
        table_widget.setColumnCount(2)
        table_widget.setHorizontalHeaderLabels(['Tabela', 'Possui Chave Primária'])
        table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for row_idx, (table_name, has_primary_key) in enumerate(table_info):
            table_widget.setItem(row_idx, 0, QTableWidgetItem(table_name))
            status = "Sim" if has_primary_key else "Não"
            table_widget.setItem(row_idx, 1, QTableWidgetItem(status))

        self.layout().addWidget(table_widget)

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
