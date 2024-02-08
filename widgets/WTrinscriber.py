import argparse
import logging
import sys
import os
from pathlib import Path

import requests
from vosk import list_models, list_languages
from utils.vosk_transcriber import Transcriber
from PyQt6.QtWidgets import QWidget


MODEL_PRE_URL = "https://alphacephei.com/vosk/models/"
MODEL_LIST_URL = MODEL_PRE_URL + "model-list.json"
MODEL_DIRS = [os.getenv("VOSK_MODEL_PATH"), Path("/usr/share/vosk"),
        Path.home() / "AppData/Local/vosk", Path.home() / ".cache/vosk"]


class AudioTranscriber(QWidget):
    @staticmethod
    def init_standard_params():
        parser = argparse.ArgumentParser(description="Transcribe audio file and save result in selected format")
        parser.add_argument("--model", "-m", type=str, help="model path")
        parser.add_argument("--server", "-s", type=str,
                            help="use server for recognition. For example ws://localhost:2700")
        parser.add_argument("--list-models", default=False, action="store_true", help="list available models")
        parser.add_argument("--list-languages", default=False, action="store_true", help="list available languages")
        parser.add_argument("--model-name", "-n", type=str, help="select model by name")
        parser.add_argument("--lang", "-l", default="en-us", type=str, help="select model by language")
        parser.add_argument("--input", "-i", type=str, help="audiofile")
        parser.add_argument("--output", "-o", default="", type=str, help="optional output filename path")
        parser.add_argument("--output-type", "-t", default="txt", type=str, help="optional arg output data type")
        parser.add_argument("--tasks", "-ts", default=10, type=int, help="number of parallel recognition tasks")
        parser.add_argument("--log-level", default="INFO", help="logging level")
        return parser

    @staticmethod
    def get_models_names():
        response = requests.get(MODEL_LIST_URL, timeout=10)
        return [model["name"] for model in response.json()]

    @staticmethod
    def get_languages():
        response = requests.get(MODEL_LIST_URL, timeout=10)
        return {m["lang"] for m in response.json()}

    def __init__(self, model_path):
        super().__init__()
        self.parser = self.init_standard_params()
        self.args, self.unknown = self.parser.parse_known_args()
        self.args.model = model_path

    def transcribe(self, path_to_audio, output, log_level='INFO'):
        self.args.input = path_to_audio
        self.args.output = output

        logging.getLogger().setLevel(log_level)

        if not Path(self.args.input).exists():
            logging.info(f"File/folder {self.args.input} does not exist, " \
                          "please specify an existing file/directory")
            sys.exit(1)

        transcriber = Transcriber(self.args)

        if Path(self.args.input).is_dir():
            task_list = [(Path(self.args.input, fn),
                          Path(self.args.output,
                               Path(fn).stem).with_suffix(f".{self.args.output_type}"))
                         for fn in os.listdir(self.args.input)
                         ]
        elif Path(self.args.input).is_file():
            if self.args.output == "":
                task_list = [(Path(self.args.input), self.args.output)]
            else:
                task_list = [(Path(self.args.input), Path(self.args.output))]
        else:
            logging.info("Wrong arguments")
            sys.exit(1)

        transcriber.process_task_list_pool(task_list)


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow
    from settings import model

    app_path = Path(__file__).resolve()
    two_up_path = app_path.parents[1]

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.show()

    transcriber = AudioTranscriber(model.path_to_model)
    transcriber.transcribe(fr"{two_up_path}\audio", fr"{two_up_path}\output")

    sys.exit(app.exec())
