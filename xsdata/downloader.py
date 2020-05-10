from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import List
from typing import Optional
from typing import Union
from urllib.request import urlopen

from xsdata.logger import logger
from xsdata.models.elements import Import
from xsdata.models.elements import Include
from xsdata.models.elements import Override
from xsdata.models.elements import Redefine
from xsdata.models.elements import Schema
from xsdata.parser import SchemaParser

SubSchema = Union[Import, Include, Redefine, Override]


@dataclass
class SchemaDownloader:
    processed: List[str] = field(init=False, default_factory=list)

    def process(self, urls: List[str], package: str):
        destination = Path.cwd().joinpath(*package.split("."))
        for url in urls:
            self.process_schema(url, destination)

    def process_schema(self, url: str, destination: Path):
        """Recursively parse the given schema url and the included schemas and
        download all resources."""
        if url in self.processed:
            return

        self.processed.append(url)
        schema = self.parse_schema(url, destination)
        if not schema:
            return

        for sub in schema.included():
            if (
                not sub.location
                or sub.location in self.processed
                or not sub.schema_location
            ):
                continue

            self.process_schema(
                sub.location, destination.joinpath(sub.schema_location).parent
            )

    @staticmethod
    def parse_schema(url: str, destination: Path) -> Optional[Schema]:
        """
        Parse the given schema url and return the schema tree object.

        Optionally add the target namespace if the schema is included
        and is missing a target namespace.
        """

        try:
            schema = urlopen(url).read()
            file_name = Path(url).name
            destination.mkdir(parents=True, exist_ok=True)
            destination.joinpath(file_name).write_bytes(schema)
        except OSError:
            logger.warning("Schema not found %s", url)
        else:
            parser = SchemaParser(schema_location=url)
            return parser.from_bytes(schema, Schema)

        return None
