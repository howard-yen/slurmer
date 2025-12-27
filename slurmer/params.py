#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
import glob
import itertools
import os
from typing import Dict, List, Optional, Tuple
from collections.abc import Iterable

ParameterValue = str | int | float | bool | None


@dataclass
class SpecialParameter:
    glob: str | None = None
    root_dir: str | None = None

    range: List[int] | None = None

    groups: Dict[str, List[str | int | float]] | None = None

    def __iter__(self) -> Iterable[str | int | float]:
        if self.glob:
            files = sorted(glob.glob(
                os.path.expanduser(self.glob),
                root_dir=(
                    os.path.expanduser(self.root_dir) if self.root_dir else None
                )
            ))
           # if not files:
           #     raise FileNotFoundError(f"No match for glob '{self.glob}'")
            yield from files
        elif self.range:
            yield from list(range(*self.range))
        
        elif self.groups:
            # each value is in the form of {group_name: value} for all values in the list
            yield from [dict(zip(self.groups.keys(), v)) for v in zip(*self.groups.values())]


ParameterDict = Dict[str, ParameterValue]
Parameters = Dict[str, ParameterValue | SpecialParameter | List[ParameterValue]]


def split_variables_and_arguments(param_dict: ParameterDict) -> Tuple[ParameterDict, ParameterDict]:
    """Split parameters into variables and arguments."""
    variables, arguments = {}, {}
    for key, value in param_dict.items():
        if key.startswith('$') or key.startswith('-'):
            arguments[key] = value
        else:
            variables[key] = value
    return variables, arguments


def format_parameter(param: ParameterValue) -> str:
    if isinstance(param, bool):
        # More canonical in bash to use "true" or "false" rather than "True" or "False"
        # Maybe make this configurable in the future
        return str(param).lower() 
    elif param is None:
        # More canonical in bash to use "null" rather than "None" or "none"
        return "null"
    else:
        return f"{param}"


def flatten_parameters(params: Parameters | List[Parameters]) -> List[Parameters]:
    if isinstance(params, dict):
        return list(iter(SpecialParameter(**params)))
    elif isinstance(params, list):
        return sum((flatten_parameters(p) for p in params), [])
    else:
        return [params]


def normalize_parameters(params: Parameters | List[Parameters]) -> Iterable[ParameterDict]:
    """Normalize parameters into a list of simple dictionaries with all combinations."""
    if isinstance(params, dict):
        params = [params]

    for param_set in params:
        # First, process any special parameters
        grid_params = {}
        for key, value in param_set.items():
            grid_params[key] = flatten_parameters(value)

        # Generate all combinations of grid parameters
        keys = list(grid_params.keys())
        values = [grid_params[k] for k in keys]
        for combination in itertools.product(*values):
            # flatten the grouped parameters into the combination
            combo = dict(zip(keys, combination))
            for k in keys:
                if k.lower().startswith("group"):
                    v = combo.pop(k)
                    combo.update(v)
                    
            yield combo
