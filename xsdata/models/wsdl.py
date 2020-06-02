from dataclasses import dataclass
from typing import List
from typing import Optional

from xsdata.models.enums import Namespace
from xsdata.models.mixins import array_any_element
from xsdata.models.mixins import array_element
from xsdata.models.mixins import attribute
from xsdata.models.mixins import element
from xsdata.models.xsd import Schema


@dataclass
class Documentation:
    """
    :params elements:
    """

    elements: List[object] = array_any_element()


@dataclass
class WsdlElement:
    """
    :param name:
    :param documentation:
    """

    name: Optional[str] = attribute()
    documentation: Optional[Documentation] = element()


@dataclass
class Types:
    """
    :param schemas:
    :param documentation:
    """

    schemas: List[Schema] = array_element(name="schema", namespace=Namespace.XS.uri)
    documentation: Optional[Documentation] = element()


@dataclass
class Import:
    """
    :param location:
    :param namespace:
    """

    location: Optional[str] = attribute()
    namespace: Optional[str] = attribute()


@dataclass
class Message(WsdlElement):
    """
    :param part:
    """

    part: List["Message.Part"] = array_element()

    class Part:
        """
        :param name:
        :param type:
        :param element:
        """

        name: Optional[str] = attribute()
        type: Optional[str] = attribute()
        element: Optional[str] = element()


@dataclass
class PortTypeMessage(WsdlElement):
    """
    :param message:
    """

    message: Optional[str] = attribute()


@dataclass
class PortTypeOperation(WsdlElement):
    """
    :param input:
    :param output:
    :param faults:
    """

    input: Optional[PortTypeMessage] = element()
    output: Optional[PortTypeMessage] = element()
    faults: List[PortTypeMessage] = array_element(name="fault")


@dataclass
class PortType(WsdlElement):
    """
    :param operations:
    """

    operations: List[PortTypeOperation] = array_element()
    extensible_elements: List[object] = array_any_element()


@dataclass
class BindingMessage(WsdlElement):
    """
    :param extensible_elements:
    """

    extensible_elements: List[object] = array_any_element()


@dataclass
class Input(BindingMessage):
    pass


@dataclass
class Output(BindingMessage):
    pass


@dataclass
class Fault(BindingMessage):
    pass


@dataclass
class BindingOperation(WsdlElement):
    """
    :param input:
    :param output:
    :param faults:
    :param extensible_elements:
    """

    input: Optional[Input] = element()
    output: Optional[Output] = element()
    faults: List[Fault] = array_element(name="fault")
    extensible_elements: List[object] = array_any_element()


@dataclass
class Binding(WsdlElement):
    """
    :param type:
    :param operations:
    :param extensible_elements:
    """

    type: Optional[str] = attribute()
    operations: List[BindingOperation] = array_element(name="operation")
    extensible_elements: List[object] = array_any_element()


@dataclass
class ServicePort(WsdlElement):
    """
    :param binding:
    :param extensible_elements:
    """

    binding: Optional[str] = attribute()
    extensible_elements: List[object] = array_any_element()


@dataclass
class Service(WsdlElement):
    """
    :param ports:
    """

    ports: List[ServicePort] = array_element(name="port")


@dataclass
class Definitions(WsdlElement):
    """
    :param types:
    :param imports:
    :param messages:
    :param port_types:
    :param bindings:
    :param services:
    :param extensible_elements:
    """

    class Meta:
        name = "definitions"
        namespace = "http://schemas.xmlsoap.org/wsdl/"

    target_namespace: Optional[str] = attribute(name="targetNamespace")

    types: Types = element()
    imports: List[Import] = array_element(name="import")
    messages: List[Message] = array_element(name="message")
    port_types: List[PortType] = array_element(name="portType")
    bindings: List[Binding] = array_element(name="binding")
    services: List[Service] = array_element(name="service")
    extensible_elements: List[object] = array_any_element()
