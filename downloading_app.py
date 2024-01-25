import urllib.request
from urllib.parse import urlparse, ParseResult

from PyQt6.QtWidgets import *
import sys
import ssl
import os
import re
from dataclasses import dataclass

ssl._create_default_https_context = ssl._create_unverified_context

@dataclass
class Model:
    __model_name: str
    __url: str

    def __post_init__(self):
        if not self._is_valid_url(self.url):
            raise ValueError("Invalid URL")

    @property
    def parsed_url(self):
        return urlparse(self.__url)


    @property
    def url(self):
        return self.__url

    @property
    def model_name(self):
        return self.__model_name

    @property
    def zip_name(self):
        return os.path.basename(self.parsed_url.path)

    @property
    def dir_name(self):
        return self.zip_name.rstrip('.zip')

    @staticmethod
    def _is_valid_url(url):
        pattern = r"^https://(.+)\.zip$"
        return re.match(pattern, url) is not None


big_model = Model('big_model', 'https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip')
small_model = Model('small_model', 'https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip')


class DownloadingModelApp(QWidget):
    def __init__(self, model_type):
        super().__init__()
        self.model = big_model if big_model.model_name == model_type else small_model
        # calling a defined method to initialize UI
        self.init_UI()

    # method for creating UI widgets
    def init_UI(self):
        # creating progress bar
        self.progressBar = QProgressBar(self)

        # setting its size
        self.progressBar.setGeometry(25, 45, 210, 30)

        # creating push button to start download
        self.button = QPushButton('Закрыть', self)

        # assigning position to button
        self.button.move(50, 100)

        # assigning activity to push button
        self.button.clicked.connect(sys.exit)
        self.button.hide()

        # setting window geometry
        self.setGeometry(310, 310, 280, 170)

        self.label = QLabel("Проблемы с интернетом", self)
        self.label.move(20, 20)
        self.label.hide()

        # setting window action
        self.setWindowTitle("Model downloading ")

        # showing all the widgets
        self.show()

    # when push button is pressed, this method is called
    def handle_progress(self, blocknum, blocksize, totalsize):
        ## calculate the progress
        readed_data = blocknum * blocksize

        if totalsize > 0:
            download_percentage = readed_data * 100 // totalsize
            self.progressBar.setValue(download_percentage)
            QApplication.processEvents()

    # method to download any file using urllib
    def download(self):
        # specify the url of the file which is to be downloaded
        # down_url = 'https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip'  # specify download url here
        # parsed_url = urlparse(down_url)
        parsed_url = self.model.parsed_url
        file_name = os.path.basename(parsed_url.path)
        # specify save location where the file is to be saved
        save_loc = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(save_loc, file_name)
        print(self.model.url)
        # Downloading using urllib
        try:
            urllib.request.urlretrieve(self.model.url, full_path, self.handle_progress)
        except urllib.error.URLError:
            self.label.show()
            print("Возможно проблемы с интернетом")
        self.label.setText('Скачано!')
        self.label.show()
        self.button.setText("Закрыть")
        self.button.show()




# main method to call our app
if __name__ == '__main__':
    # create app
    # App = QApplication(sys.argv)
    #
    # # create the instance of our window
    # window = DownloadingModelApp(big_model)
    # Получаем список аргументов командной строки
    print('downloading')
    args = sys.argv
    # Получаем параметр
    param = args[1]
    # Создаем приложение
    App = QApplication(sys.argv[1:])
    # Создаем окно приложения с переданным параметром
    window = DownloadingModelApp(param)
    window.download()

    # start the app
    sys.exit(App.exec())
