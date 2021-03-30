import abc
import collections
import re
from pathlib import Path
from typing import Any, Dict, Iterator, List, Union

import tomlkit
from tomlkit.items import Array, InlineTable


def convert_from(field=None, name=None):
    def wrapper(func):
        func._convert_from = field
        func._convert_to = name
        return func

    return wrapper


class Unset(Exception):
    pass


class _MetaConverterMeta(abc.ABCMeta):
    def __init__(cls, name, bases, ns):
        super().__init__(name, bases, ns)
        cls._converters = {}
        _default = object()
        for key, value in ns.items():
            if getattr(value, "_convert_from", _default) is not _default:
                name = value._convert_to or key
                cls._converters[name] = value


class MetaConverter(collections.abc.Mapping, metaclass=_MetaConverterMeta):
    """Convert a metadata dictionary to PDM's format"""

    def __init__(
        self, source: Dict[str, Any], filename: Union[None, Path, str] = None
    ) -> None:
        self._data = {}
        self.filename = filename
        self.settings = {}
        self._convert(dict(source))

    def __getitem__(self, k: str) -> Any:
        return self._data[k]

    def __len__(self):
        return len(self._data)

    def __iter__(self) -> Iterator:
        return iter(self._data)

    def get_settings(self, source: Dict[str, Any]) -> None:
        pass

    def _convert(self, source: Dict[str, Any]) -> None:
        for key, func in self._converters.items():
            if func._convert_from and func._convert_from not in source:
                continue
            if func._convert_from is None:
                value = source
            else:
                value = source[func._convert_from]
            try:
                self._data[key] = func(self, value)
            except Unset:
                pass

        # Delete all used fields
        for key, func in self._converters.items():
            if func._convert_from is None:
                continue
            try:
                del source[func._convert_from]
            except KeyError:
                pass
        # Add remaining items to the data
        self.get_settings(source)
        self._data.update(source)


NAME_EMAIL_RE = re.compile(r"(?P<name>[^,]+?)\s*<(?P<email>.+)>\s*$")


def make_inline_table(data: Dict[str, str]) -> InlineTable:
    """Create an inline table from the given data."""
    table = tomlkit.inline_table()
    table.update(data)
    return table


def make_array(
    data: Union[List[str], List[InlineTable]], multiline: bool = False
) -> Union[List, Array]:
    if not data:
        return []
    array = tomlkit.array()
    array.multiline(multiline)
    for item in data:
        array.append(item)
    return array


def array_of_inline_tables(
    value: List[Dict[str, str]], multiline: bool = True
) -> Array:
    return make_array([make_inline_table(item) for item in value], multiline)


def parse_name_email(name_email: List[str]) -> Array:
    return array_of_inline_tables(
        [NAME_EMAIL_RE.match(item).groupdict() for item in name_email]
    )
