import sys
import ssl
import os
import urllib.request
from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QProgressBar, QPushButton

from utils.model_template import Model

ssl._create_default_https_context = ssl._create_unverified_context


class DownloadingModelWidget(QWidget):
    def __init__(self):
        super().__init__()
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
        # calculate the progress
        readed_data = blocknum * blocksize

        if totalsize > 0:
            download_percentage = readed_data * 100 // totalsize
            self.progressBar.setValue(download_percentage)
            QApplication.processEvents()

    # method to download any file using urllib
    def download(self, model: Model):
        parsed_url = model.parsed_url
        file_name = os.path.basename(parsed_url.path)
        # specify save location where the file is to be saved
        save_loc = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(save_loc, file_name)
        print(model.url)
        # Downloading using urllib
        try:
            urllib.request.urlretrieve(model.url, full_path, self.handle_progress)
        except urllib.error.URLError:
            self.label.show()
            print("Возможно проблемы с интернетом")
        self.label.setText('Скачано!')
        self.label.show()
        self.button.setText("Закрыть")
        self.button.show()


if __name__ == '__main__':
    from settings import small_model, big_model

    # Получаем список аргументов командной строки
    print('downloading')
    args = sys.argv
    # Получаем параметр
    param = small_model
    # Создаем приложение
    App = QApplication(sys.argv)
    # Создаем окно приложения с переданным параметром
    window = DownloadingModelWidget()
    window.download(param)

    sys.exit(App.exec())
