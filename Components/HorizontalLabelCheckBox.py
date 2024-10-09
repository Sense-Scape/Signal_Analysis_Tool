from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *


class HorizontalCheckbox(QWidget):
    def __init__(self, description, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)

        self.description_label = QLabel(description)
        self.check_box =  QCheckBox(self)

        layout.addWidget(self.description_label)
        layout.addWidget(self.check_box)

        self.setLayout(layout)

    def getInputText(self):
        return self.check_box.text()
    
    def enable(self):
        self.check_box.setEnabled(True)
        self.description_label.setStyleSheet("color: black;")
        self.check_box.setStyleSheet("""
        QCheckBox {
            color: black;
        }
        QCheckBox:hover {
            background-color: lightblue;
        }
        QCheckBox::indicator {
        /* Reset the indicator to the default style */
        }
        """)

    def disable(self):
        self.check_box.setEnabled(False)
        self.description_label.setStyleSheet("color: grey;")
        self.check_box.setStyleSheet("""
        QCheckBox {
            color: grey;
        }
        QCheckBox:hover {

        }
        QCheckBox::indicator {
        width: 15px;
        height: 15px;
        background-color: lightgrey;
        border: 0.5px solid black; 
        border-radius: 5px; 
        }
        """)
        
