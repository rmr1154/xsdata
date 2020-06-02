from dataclasses import dataclass
from typing import Optional

from xsdata.models.enums import BindingStyle
from xsdata.models.enums import UseChoice
from xsdata.models.mixins import attribute


@dataclass
class SoapOperation:
    """
    :param action:
    :param style:
    :param transport: soap 1.1 only
    :param action_required:  soap 1.2 only
    """

    action: Optional[str] = attribute(name="soapAction")
    style: Optional[str] = attribute(default=BindingStyle.DOCUMENT)
    transport: Optional[str] = attribute()
    action_required: bool = attribute(name="soapActionRequired", default=True)


@dataclass
class SoapBody:
    """
    :param use:
    :param parts:
    :param namespace:
    :param encoding_style:
    """

    use: Optional[UseChoice] = attribute(default=UseChoice.LITERAL)
    parts: Optional[str] = attribute()
    namespace: Optional[str] = attribute()
    encoding_style: Optional[str] = attribute(name="encodingStyle")


@dataclass
class SoapHeader:
    """
    :param use:
    :param part:
    :param message:
    :param namespace:
    :param encoding_style:
    """

    use: Optional[UseChoice] = attribute(default=UseChoice.LITERAL)
    part: Optional[str] = attribute()
    message: Optional[str] = attribute()
    namespace: Optional[str] = attribute()
    encoding_style: Optional[str] = attribute(name="encodingStyle")


@dataclass
class SoapFault:
    """
    :param use:
    :param name:
    :param namespace:
    :param encoding_style:
    """

    use: Optional[UseChoice] = attribute(default=UseChoice.LITERAL)
    name: Optional[str] = attribute()
    namespace: Optional[str] = attribute()
    encoding_style: Optional[str] = attribute(name="encodingStyle")


@dataclass
class SoapHeaderFault:
    """
    :param use:
    :param name:
    :param part:
    :param namespace:
    :param encoding_style:
    """

    use: Optional[UseChoice] = attribute(default=UseChoice.LITERAL)
    name: Optional[str] = attribute()
    part: Optional[str] = attribute()
    namespace: Optional[str] = attribute()
    encoding_style: Optional[str] = attribute(name="encodingStyle")


@dataclass
class SoapBinding:
    """
    :param style:
    :param transport:
    """

    style: Optional[BindingStyle] = attribute(default=BindingStyle.DOCUMENT)
    transport: Optional[str] = attribute()


@dataclass
class SoapAddress:
    """
    :param location:
    """

    location: Optional[str] = attribute()
