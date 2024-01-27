import sys
import os
import json
import zipfile
import subprocess
import re

import vosk
import docx
import g4f
import textwrap
import threading
from PyQt6 import QtGui
from PyQt6.QtCore import QSettings, QDir, QRect
from PyQt6.QtGui import QAction, QFont, QIcon
from PyQt6.QtWidgets import (QApplication, QFileDialog, QMainWindow, QPushButton,
                             QTextEdit, QVBoxLayout, QWidget, QProgressBar, QMessageBox)
from downloading_app import DownloadingModelWidget
import settings

g4f.debug.logging = True  # enable logging
g4f.debug.version_check = False  # Disable automatic version checking

ffmpeg_zip_url_win = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.result = ''
        # Set default model folder
        # self.select_model_folder()
        self.model_dir = ''

    @staticmethod
    def check_model_dir(model):
        # Проверяем директорию модели в папке приложения
        app_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(app_dir, model.dir_name)  # 'vosk-model-ru-0. 42')
        print(model_dir)
        if os.path.exists(model_dir):
            return True
        return False

    def create_recognizer(self):
        self.button_transcribe.setText('Загружается модель...')
        self.button_transcribe.setEnabled(False)
        self.menuBar().setEnabled(False)
        print(self.model_dir)
        self.model = vosk.Model(self.model_dir)  # 'vosk-model-ru-0.42'
        self.rec = vosk.KaldiRecognizer(self.model, 16000)
        self.button_transcribe.setEnabled(True)
        self.button_transcribe.setText('Transcribe Audio')
        self.menuBar().setEnabled(True)

    def select_model_folder(self):
        folder_name = QFileDialog.getExistingDirectory(self, 'Select Model Folder', '')
        if folder_name:
            self.model_dir = folder_name
            self.save_model_dir(self.model_dir)

    def save_model_dir(self, model_folder):
        # Сохраняем путь в настройках приложения
        settings = QSettings('JJoy', 'AppSettings')
        settings.setValue('model_dir', model_folder)
        self.model_dir = model_folder
        # thread = threading.Thread(target=self.create_recognizer)
        # thread.start()
        self.create_recognizer()

    def init_ui(self):
        # Create UI elements
        self.button_transcribe = QPushButton('Transcribe Audio', self)
        self.button_transcribe.clicked.connect(self.transcribe_audio)

        self.button_ai = QPushButton('AI', self)
        self.button_ai.clicked.connect(self.ai_text_editing)

        self.text_edit = QTextEdit(self)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFont(QFont('Arial', 7))

        # Set layout
        layout = QVBoxLayout()
        layout.addWidget(self.button_transcribe)
        layout.addWidget(self.button_ai)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.progress_bar)

        # Create a central widget and set the layout
        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Set window title
        # icon = QIcon('icons/icon_048.ico')
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/icon.png"), state=QtGui.QIcon.State.On)
        self.setWindowIcon(icon)
        self.setWindowTitle('JJoy - Audio to Text Converter')
        self.download_widget = DownloadingModelWidget()
        self.download_widget.hide()

        # Create menu bar
        menu_bar = self.menuBar()

        # Create 'File' menu
        file_menu = menu_bar.addMenu('File')

        # Add 'Save' action to the 'File' menu
        save_action = QAction('Save', self)
        save_action.triggered.connect(self.save_as_docx)
        file_menu.addAction(save_action)

        # Add 'Select Model Folder' action to the 'File' menu
        select_model_folder_action = QAction('Select Model Folder', self)
        select_model_folder_action.triggered.connect(self.select_model_folder)
        file_menu.addAction(select_model_folder_action)

    @staticmethod
    def remove_tags(text, tag_names):
        for tag_name in tag_names:
            pattern = re.compile(r'<' + tag_name + r'>.*?</' + tag_name + r'>', re.DOTALL)
            text = re.sub(pattern, '', text)
        return text

    def ai_text_editing(self):
        text_to_edit = self.text_edit.toPlainText()
        if not text_to_edit:
            print('There is no text!')
            return
        print(g4f.version)  # check version
        print(g4f.Provider.Ails.params)  # supported args

        batches = textwrap.wrap(text_to_edit, 2260)
        ai_response = ''
        self.progress_bar.setRange(0, len(batches))
        for i, batch in enumerate(batches):
            try:
                response = g4f.ChatCompletion.create(
                    model=g4f.models.gpt_4,

                    messages=[{"role": """text editor""",
                               "content": f"Ты получишь транскрибацию аудио файла. Нужно переделать её в удобный для "
                                          f"чтения вид: поставить знаки препинания, исправить грамматику, прямую, "
                                          f"косвенную речь. Старайся как можно меньше изменять смысл текста. "
                                          f"СВОИ КОММЕНТАРИИИ НЕ ПИШИ!!! ОЦЕНОЧНЫХ СУЖДЕНИЙ НЕ ВЫСКАЗЫВАЙ!"
                                          f"Вот текст для исправления: {batch}"}],
                )  # alternative model setting
                self.progress_bar.setValue(i + 1)
            except Exception:
                self.text_edit.setPlainText("Возможно проблемы с интернетом")
                return

            if response:
                ai_response += f'\n\n{response}'
        response = self.remove_tags(ai_response, ["PHIND_SPAN_BEGIN", "PHIND_SPAN_END"]).strip()
        self.text_edit.setPlainText(response)

    def transcribe_audio(self):

        default_directory = QDir.rootPath()

        # Использование метода getOpenFileNameAndFilter() для создания диалогового окна
        file_name, _ = QFileDialog.getOpenFileName(
            parent=None,
            caption='Open Audio File',
            directory=default_directory,
            filter='Audio Files (*.mp3 *.wav)'
        )

        if not file_name:
            return

        self.button_transcribe.setEnabled(False)
        number_of_iterations = os.path.getsize(file_name) // 4000
        self.progress_bar.setRange(0, number_of_iterations)
        i = 0
        with subprocess.Popen(["ffmpeg", "-loglevel", "quiet", "-i",
                               file_name,
                               "-ar", str(16000), "-ac", "1", "-f", "s16le", "-"],
                              stdout=subprocess.PIPE) as process:
            while True:
                data = process.stdout.read(4000)
                i += 1
                if len(data) == 0:
                    break
                # self.progress_bar.setRange(0, rec.NumFrames())
                self.progress_bar.setValue(i)
                self.rec.AcceptWaveform(data)

            self.result: str = json.loads(self.rec.FinalResult())[
                'text']  # запятые в числах мешают преобразовать в json
            print(self.result)
            # Display the recognized text
            self.text_edit.setPlainText(self.result.strip())

            # Save the result as a docx file
            self.save_as_docx()
            self.button_transcribe.setEnabled(True)

    def save_as_docx(self):
        file_name, _ = QFileDialog.getSaveFileName(self, 'Save as Word Document', '', 'Word Document (*.docx)')
        if not file_name.endswith('.docx'):
            file_name = f'{file_name}.docx'
        if file_name:
            doc = docx.Document()
            doc.add_paragraph(self.text_edit.toPlainText())
            doc.save(file_name)


