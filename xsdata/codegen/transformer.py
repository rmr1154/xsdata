import os
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union
from urllib.parse import urlparse
from urllib.request import urlopen

from xsdata.codegen.analyzer import ClassAnalyzer
from xsdata.codegen.builder import ClassBuilder
from xsdata.codegen.models import Class
from xsdata.codegen.parser import DefinitionsParser
from xsdata.codegen.parser import SchemaParser
from xsdata.codegen.writer import writer
from xsdata.logger import logger
from xsdata.models.enums import COMMON_SCHEMA_DIR
from xsdata.models.wsdl import Definitions
from xsdata.models.xsd import Import
from xsdata.models.xsd import Include
from xsdata.models.xsd import Override
from xsdata.models.xsd import Redefine
from xsdata.models.xsd import Schema
from xsdata.utils import collections

Included = Union[Import, Include, Redefine, Override]


@dataclass
class SchemaTransformer:
    """
    Orchestrate the code generation from a list of sources to the output
    format.

    :param print: Print to stdout the generated output.
    :param output: The output type.
    :param class_map: The classes generated indexed by the source uri.
    :param processed: Index of the already processed uris.
    """

    print: bool
    output: str
    class_map: Dict[str, List[Class]] = field(init=False, default_factory=dict)
    processed: List[str] = field(init=False, default_factory=list)

    def process_definitions(self, uri: str, package: str):

        definitions = self.parse_definitions(uri)

        if definitions is None:
            raise Exception("Failed")

        if definitions.types:
            collections.apply(definitions.types.schemas, self.convert_schema)

        self.process_classes(package)

    def process_schemas(self, uris: List[str], package: str):
        """
        Run main processes.

        :param uris: list of uris to process
        :param package: package name eg foo.bar.xxx
        """

        collections.apply(uris, self.process_schema)

        self.process_classes(package)

    def process_classes(self, package: str):
        classes = [cls for classes in self.class_map.values() for cls in classes]
        class_num, inner_num = self.count_classes(classes)
        if class_num:
            logger.info(
                "Analyzer input: %d main and %d inner classes", class_num, inner_num
            )
            self.assign_packages(package)

            classes = self.analyze_classes(classes)
            class_num, inner_num = self.count_classes(classes)
            logger.info(
                "Analyzer output: %d main and %d inner classes", class_num, inner_num
            )

            writer.designate(classes, self.output)
            if self.print:
                writer.print(classes, self.output)
            else:
                writer.write(classes, self.output)
        else:
            logger.warning("Analyzer returned zero classes!")

    def process_schema(self, uri: str, namespace: Optional[str] = None):
        """
        Parse and convert schema to codegen models.

        Avoid processing the same uri twice and fail silently if
        anything goes wrong with fetching and parsing the schema
        document.
        """
        if uri in self.processed:
            logger.debug("Already processed skipping: %s", uri)
        else:
            logger.info("Parsing schema %s", os.path.basename(uri))
            self.processed.append(uri)

            schema = self.parse_schema(uri, namespace)
            if schema:
                self.convert_schema(schema)

    def convert_schema(self, schema: Schema):
        """Convert schema instance to codegen classes and process imports to
        other schemas."""
        for sub in schema.included():
            if sub.location:
                self.process_schema(sub.location, schema.target_namespace)

        assert schema.location is not None

        self.class_map[schema.location] = self.generate_classes(schema)

    def generate_classes(self, schema: Schema) -> List[Class]:
        """Convert and return the given schema tree to classes."""
        uri = schema.location
        logger.info("Compiling schema %s", "..." if not uri else os.path.basename(uri))
        classes = ClassBuilder(schema=schema).build()

        class_num, inner_num = self.count_classes(classes)
        if class_num > 0:
            logger.info("Builder: %d main and %d inner classes", class_num, inner_num)

        return classes

    @staticmethod
    def parse_schema(uri: str, namespace: Optional[str] = None) -> Optional[Schema]:
        """
        Parse the given schema uri and return the schema tree object.

        Optionally add the target namespace if the schema is included
        and is missing a target namespace.
        """

        try:
            input_stream = urlopen(uri).read()
        except OSError:
            logger.warning("Schema not found %s", uri)
        else:
            parser = SchemaParser(target_namespace=namespace, location=uri)
            return parser.from_bytes(input_stream, Schema)

        return None

    @classmethod
    def parse_definitions(
        cls, uri: str, namespace: Optional[str] = None
    ) -> Optional[Definitions]:
        """
        Parse the given schema uri and return the schema tree object.

        Optionally add the target namespace if the schema is included
        and is missing a target namespace.
        """

        try:
            input_stream = urlopen(uri).read()
        except OSError:
            logger.warning("Definitions not found %s", uri)
        else:
            parser = DefinitionsParser(target_namespace=namespace, location=uri)
            definitions = parser.from_bytes(input_stream, Definitions)

            for imp in definitions.imports:
                if not imp.location:
                    continue

                res = cls.parse_definitions(imp.location, definitions.target_namespace)

                if not res:
                    continue

                if res.types:

                    if not definitions.types:
                        definitions.types = res.types
                    else:
                        definitions.types.schemas.extend(res.types.schemas)
                definitions.messages.extend(res.messages)
                definitions.port_types.extend(res.port_types)
                definitions.bindings.extend(res.bindings)
                definitions.services.extend(res.services)
                definitions.extensible_elements.extend(res.extensible_elements)

        return definitions

    @staticmethod
    def analyze_classes(classes: List[Class]) -> List[Class]:
        """Analyzer the given class list and simplify attributes and
        extensions."""
        return ClassAnalyzer.from_classes(classes).process()

    def count_classes(self, classes: List[Class]) -> Tuple[int, int]:
        """Return a tuple of counters for the main and inner classes."""
        main = len(classes)
        inner = 0
        for cls in classes:
            inner += sum(self.count_classes(cls.inner))

        return main, inner

    def assign_packages(self, package: str):
        """Group uris by common path and auto assign package names to all
        classes."""
        prev = ""
        index = 0
        groups = defaultdict(list)
        common_schemas_dir = COMMON_SCHEMA_DIR.as_uri()
        for key in sorted(self.class_map.keys()):
            if key.startswith(common_schemas_dir):
                groups[0].append(key)
            else:
                key_parsed = urlparse(key)
                common_path = os.path.commonpath((prev, key))
                if not common_path or common_path == key_parsed.scheme:
                    index += 1

                prev = key
                groups[index].append(key)

        for keys in groups.values():
            common_path = (
                os.path.dirname(keys[0]) if len(keys) == 1 else os.path.commonpath(keys)
            )
            for key in keys:
                items = self.class_map[key]
                suffix = ".".join(Path(key).parent.relative_to(common_path).parts)
                package_name = f"{package}.{suffix}" if suffix else package
                self.assign_package(items, package_name)

    @classmethod
    def assign_package(cls, classes: List[Class], package: str):
        """Assign the given package to all the classes and their inners."""
        for obj in classes:
            obj.package = package
            cls.assign_package(obj.inner, package)
