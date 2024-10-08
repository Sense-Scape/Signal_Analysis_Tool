from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *


class HorizontalLabelComboBox(QWidget):
    def __init__(self, description, items, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)

        self.description_label = QLabel(description)
        self.combo_box =  QComboBox(self)
        self.combo_box.addItems(items)

        layout.addWidget(self.description_label)
        layout.addWidget(self.combo_box)

        self.setLayout(layout)

    def getInputText(self):
        return self.combo_box.currentText()
    
    def set_items(self, items):
        self.combo_box.clear()
        self.combo_box.addItems(items)

    def enable(self):
        self.combo_box.setEnabled(True)
        self.description_label.setStyleSheet("color: black;")
        self.combo_box.setStyleSheet("""
            QComboBox {
                background-color: white;
                color: black;
            }
            QComboBox:hover {
                background-color: lightblue;
            }
        """)

    def disable(self):
        self.combo_box.setEnabled(False)
        self.combo_box.setStyleSheet("""
            QComboBox {
                background: lightgrey;
                color: darkgrey;
            }
            QComboBox:hover {
                background: lightgrey;
            }
        """)
        self.description_label.setStyleSheet("color: grey;")
