from PyQt6.QtCore import QThread
import vosk


class ModelInitThread(QThread):
    def __init__(self, model_dir):
        super().__init__()
        self.model_dir = model_dir

    def run(self):
        """
        :param model_dir: путь до папки с моделью
        :return:
        """
        self.model = vosk.Model(self.model_dir)  # 'vosk-model-ru-0.42'
        self.rec = vosk.KaldiRecognizer(self.model, 16000)