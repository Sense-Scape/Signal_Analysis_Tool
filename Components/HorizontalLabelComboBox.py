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
