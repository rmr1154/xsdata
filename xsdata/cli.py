import logging
from pathlib import Path
from typing import Any
from typing import Iterator

import click
import click_log
from pkg_resources import get_distribution

from xsdata.codegen.transformer import SchemaTransformer
from xsdata.codegen.writer import writer
from xsdata.exceptions import CodeGenerationError
from xsdata.logger import logger

outputs = click.Choice(writer.formats)


@click.command("generate")
@click.argument("source", required=True)
@click.option("--package", required=True, help="Target Package")
@click.option("--output", type=outputs, help="Output Format", default="pydata")
@click.option("--wsdl", is_flag=True, default=False, help="WSDL Mode")
@click.option("--print", is_flag=True, default=False, help="Print output")
@click.version_option(get_distribution("xsdata").version)
@click_log.simple_verbosity_option(logger)
def cli(*args: Any, **kwargs: Any):
    """
    Convert schema definitions to code.

    SOURCE can be either a filepath, directory or url
    """
    if kwargs["print"]:
        logger.setLevel(logging.ERROR)

    uris = resolve_source(kwargs["source"], wsdl=kwargs["wsdl"])
    transformer = SchemaTransformer(output=kwargs["output"], print=kwargs["print"])

    if kwargs["wsdl"]:
        transformer.process_definitions(next(uris), kwargs["package"])
    else:
        transformer.process_schemas(list(uris), kwargs["package"])


def resolve_source(source: str, wsdl: bool) -> Iterator[str]:
    path = Path(source).resolve()
    if path.is_dir():

        if wsdl:
            raise CodeGenerationError("WSDL mode doesn't support scanning directories.")

        yield from (x.as_uri() for x in path.glob("*.xsd"))
    elif path.is_file():
        yield path.as_uri()
    else:
        yield source


if __name__ == "__main__":  # pragma: no cover
    cli()
