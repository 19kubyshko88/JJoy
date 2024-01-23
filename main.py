import sys
import subprocess
import json
import vosk
import docx
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (QApplication, QFileDialog, QMainWindow, QPushButton,
                             QTextEdit, QVBoxLayout, QWidget, QProgressBar)
import g4f
import textwrap

g4f.debug.logging = True # enable logging
g4f.debug.version_check = False # Disable automatic version checking


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()
        self.result = ''

    def init_ui(self):
        # Create UI elements
        self.button = QPushButton('Transcribe Audio', self)
        self.button.clicked.connect(self.transcribe_audio)

        self.button_ai = QPushButton('AI', self)
        self.button_ai.clicked.connect(self.ai_text_editing)

        self.text_edit = QTextEdit(self)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFont(QFont('Arial', 7))
        # self.progress_bar.setStyleSheet(
        #     "QProgressBar {font-size: 5px, height: 5px; border: 1px solid #333; border-radius: 5px; text-align: center;}")

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
        self.progress_bar.setRange(0, len(batches))
        for i, batch in enumerate(batches):
            response = ''
            try:
                response = g4f.ChatCompletion.create(
                    model= g4f.models.gpt_4,

                    messages=[{"role": """text editor""",
                               "content": f"Ты получишь транскрибацию аудио файла. Нужно переделать её в удобный для чтения вид: "
                                          f"Поставить знаки препинания, исправить грамматику, прямую, косвенную речь. "
                                          f"Старайся как можно меньше изменять смысл текста. СВОИ КОММЕНТАРИИИ НЕ ПИШИ!!! ОЦЕНОЧНЫХ СУЖДЕНИЙ НЕ ВЫСКАЗЫВАЙ!"
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
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open Audio File', '', 'Audio Files (*.mp3 *.wav)')
        if file_name:
            self.model = vosk.Model('vosk-model-ru-0.42')
            rec = vosk.KaldiRecognizer(self.model, 16000)
            with subprocess.Popen(["ffmpeg", "-loglevel", "quiet", "-i",
                                   file_name,
                                   "-ar", str(16000), "-ac", "1", "-f", "s16le", "-"],
                                  stdout=subprocess.PIPE) as process:
                while True:
                    data = process.stdout.read(4000)
                    if len(data) == 0:
                        break
                    rec.AcceptWaveform(data)

                self.result: str = json.loads(rec.FinalResult())['text']   # запятые в числах мешают преобразовать в json
                # result = result.split('"text"')[1]
                print(self.result, type(self.result))
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
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())