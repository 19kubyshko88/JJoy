import argparse
import docx
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QDialog


def save_as_docx(file_name, result):
    text = result[0]['text']
    if file_name:
        doc = docx.Document()
        doc.add_paragraph(text)
        doc.save(file_name)


def show_interactive_text(root, text):
    """
    Create an interactive text label within a given root widget.

    Args:
        root: The root widget to place the interactive text label.
        text: The text to be displayed in the interactive label.

    Returns:
        None
    """
    label = QLabel(root)
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)  # Allow hyperlink interaction
    label.setOpenExternalLinks(True)  # Open the hyperlink in a web browser

    label.setText(text)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Optional: Center align the text

    layout = QVBoxLayout()
    layout.addWidget(label)

    dialog = QDialog(root)
    dialog.setLayout(layout)
    dialog.exec()


def parse_arguments():
    """
       Parse command line arguments and return the parser object.
    """
    parser = argparse.ArgumentParser(
        description="Transcribe audio file and save result in selected format")
    parser.add_argument(
        "--model", "-m", type=str,
        help="model path")
    parser.add_argument(
        "--server", "-s", type=str,
        help="use server for recognition. For example ws://localhost:2700")
    parser.add_argument(
        "--list-models", default=False, action="store_true",
        help="list available models")
    parser.add_argument(
        "--list-languages", default=False, action="store_true",
        help="list available languages")
    parser.add_argument(
        "--model-name", "-n", type=str,
        help="select model by name")
    parser.add_argument(
        "--lang", "-l", default="en-us", type=str,
        help="select model by language")
    parser.add_argument(
        "--input", "-i", type=str,
        help="audiofile")
    parser.add_argument(
        "--output", "-o", default="", type=str,
        help="optional output filename path")
    # parser.add_argument(
    #     "--output-type", "-t", default="txt", type=str,
    #     help="optional arg output data type")
    parser.add_argument(
        "--output-type", "-t", default="docx", type=str,
        help="optional arg output data type")
    parser.add_argument(
        "--tasks", "-ts", default=10, type=int,
        help="number of parallel recognition tasks")
    parser.add_argument(
        "--log-level", default="INFO",
        help="logging level")
    return parser