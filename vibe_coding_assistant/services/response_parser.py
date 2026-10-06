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
described in spec section 9. Built to be resilient against LLM syntax drifts
(unescaped quotes in code, stray fences, control characters, truncated JSON).
"""

import json
import logging
import re

_logger = logging.getLogger(__name__)


class ResponseParseError(Exception):
    """Raised when the raw AI response cannot be parsed into the expected shape."""


def parse(raw: str) -> dict:
    """Parse raw AI provider output into the module generation envelope.

    Multi-pass strategy:
    1. Strip code fences & slice to outermost JSON object bounds.
    2. Try strict json.loads().
    3. Try non-strict json.loads(strict=False).
    4. Clean trailing commas & fix unescaped backslashes, then try json.loads().
    5. Fallback regex extractor for files if unescaped inner quotes broke JSON parsing.
    """
    if not raw or not raw.strip():
        raise ResponseParseError("Empty response received from AI model.")

    text = raw.strip()

    # Remove markdown code fences: ```json ... ``` or ``` ... ```
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.DOTALL)
    text = re.sub(r"\s*```\s*$", "", text, flags=re.DOTALL)
    text = text.strip()

    # Slice to the outermost JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ResponseParseError(
            f"No JSON object found in response. First 200 chars: {raw[:200]!r}"
        )
    sliced_text = text[start : end + 1]

    # Pass 1: Strict JSON parse
    try:
        data = json.loads(sliced_text)
        return _validate_and_return(data, raw)
    except Exception:
        pass

    # Pass 2: Non-strict JSON parse (permits unescaped control chars like \n in strings)
    try:
        data = json.loads(sliced_text, strict=False)
        return _validate_and_return(data, raw)
    except Exception:
        pass

    # Pass 3: Clean trailing commas & backslashes, then parse
    cleaned_text = re.sub(r',\s*([\]}])', r'\1', sliced_text)
    fixed_escapes = re.sub(r'(?<!\\)\\(?![\\"/bfnrtu])', r'\\\\', cleaned_text)
    try:
        data = json.loads(fixed_escapes, strict=False)
        return _validate_and_return(data, raw)
    except Exception:
        pass

    # Pass 4: Fallback regex structure extractor (recovers module & files when inner quotes fail JSON)
    _logger.info("Attempting fallback regex structure extractor on raw AI response...")
    try:
        data = _extract_fallback_structure(text)
        return _validate_and_return(data, raw)
    except Exception as exc:
        raise ResponseParseError(
            f"JSON parse failed ({exc}). First 200 chars: {raw[:200]!r}"
        ) from exc


def _extract_fallback_structure(raw_text: str) -> dict:
    """Fallback extractor when unescaped quotes or syntax drifts break standard json.loads."""
    # Extract module metadata
    module_dict = {
        "technical_name": "vibe_generated_module",
        "display_name": "Vibe Generated Module",
        "summary": "Generated Odoo Module",
        "category": "Custom",
        "version": "17.0.1.0.0",
        "depends": ["base"],
        "license": "LGPL-3"
    }

    # Try extracting module JSON snippet
    mod_match = re.search(r'"module"\s*:\s*\{([^}]+)\}', raw_text, re.DOTALL)
    if mod_match:
        try:
            m_dict = json.loads("{" + mod_match.group(1) + "}", strict=False)
            if isinstance(m_dict, dict):
                module_dict.update(m_dict)
        except Exception:
            for key in ["technical_name", "display_name", "summary", "category", "version", "license"]:
                km = re.search(r'"' + key + r'"\s*:\s*"([^"]+)"', mod_match.group(1))
                if km:
                    module_dict[key] = km.group(1)

    # Extract files array using regex for path and content pairs
    files = []
    # Match path entries
    paths = re.findall(r'"path"\s*:\s*"([^"]+)"', raw_text)
    for p in paths:
        p_pos = raw_text.find(f'"path": "{p}"')
        if p_pos != -1:
            c_pos = raw_text.find('"content": "', p_pos)
            if c_pos != -1:
                start_c = c_pos + len('"content": "')
                # Find boundary of this file entry
                next_p = raw_text.find('"path": "', start_c)
                if next_p != -1:
                    end_c = raw_text.rfind('"', start_c, next_p)
                else:
                    end_c = raw_text.rfind('"')
                
                if end_c > start_c:
                    c_text = raw_text[start_c:end_c]
                    # Unescape common JSON escapes
                    c_text = c_text.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
                    files.append({"path": p, "content": c_text})

    if files:
        return {"module": module_dict, "files": files}

    raise ResponseParseError("Could not extract file structure from AI output.")


def _validate_and_return(data: dict, raw: str) -> dict:
    if not isinstance(data, dict):
        raise ResponseParseError(f"Root JSON is not an object. First 200 chars: {raw[:200]!r}")

    if "error" in data:
        raise ResponseParseError(str(data["error"]))

    if not isinstance(data.get("module"), dict):
        raise ResponseParseError(f"'module' key missing or not a dict. First 200 chars: {raw[:200]!r}")

    if not isinstance(data.get("files"), list):
        raise ResponseParseError(f"'files' key missing or not a list. First 200 chars: {raw[:200]!r}")

    for i, f in enumerate(data["files"]):
        if not isinstance(f, dict) or "path" not in f or "content" not in f:
            raise ResponseParseError(f"files[{i}] missing 'path' or 'content'. First 200 chars: {raw[:200]!r}")

    return data