if __name__ == '__main__':
    model = settings.model
    app = QApplication(sys.argv)
    screen_width = QApplication.screens()[0].size().width()
    screen_height = QApplication.screens()[0].size().height()
    window = MainWindow()
    win_width = 350
    win_height = 300
    window.setGeometry(QRect((screen_width - win_width) // 2,
                             (screen_height - win_height) // 2,
                             win_width,
                             win_height)
                       )
    window.show()  # будем хоть какоето окно видеть, пока запускается
    model_found = window.check_model_dir(model)

    if model_found:
        window.save_model_dir(model.dir_name)
    else:
        # Если нет - предлагаем скачать
        resp = QMessageBox.question(
            window, 'Model not found',
            'Модель для транскрибации не найдена. Скачать?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if resp == QMessageBox.StandardButton.Yes:
            model_zip = model.zip_name

            window.download_widget.show()
            window.download_widget.download(model)

            app_dir = os.path.dirname(os.path.abspath(__file__))
            with zipfile.ZipFile(model_zip, 'r') as zip_ref:
                zip_ref.extractall(app_dir)
            # os.remove(model_zip)
            window.save_model_dir(model.dir_name)
        else:
            # Если отказались - запрашиваем директорию
            model_dir = QFileDialog.getExistingDirectory(window, 'Select Model Directory')
            print(model_dir)
            if model_dir:
                # Сохраняем выбранную директорию
                window.save_model_dir(model_dir)
            print(window.model_dir)

    sys.exit(app.exec())
