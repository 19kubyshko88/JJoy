import os
import re
from urllib.parse import urlparse
from dataclasses import dataclass


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
