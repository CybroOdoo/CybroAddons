# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3)
#    (https://www.gnu.org/licenses/lgpl-3.0-standalone.html).
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

"""Response parser for the Vibe Coding Assistant.

Takes the raw string from the AI provider and extracts the JSON envelope
described in spec section 9. Built to be forgiving of common model drift
(stray fences, leading prose, etc.) while still failing fast on garbage.
"""

import json
import re


class ResponseParseError(Exception):
    """Raised when the raw AI response cannot be parsed into the expected shape."""


def parse(raw: str) -> dict:
    """Parse raw AI provider output into the module generation envelope.

    Algorithm (spec §10.1):
    1. Strip whitespace.
    2. Strip markdown code fences if present.
    3. Slice from the first '{' to the last '}' (tolerates stray sentences).
    4. json.loads().
    5. Raise ResponseParseError if the envelope has an "error" key.
    6. Validate top-level shape: must have "module" (dict) and "files" (list).
    7. Return the parsed dict.

    Raises:
        ResponseParseError: with a message that includes up to 200 chars of
            the raw response for debugging. NEVER surface this to end users —
            the caller shows a generic retry message instead.
    """
    text = raw.strip()

    # 2. Remove opening code fence: ```json or ```
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.DOTALL)
    # Remove closing code fence
    text = re.sub(r"\s*```\s*$", "", text, flags=re.DOTALL)
    text = text.strip()

    # 3. Slice to the outermost JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ResponseParseError(
            f"No JSON object found in response. "
            f"First 200 chars: {raw[:200]!r}"
        )
    text = text[start : end + 1]

    # 4. Parse
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ResponseParseError(
            f"JSON parse failed ({exc}). "
            f"First 200 chars: {raw[:200]!r}"
        ) from exc

    # 5. AI-reported error
    if "error" in data:
        raise ResponseParseError(str(data["error"]))

    # 6. Validate shape
    if not isinstance(data.get("module"), dict):
        raise ResponseParseError(
            f"'module' key missing or not a dict. "
            f"First 200 chars: {raw[:200]!r}"
        )
    if not isinstance(data.get("files"), list):
        raise ResponseParseError(
            f"'files' key missing or not a list. "
            f"First 200 chars: {raw[:200]!r}"
        )
    for i, f in enumerate(data["files"]):
        if not isinstance(f, dict) or "path" not in f or "content" not in f:
            raise ResponseParseError(
                f"files[{i}] is missing 'path' or 'content'. "
                f"First 200 chars: {raw[:200]!r}"
            )

    return data
