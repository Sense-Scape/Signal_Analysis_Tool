from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

import librosa
import librosa.display
import pygame

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

from scipy.fftpack import fft
from scipy import signal

import numpy as np
import os

from Components.HorizontalLabelInput import HorizontalLabelInput

class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Main Window with Input Box")

        # Central widget and layout
        central_widget = QWidget()
        layout = QHBoxLayout()  # Use QHBoxLayout for horizontal arrangement
        central_widget.setLayout(layout)

        plots_layout = QVBoxLayout()
        
        ###     Spectrogram     ###

        # Plot area for the spectrogram
        self.figure, self.axes = plt.subplots()
        self.figure.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.15)
        self.spectrogram_canvas = FigureCanvasQTAgg(self.figure)
        self.axes.plot([],[])

        # Toolbar and figure layout
        plots_layout.addWidget(NavigationToolbar(self.spectrogram_canvas, self))
        plots_layout.addWidget(self.spectrogram_canvas)

        ###     Spectrum     ###

        # Add a second figure for plotting the column data
        self.spectrum_figure, self.spectrum_axes = plt.subplots()
        self.spectrum_figure.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.15)
        self.spectrum_canvas = FigureCanvasQTAgg(self.spectrum_figure)
        self.spectrum_axes.plot([],[])

        # Toolbar and figure layout
        plots_layout.addWidget(NavigationToolbar(self.spectrum_canvas, self))
        plots_layout.addWidget(self.spectrum_canvas)

        # Create a new widget to hold the spectrogran_toolbar_layout
        toolbar_widget = QWidget()
        toolbar_widget.setLayout(plots_layout)
        layout.addWidget(toolbar_widget)

        ###

        # File Input 
        input_group = QGroupBox("Input Parameters")
        input_layout = QVBoxLayout()
        input_group.setLayout(input_layout)

        self.file_path_label = QLabel("No file selected")
        input_layout.addWidget(self.file_path_label)

        self.load_file_button = QPushButton("Load File")
        self.load_file_button.clicked.connect(self.load_file)
        input_layout.addWidget(self.load_file_button)

        # Inputs

        self.fft_size = HorizontalLabelInput("FFT Size", "256")
        self.fft_overlap = HorizontalLabelInput("FFT Overlap","0")
        self.integration_count = HorizontalLabelInput("Integration Count","1")

        input_layout.addWidget(self.fft_size)
        input_layout.addWidget(self.fft_overlap)
        input_layout.addWidget(self.integration_count)

        # Buttons

        self.plot_image_button = QPushButton("Plot Image")
        self.plot_image_button.clicked.connect(lambda: self.update_image())
        input_layout.addWidget(self.plot_image_button)

        self.save_image_button = QPushButton("Save Spectrogram")
        self.save_image_button.clicked.connect(self.save_spectrogram_image)
        input_layout.addWidget(self.save_image_button)

        self.save_image_button = QPushButton("Save Spectrum")
        self.save_image_button.clicked.connect(self.save_spectrum_image)
        input_layout.addWidget(self.save_image_button)

        self.play_audio_button = QPushButton("Play Audio")
        self.play_audio_button.clicked.connect(self.play_audio)
        input_layout.addWidget(self.play_audio_button)

        layout.addWidget(input_group)

        # Set the central widget
        self.setCentralWidget(central_widget)

        # Connect the canvas click event
        self.spectrogram_canvas.mpl_connect('button_press_event', self.on_click)
        self.Sxx = None  # Store spectrogram data
        self.show()

    def update_image(self):

            # First check if path exists
            if not(os.path.exists(self.file_path_label.text())):
                self.show_popup("File Not Found")
                return

            # Then load it
            data, fs = librosa.load(self.file_path_label.text(),sr=None)

            f, t, self.Sxx = signal.spectrogram(data, 
                                                nperseg=int(self.fft_size.getInputText()),
                                                noverlap=int(self.fft_overlap.getInputText()),
                                                fs=fs, 
                                                mode="psd", 
                                                return_onesided=True
                                                )

             # Split the array into groups
            tmp = np.abs(self.Sxx)
            averaging_count = int(self.integration_count.getInputText())
            groups = np.array_split(self.Sxx, np.arange(averaging_count, tmp.shape[1], averaging_count), axis=1)
            tmp =np.array([group.sum(axis=1) for group in groups]).T

            
            self.Sxx_proc = tmp

            freq_max = fs/(2*1000)
            time_max = len(data)*1/fs

            print(freq_max)

            # Plot the spectrogram
            self.axes.clear()
            self.axes.imshow(20*np.log10(self.Sxx_proc), origin='lower', aspect="auto", extent=[0,time_max, 0, freq_max])
            self.axes.set_xlabel('Time [s]')
            self.axes.set_ylabel('Frequency [KHz]')
            self.axes.set_title('Spectrogram of \n' + self.file_path_label.text())

            # Update the canvas to display the plot
            self.spectrogram_canvas.draw()

    def on_click(self, event):
        if event.inaxes == self.axes:  # Ensure the click is inside the spectrogram plot
            x_click = int(event.xdata)

            if self.Sxx is not None:
                # Get the column corresponding to the clicked x-coordinate (time index)
                column_data = 20 * np.log10(np.abs(self.Sxx_proc[:, x_click]))

                # Plot the column data (frequency vs. intensity)
                self.spectrum_axes.clear()
                self.spectrum_axes.plot(column_data)
                self.spectrum_axes.set_xlabel('Frequency [Hz]')
                self.spectrum_axes.set_ylabel('Intensity [Arb dB]')
                self.spectrum_axes.set_title(f'Spectrum Sample at Time of {x_click} Seconds of \n ' + self.file_path_label.text())
                
                # Update the column plot canvas
                self.spectrum_canvas.draw()

    def load_file(self):
        # Open a file dialog to let the user select a file
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "*.wav")

        # Check if a file was selected
        if file_path:
            # Update the label to display the selected file path
            self.file_path_label.setText(f"{file_path}")
        else:
            # Handle the case where no file was selected
            self.file_path_label.setText("No file selected")

    def save_spectrogram_image(self):
        # Open a file dialog to select where to save the image
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG Files (*.png);;JPEG Files (*.jpg)")

        if save_path:
            # Save the current figure as an image
            self.figure.savefig(save_path)

    def save_spectrum_image(self):
        # Open a file dialog to select where to save the image
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG Files (*.png);;JPEG Files (*.jpg)")

        if save_path:
            # Save the current figure as an image
            self.spectrum_figure.savefig(save_path)

    def play_audio(self):

        # First check if path exists
        if not(os.path.exists(self.file_path_label.text())):
            self.show_popup("File Not Found")
            return
            
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.load(self.file_path_label.text())
        pygame.mixer.music.play()

    
    def show_popup(self, text):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(text) 
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

app = QApplication([])
window = MainWindow()
app.exec()