from dataclasses import MISSING, dataclass, field, fields, is_dataclass
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Optional,
    Set,
    Type,
    get_type_hints,
)

from xsdata.models.enums import TagType


@dataclass(frozen=True)
class Field:
    name: str
    local_name: str
    type: Any
    is_list: bool = False
    is_attribute: bool = False
    is_dataclass: bool = False
    default: Any = None
    namespace: Optional[str] = None


@dataclass(frozen=True)
class Meta:
    name: str
    namespace: Optional[str]


@dataclass
class ModelInspect:
    cache: Dict = field(init=False, default_factory=dict)
    ns_cache: Dict = field(init=False, default_factory=dict)

    def fields(self, clazz: Type) -> List[Field]:
        if not self.is_dataclass(clazz):
            raise TypeError(f"Object {clazz} is not a dataclass")

        if clazz not in self.cache:
            self.cache[clazz] = list(self.get_type_hints(clazz))
        return self.cache[clazz]

    def namespaces(self, clazz: Type) -> List[str]:
        if not self.is_dataclass(clazz):
            raise TypeError(f"Object {clazz} is not a dataclass")

        if clazz not in self.ns_cache:
            self.ns_cache[clazz] = list(self.get_unique_namespaces(clazz))
        return self.ns_cache[clazz]

    def get_unique_namespaces(self, clazz) -> Set[str]:
        namespaces = set()
        if self.is_dataclass(clazz):
            meta = self.class_meta(clazz)
            if meta.namespace:
                namespaces.add(meta.namespace)

            for f in self.fields(clazz):
                if f.namespace:
                    namespaces.add(f.namespace)
                if f.is_dataclass:
                    namespaces.update(self.namespaces(f.type))

        return namespaces

    def get_type_hints(self, clazz) -> Iterator[Field]:
        type_hints = get_type_hints(clazz)

        for f in fields(clazz):
            tp = type_hints[f.name]
            is_list = False

            if hasattr(tp, "__origin__"):
                is_list = tp.__origin__ is list
                tp = tp.__args__[0]

            default_value = None
            if f.default_factory is not MISSING:  # type: ignore
                default_value = f.default_factory  # type: ignore
            elif f.default is not MISSING:
                default_value = f.default

            namespace = (
                f.metadata.get("namespace") or self.class_meta(tp).namespace
            )

            yield Field(
                name=f.name,
                local_name=f.metadata["name"],
                is_attribute=f.metadata["type"] == TagType.ATTRIBUTE.cname,
                is_list=is_list,
                is_dataclass=self.is_dataclass(tp),
                type=tp,
                default=default_value,
                namespace=namespace,
            )

    @staticmethod
    def class_meta(clazz: Type) -> Meta:
        meta = getattr(clazz, "Meta", None)
        return Meta(
            name=getattr(meta, "name", clazz.__name__),
            namespace=getattr(meta, "namespace", None),
        )

    @staticmethod
    def is_dataclass(obj: object):
        return is_dataclass(obj)