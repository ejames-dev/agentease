from __future__ import annotations

import json
from typing import TypeVar

from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)


def enforce_json_schema(payload: str | dict, schema: type[SchemaT]) -> SchemaT:
    """Parse and validate an LLM payload with a strict Pydantic schema."""

    data = json.loads(payload) if isinstance(payload, str) else payload
    return schema.model_validate(data)
