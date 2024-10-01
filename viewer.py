from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

import librosa
import librosa.display
import pygame
import time


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

from scipy.fftpack import fft
from scipy import signal

import numpy as np
import os

from Components.HorizontalLabelInput import HorizontalLabelInput
from Components.HorizontalLabelComboBox import HorizontalLabelComboBox

class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Insert Funny and Quirky Comment")

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
        self.fft_hop = HorizontalLabelInput("FFT Hop","256")
        self.integration_count = HorizontalLabelInput("Integration Count","1")

        self.fft_window = HorizontalLabelComboBox("FFT Window", ["Rect", "Hanning", "Hamming", "Blackman"])
        self.spectrum_mode = HorizontalLabelComboBox("Spectrum Mode", ["Amplitude [dB]", "Amplitude [lin]", "Phase [Rad]", "Phase [Deg]"])

        input_layout.addWidget(self.fft_size)
        input_layout.addWidget(self.fft_hop)
        input_layout.addWidget(self.integration_count)
        input_layout.addWidget(self.fft_window)
        input_layout.addWidget(self.spectrum_mode)

        # Buttons

        self.plot_image_button = QPushButton("Plot Image")
        self.plot_image_button.clicked.connect(lambda: self.update_images())
        input_layout.addWidget(self.plot_image_button)

        self.play_audio_button = QPushButton("Play Audio")
        self.play_audio_button.clicked.connect(self.play_audio)
        input_layout.addWidget(self.play_audio_button)

        layout.addWidget(input_group)

        # Set the central widget
        self.setCentralWidget(central_widget)

        # Connect the canvas click event
        self.spectrogram_canvas.mpl_connect('button_press_event', self.on_click)
        self.Sxx = None  # Store spectrogram data
        self.showMaximized() 

    def update_images(self):

        if not(self.load_audio_data()):
            self.show_popup("File Not Found")
            return False

        msg = self.show_popup("Loading", False)

        self.generate_spectrogram_data()

        self.update_spectrogram_image()
        self.update_spectrum_image(0)

        msg.close()
    
    def update_spectrogram_image(self):
        
        self.freq_max_khz = self.sample_rate_hz/(2*1000)
        time_max_s = len(self.data[0,:])*1/self.sample_rate_hz

        # Plot the spectrogram
        self.axes.clear()
        self.axes.imshow(self.Sxx[0], origin='lower', aspect="auto", extent=[0,time_max_s, 0, self.freq_max_khz])
        self.axes.set_xlabel('Time [s]')
        self.axes.set_ylabel('Frequency [KHz]')
        self.axes.set_title('Spectrogram of \n' + self.file_path_label.text())

        self.spectrogram_canvas.draw()
        
    def update_spectrum_image(self, spectrum_column_index):
        
        if self.Sxx is not None:
                
                # Get the column corresponding to the clicked x-coordinate (time index)
                column_data = self.Sxx[0][:, spectrum_column_index]
                freq_axis = np.linspace(1,len(column_data),len(column_data))*self.freq_max_khz/len(column_data)
                _, x_max = self.axes.get_xlim()
                slice_time = np.round(x_max*spectrum_column_index/np.shape(self.Sxx[0])[1],1)

                # Plot the column data (frequency vs. intensity)
                self.spectrum_axes.clear()
                self.spectrum_axes.plot(freq_axis,column_data)
                self.spectrum_axes.set_xlabel('Frequency [KHz]')
                self.spectrum_axes.set_ylabel('Intensity [Arb dB]')
                self.spectrum_axes.set_title(f'Spectrum Sample at Time of {slice_time} Seconds of \n ' + self.file_path_label.text())

                self.set_spectrum_axes_limits()

                # Update the column plot canvas
                self.spectrum_canvas.draw()
                
    def set_spectrum_axes_limits(self):

        selected_spectrum_mode = self.spectrum_mode.getInputText()
        
        if selected_spectrum_mode == "Amplitude [dB]":
           self.spectrum_axes.set_ylim([-60,60])
        elif selected_spectrum_mode == "Amplitude [lin]":
            self.spectrum_axes.set_ylim([-1,50])
        elif selected_spectrum_mode == "Phase [Rad]":
            self.spectrum_axes.set_ylim([-1.1*np.pi,1.1*np.pi])
        elif selected_spectrum_mode == "Phase [Deg]":
            self.spectrum_axes.set_ylim([-185,185])

    def on_click(self, event):
        if event.inaxes == self.axes:  # Ensure the click is inside the spectrogram plot
            
            # Check where one clicked 
            x_axis_timestamp = int(event.xdata)
            _, x_max = self.axes.get_xlim()

            # Convert the time stamp to the index in spectorgram
            spectrogram_shape_tuple = np.shape(self.Sxx[0])
            spectrum_column_index = int(np.floor(spectrogram_shape_tuple[1]*x_axis_timestamp/x_max))

            # Plot that part of the spectrogram
            self.update_spectrum_image(spectrum_column_index) 

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

    def load_audio_data(self):

        # First check if path exists
        if not(os.path.exists(self.file_path_label.text())):
            return False

        # Then load it
        self.data, self.sample_rate_hz \
            = librosa.load(self.file_path_label.text(),sr=None, mono=False)

        # Lets determine the number of audio channels
        if len(np.shape(self.data)) == 1:
            self.num_channels = 1
        else:
            self.num_channels = np.shape(self.data)[0]

        # Then reshape to what the program expects in the case of one channel
        if self.num_channels == 1:
            self.data = np.reshape(self.data, [1,-1])
            print(np.shape( self.data))

        return True


    def play_audio(self):

        # First check if path exists
        if not(os.path.exists(self.file_path_label.text())):
            self.show_popup("File Not Found")
            return
            
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.load(self.file_path_label.text())
        pygame.mixer.music.play()

    
    def show_popup(self, text, use_button_continue = True):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(text) 

        if use_button_continue:
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        else:
            msg.setStandardButtons(QMessageBox.StandardButton.NoButton)

        # Show the message box non-blocking
        msg.show()
        # Process pending events to ensure the text is displayed
        QApplication.processEvents()

        return msg

    def get_selected_window(self):

        selected_window = self.fft_window.getInputText()
        window_length = int(self.fft_size.getInputText())
        window = np.ones(window_length)

        if selected_window == "Blackman":
            window = np.blackman(window_length)
        elif selected_window == "Hamming":
            window = np.hamming(window_length)
        elif selected_window == "Hanning":
            window = np.hanning(window_length)

        return window
    
    def generate_spectrogram_data(self):
        
        # Generate spectrogram game
        self.Sxx = {}
        window = self.get_selected_window()

        for i in range(self.num_channels):
            SFT = signal.ShortTimeFFT(win=window,
                                mfft=int(self.fft_size.getInputText()),
                                hop=int(self.fft_hop.getInputText()),
                                fs=self.sample_rate_hz,  
                                fft_mode="onesided"
                                )
            self.Sxx[i] = SFT.stft(self.data[i,:])

            # Process data further
            self.apply_integration(i)
            self.apply_spectrum_mode(i)

    
    def apply_integration(self, channel_index):

        # Split the array into groups
        tmp = np.abs(self.Sxx[channel_index])
        averaging_count = int(self.integration_count.getInputText())
        groups = np.array_split(self.Sxx[channel_index], np.arange(averaging_count, tmp.shape[1], averaging_count), axis=1)
        self.Sxx[channel_index] = np.array([group.sum(axis=1) for group in groups]).T
    
    def apply_spectrum_mode(self, channel_index):

        selected_spectrum_mode = self.spectrum_mode.getInputText()

        if selected_spectrum_mode == "Amplitude [dB]":
           self.Sxx[channel_index] = 20*np.log10(np.abs(self.Sxx[channel_index]))
        elif selected_spectrum_mode == "Amplitude [lin]":
            self.Sxx[channel_index] = np.abs(self.Sxx[channel_index])
        elif selected_spectrum_mode == "Phase [Rad]":
            self.Sxx[channel_index] = np.angle(self.Sxx[channel_index], deg=False)
        elif selected_spectrum_mode == "Phase [Deg]":
            self.Sxx[channel_index] = np.angle(self.Sxx[channel_index], deg=True)

app = QApplication([])
window = MainWindow()
app.exec()