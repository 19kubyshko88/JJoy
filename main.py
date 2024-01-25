import sys
import os
import json
import zipfile
import subprocess
import vosk
import docx
import g4f
import textwrap

from PyQt6.QtCore import QSettings, QProcess, QDir
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (QApplication, QFileDialog, QMainWindow, QPushButton,
                             QTextEdit, QVBoxLayout, QWidget, QProgressBar, QMessageBox)

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

        model_dir = os.path.join(app_dir, model.dir_name) #'vosk-model-ru-0. 42')
        print(model_dir)
        if os.path.exists(model_dir):
            return True
        return False

    def select_model_folder(self):
        folder_name = QFileDialog.getExistingDirectory(self, 'Select Model Folder', '')
        if folder_name:
            self.model_dir = folder_name
            self.save_model_dir(self.model_dir)

    def save_model_dir(self, model_dir):
        # Сохраняем путь в настройках приложения
        settings = QSettings('JJoy', 'AppSettings')
        settings.setValue('model_dir', model_dir)
        self.model_dir = model_dir

    def init_ui(self):
        # Create UI elements
        self.button = QPushButton('Transcribe Audio', self)
        self.button.clicked.connect(self.transcribe_audio)

        self.button_ai = QPushButton('AI', self)
        self.button_ai.clicked.connect(self.ai_text_editing)

        self.text_edit = QTextEdit(self)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFont(QFont('Arial', 7))

        # Set layout
        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.button_ai)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.progress_bar)

        # Create a central widget and set the layout
        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Set window title
        self.setWindowTitle('Audio to Text Converter')

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
                    model= g4f.models.gpt_4,

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
        self.text_edit.setPlainText(ai_response)

    def transcribe_audio(self):
        # current_path = os.path.dirname(os.path.abspath(__file__))

        default_directory = QDir.rootPath()

        # Использование метода getOpenFileNameAndFilter() для создания диалогового окна
        file_name, _ = QFileDialog.getOpenFileName(
            parent=None,
            caption='Open Audio File',
            directory=default_directory,
            filter='Audio Files (*.mp3 *.wav)'
        )
        # file_name, _ = QFileDialog.getOpenFileName(self, 'Open Audio File', '', 'Audio Files (*.mp3 *.wav)')
                                                   # directory=str(os.path.dirname(os.path.abspath(__file__))))
        if file_name:
            self.model = vosk.Model(self.model_dir)  # 'vosk-model-ru-0.42'
            rec = vosk.KaldiRecognizer(self.model, 16000)

            number_of_iterations = os.path.getsize(file_name)//4000
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
                    rec.AcceptWaveform(data)

                self.result: str = json.loads(rec.FinalResult())['text']  # запятые в числах мешают преобразовать в json
                print(self.result)
                # Display the recognized text
                self.text_edit.setPlainText(self.result.strip())

                # Save the result as a docx file
                self.save_as_docx()

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

    window = MainWindow()

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

            process = QProcess()

            # Путь к второму приложению
            program_path = "downloading_app.py"
            # Запускаем второе приложение
            file_path = os.path.join(os.path.dirname(__file__), program_path)
            print(file_path)
            # Запускаем второе приложение с передачей параметра
            subprocess.run(["python3", file_path, model.model_name])

            app_dir = os.path.dirname(os.path.abspath(__file__))
            with zipfile.ZipFile(model_zip, 'r') as zip_ref:
                zip_ref.extractall(app_dir)
            os.remove(model_zip)
            window.save_model_dir(model.dir_name)
        else:
            # Если отказались - запрашиваем директорию
            model_dir = QFileDialog.getExistingDirectory(window, 'Select Model Directory')
            print(model_dir)
            if model_dir:
                # Сохраняем выбранную директорию
                window.save_model_dir(model_dir)
            print(window.model_dir)

    window.show()
    sys.exit(app.exec())
