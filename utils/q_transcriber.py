import json
import docx
import shlex
import subprocess
import os
import logging
from vosk import KaldiRecognizer, Model
from queue import Queue
from timeit import default_timer as timer
from multiprocessing.dummy import Pool


CHUNK_SIZE = 4000
SAMPLE_RATE = 16000.0


class QTranscriber:
    """
    This class transcribes audio files using the Vosk speech recognition library with multiprocessing.
    It defines methods to recognize a stream, resample audio using ffmpeg, process a task list in a
    multiprocessing pool, and save the transcription as a .docx file. It also initializes the ffmpeg path and the
    PATH environment variable to include the ffmpeg path if it's not already present.
    """
    # Define the path to ffmpeg
    ffmpeg_path = r'C:\ffmpeg\bin'

    # Get the current value of the PATH environment variable
    current_path = os.environ['PATH']
    # Check if the path already exists in the PATH variable
    if ffmpeg_path not in current_path:
        # If not, add the path to the PATH variable
        os.environ['PATH'] += os.pathsep + ffmpeg_path

    def __init__(self, args):
        super().__init__()
        self.model = Model(model_path=args.model)
        self.args = args
        self.queue = Queue()

    @staticmethod
    def recognize_stream(rec, stream):
        tot_samples = 0
        result = []

        while True:
            data = stream.stdout.read(CHUNK_SIZE)

            if len(data) == 0:
                break

            tot_samples += len(data)
            rec.AcceptWaveform(data)
            # if rec.AcceptWaveform(data):
            #     jres = json.loads(rec.Result())
            #     logging.info(jres)
            #     result.append(jres)
            # else:
            #     jres = json.loads(rec.PartialResult())
            #     if jres["partial"] != "":
            #         logging.info(jres)

        jres = json.loads(rec.FinalResult())
        result.append(jres)
        return result, tot_samples

    def save_as_docx(self, file_name, result):
        text = result[0]['text']
        if file_name:
            doc = docx.Document()
            doc.add_paragraph(text)
            doc.save(file_name)

    @staticmethod
    def resample_ffmpeg(infile):
        cmd = shlex.split(f"ffmpeg -nostdin -loglevel quiet -i \'{str(infile)}\' "
                          f"-ar {SAMPLE_RATE} -ac 1 -f s16le -"
                          )
        stream = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        return stream

    def pool_worker(self, inputdata):
        logging.info("Recognizing {}".format(inputdata[0]))
        start_time = timer()

        try:
            stream = self.resample_ffmpeg(inputdata[0])
        except FileNotFoundError as e:
            print(e, "Missing FFMPEG, please install and try again")
            return
        except Exception as e:
            logging.info(e)
            return

        rec = KaldiRecognizer(self.model, SAMPLE_RATE)
        rec.SetWords(True)
        result, tot_samples = self.recognize_stream(rec, stream)
        if tot_samples == 0:
            return
        self.save_as_docx(inputdata[1], result)
        # processed_result = self.format_result(result)
        # if inputdata[1] != "":
        #     logging.info("File {} processing complete".format(inputdata[1]))
        #     with open(inputdata[1], "w", encoding="utf-8") as fh:
        #         fh.write(processed_result)
        # else:
        #     print(processed_result)

        elapsed = timer() - start_time
        logging.info(f"Execution time: {elapsed:.3f} sec; xRT {(float(elapsed) * (2 * SAMPLE_RATE) / tot_samples):.3f}")

    def process_task_list_pool(self, task_list):
        with Pool() as pool:
            pool.map(self.pool_worker, task_list)
