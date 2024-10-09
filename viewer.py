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
from Components.HorizontalLabelCheckBox import HorizontalCheckbox
from PlotConfig import PlotConfig

class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Insert Funny and Quirky Comment")

        # Central widget and layout
        central_widget = QWidget()
        layout = QHBoxLayout()  # Use QHBoxLayout for horizontal arrangement
        central_widget.setLayout(layout)

        self.channel_plots_tabs = QTabWidget()
        self.channel_plots = {}
        self.num_channels = 0

        layout.addWidget(self.channel_plots_tabs)

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

        self.enabled_phase_check_box = HorizontalCheckbox("Enable Phase Analysis")
        self.enabled_phase_check_box.disable()
        self.phase_channel_one = HorizontalLabelComboBox("Phase Channel One", [])
        self.phase_channel_one.disable()
        self.phase_channel_two = HorizontalLabelComboBox("Phase Channel Two", [])
        self.phase_channel_two.disable()
        

        input_layout.addWidget(self.fft_size)
        input_layout.addWidget(self.fft_hop)
        input_layout.addWidget(self.integration_count)
        input_layout.addWidget(self.fft_window)
        input_layout.addWidget(self.spectrum_mode)
        input_layout.addWidget(self.enabled_phase_check_box)
        input_layout.addWidget(self.phase_channel_one)
        input_layout.addWidget(self.phase_channel_two)

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
        self.showMaximized() 

    def update_images(self):

        msg = self.show_popup("Loading", False)

        self.Sxx = {}

        self.remove_all_tabs()

        for i in range(self.num_channels):
            self.add_plot_tab(i)
            self.generate_spectrogram_data(i)
            self.apply_integration(i)
            self.apply_spectrum_mode(i)
            self.update_spectrogram_image(i)
            self.update_spectrum_image(i, 0)

        if self.enabled_phase_check_box.get_check_state():
            self.add_plot_tab(self.num_channels + 1)
            self.update_differential_image()
            self.update_spectrum_image(self.num_channels + 1, 0)


        msg.close()
    
    def remove_all_tabs(self):

        if self.num_channels:
            for i in range(self.num_channels):
                self.remove_plot_tab(i)
            
            # phase is always channels + 1
            if self.enabled_phase_check_box.get_check_state():
                self.remove_plot_tab(self.num_channels + 1)

    def update_differential_image(self):

        window = self.get_selected_window()

        SFT = signal.ShortTimeFFT(win=window,
                            mfft=int(self.fft_size.getInputText()),
                            hop=int(self.fft_hop.getInputText()),
                            fs=self.sample_rate_hz,  
                            fft_mode="onesided"
                            )
        
        channel_one = int(self.phase_channel_one.getInputText())
        channel_two = int(self.phase_channel_two.getInputText())

        Axx1 = np.angle(SFT.stft(self.data[channel_one,:]), deg=True)
        Axx2 = np.angle(SFT.stft(self.data[channel_two,:]), deg=True)
        A = Axx1 - Axx2

        
        channel_index = self.num_channels + 1
        self.Sxx[channel_index] = A

        self.freq_max_khz = self.sample_rate_hz/(2*1000)
        time_max_s = len(self.data[0,:])*1/self.sample_rate_hz

        # Plot the spectrogram
        self.channel_plots[channel_index].axes.clear()
        image  = self.channel_plots[channel_index].axes.imshow(A, origin='lower', aspect="auto", extent=[0,time_max_s, -180,180 ], cmap='viridis')
        cbar = self.channel_plots[channel_index].figure.colorbar(image, ax=self.channel_plots[channel_index].axes)
        self.channel_plots[channel_index].axes.set_xlabel('Time [s]')
        self.channel_plots[channel_index].axes.set_ylabel('Phase [Deg]')
        self.channel_plots[channel_index].axes.set_title('Spectrogram of \n' + self.file_path_label.text())

        self.channel_plots[channel_index].spectrogram_canvas.draw()

    def update_spectrogram_image(self, channel_index):
        
        self.freq_max_khz = self.sample_rate_hz/(2*1000)
        time_max_s = len(self.data[0,:])*1/self.sample_rate_hz
    
        # Plot the spectrogram
        self.channel_plots[channel_index].axes.clear()
        self.channel_plots[channel_index].axes.imshow(self.Sxx[channel_index], origin='lower', aspect="auto", extent=[0,time_max_s, 0, self.freq_max_khz])
        self.channel_plots[channel_index].axes.set_xlabel('Time [s]')
        self.channel_plots[channel_index].axes.set_ylabel('Frequency [KHz]')
        self.channel_plots[channel_index].axes.set_title('Spectrogram of \n' + self.file_path_label.text())

        self.channel_plots[channel_index].spectrogram_canvas.draw()
        
    def update_spectrum_image(self, channel_index, spectrum_column_index):
        
        if self.Sxx is not None:
                
                # Get the column corresponding to the clicked x-coordinate (time index)
                column_data = self.Sxx[channel_index][:, spectrum_column_index]
                freq_axis = np.linspace(1,len(column_data),len(column_data))*self.freq_max_khz/len(column_data)
                _, x_max = self.channel_plots[channel_index].axes.get_xlim()
                slice_time = np.round(x_max*spectrum_column_index/np.shape(self.Sxx[channel_index])[1],1)

                # Plot the column data (frequency vs. intensity)
                self.channel_plots[channel_index].spectrum_axes.clear()
                self.channel_plots[channel_index].spectrum_axes.plot(freq_axis,column_data)
                self.channel_plots[channel_index].spectrum_axes.set_xlabel('Frequency [KHz]')
                self.channel_plots[channel_index].spectrum_axes.set_ylabel('Intensity [Arb dB]')
                self.channel_plots[channel_index].spectrum_axes.set_title(f'Spectrum Sample at Time of {slice_time} Seconds of \n ' + self.file_path_label.text())

                self.set_spectrum_axes_limits(channel_index)

                # Update the column plot canvas
                self.channel_plots[channel_index].spectrum_canvas.draw()
                
    def set_spectrum_axes_limits(self,channel_index):

        selected_spectrum_mode = self.spectrum_mode.getInputText()
        
        if selected_spectrum_mode == "Amplitude [dB]":
           self.channel_plots[channel_index].spectrum_axes.set_ylim([-60,60])
        elif selected_spectrum_mode == "Amplitude [lin]":
            self.channel_plots[channel_index].spectrum_axes.set_ylim([-1,50])
        elif selected_spectrum_mode == "Phase [Rad]":
            self.channel_plots[channel_index].spectrum_axes.set_ylim([-1.1*np.pi,1.1*np.pi])
        elif selected_spectrum_mode == "Phase [Deg]":
            self.channel_plots[channel_index].spectrum_axes.set_ylim([-185,185])

    def on_click(self, event):
        
        for i in range(self.num_channels):

            if event.inaxes == self.channel_plots[i].axes:  # Ensure the click is inside the spectrogram plot
            
                # Check where one clicked 
                x_axis_timestamp = int(event.xdata)
                _, x_max = self.channel_plots[i].axes.get_xlim()

                # Convert the time stamp to the index in spectorgram
                spectrogram_shape_tuple = np.shape(self.Sxx[i])
                spectrum_column_index = int(np.floor(spectrogram_shape_tuple[1]*x_axis_timestamp/x_max))

                # Plot that part of the spectrogram
                self.update_spectrum_image(i, spectrum_column_index) 

    def load_file(self):

        msg = self.show_popup("Loading", False)

        # Open a file dialog to let the user select a file
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "*.wav")

        # Check if a file was selected
        if not(file_path):
            self.file_path_label.setText("No file selected")
            return
        
        # Update the label to display the selected file path
        self.file_path_label.setText(f"{file_path}")
        self.load_audio_data()

        if self.num_channels > 1:
            self.enable_phase_analysis_options()
        else:
            self.disable_phase_analysis_options()
        
        msg.close()


            
    def enable_phase_analysis_options(self):

        self.enabled_phase_check_box.enable()

        channel_indicies = [str(i) for i in range(self.num_channels)]
        self.phase_channel_one.enable()
        self.phase_channel_one.set_items(channel_indicies)
        self.phase_channel_two.enable()
        self.phase_channel_two.set_items(channel_indicies)

    def disable_phase_analysis_options(self):

        self.enabled_phase_check_box.disable()

        self.phase_channel_one.disable()
        self.phase_channel_one.set_items([])
        self.phase_channel_two.disable()
        self.phase_channel_two.set_items([])

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
    
    def generate_spectrogram_data(self, channel_index):
        
        # Generate spectrogram game
        window = self.get_selected_window()

        SFT = signal.ShortTimeFFT(win=window,
                            mfft=int(self.fft_size.getInputText()),
                            hop=int(self.fft_hop.getInputText()),
                            fs=self.sample_rate_hz,  
                            fft_mode="onesided"
                            )
        
        self.Sxx[channel_index] = SFT.stft(self.data[channel_index,:])

    
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

    def remove_plot_tab(self, channel_index):
        self.channel_plots[channel_index] = PlotConfig()
        self.channel_plots_tabs.removeTab(0)

    def add_plot_tab(self, channel_index):

        self.channel_plots[channel_index] = PlotConfig()
        self.channel_plots[channel_index].plots_layout = QVBoxLayout()
        
        ###     Spectrogram     ###
        self.channel_plots[channel_index].figure, self.channel_plots[channel_index].axes = plt.subplots()
        self.channel_plots[channel_index].figure.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.15)
        self.channel_plots[channel_index].spectrogram_canvas = FigureCanvasQTAgg(self.channel_plots[channel_index].figure)
        self.channel_plots[channel_index].axes.plot([],[])

        # Toolbar and figure layout
        self.channel_plots[channel_index].plots_layout.addWidget(NavigationToolbar(self.channel_plots[channel_index].spectrogram_canvas, self))
        self.channel_plots[channel_index].plots_layout.addWidget(self.channel_plots[channel_index].spectrogram_canvas)

        ###     Spectrum     ###
        self.channel_plots[channel_index].spectrum_figure, self.channel_plots[channel_index].spectrum_axes = plt.subplots()
        self.channel_plots[channel_index].spectrum_figure.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.15)
        self.channel_plots[channel_index].spectrum_canvas = FigureCanvasQTAgg(self.channel_plots[channel_index].spectrum_figure)
        self.channel_plots[channel_index].spectrum_axes.plot([],[])

        # Toolbar and figure layout
        self.channel_plots[channel_index].plots_layout.addWidget(NavigationToolbar(self.channel_plots[channel_index].spectrum_canvas, self))
        self.channel_plots[channel_index].plots_layout.addWidget(self.channel_plots[channel_index].spectrum_canvas)

        # Create a new widget to hold the spectrogran_toolbar_layout
        toolbar_widget = QWidget()
        toolbar_widget.setLayout(self.channel_plots[channel_index].plots_layout)
    
        self.channel_plots_tabs.addTab(toolbar_widget,"Channel " + str(channel_index))
        self.channel_plots[channel_index].spectrogram_canvas.mpl_connect('button_press_event', self.on_click)


app = QApplication([])
window = MainWindow()
app.exec()