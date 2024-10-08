from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *


class HorizontalLabelInput(QWidget):
    def __init__(self, description, defualt_value="", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)

        self.description_label = QLabel(description)
        self.edit_box =  QLineEdit(self)
        self.edit_box.setText(defualt_value)

        layout.addWidget(self.description_label)
        layout.addWidget(self.edit_box)

        self.setLayout(layout)

    def getInputText(self):
        return self.edit_box.text()
    
    def enable(self):
        self.edit_box.setEnabled(True)

    def disable(self):
        self.edit_box.setEnabled(False)
