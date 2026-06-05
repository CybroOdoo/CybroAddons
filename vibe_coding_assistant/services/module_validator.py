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

"""Module validator for the Vibe Coding Assistant.

Runs structural and manifest checks on the parsed generation envelope.
No Python execution or test-install — static analysis only (spec §11).

Returns a list of error dicts: {"file": str, "line": int|None, "message": str}.
Empty list means the module passed all checks.
"""

import ast
import re


def validate(parsed: dict) -> list[dict]:
    """Run all 9 validation checks and return accumulated errors.

    Caller sets vibe.generated.module.validation_state to 'valid' (empty)
    or 'invalid' (non-empty) based on the returned list.
    """
    errors: list[dict] = []
    module = parsed.get("module", {})
    files: dict[str, str] = {
        f["path"]: f["content"] for f in parsed.get("files", [])
    }

    # ── 1. Technical name pattern ─────────────────────────────────────────
    tech_name = module.get("technical_name", "")
    if not re.match(r"^[a-z][a-z0-9_]*$", tech_name):
        errors.append({
            "file": "__manifest__.py",
            "line": None,
            "message": f"Invalid technical_name {tech_name!r} — must match ^[a-z][a-z0-9_]*$",
        })

    # ── 2. Version pattern ────────────────────────────────────────────────
    version = module.get("version", "")
    if not re.match(r"^\d+\.0\.\d+\.\d+\.\d+$", version):
        errors.append({
            "file": "__manifest__.py",
            "line": None,
            "message": f"Invalid version {version!r} — must match ^\\d+\\.0\\.\\d+\\.\\d+\\.\\d+$",
        })

    # ── 3. Required files ─────────────────────────────────────────────────
    for required in ("__manifest__.py", "__init__.py"):
        if required not in files:
            errors.append({
                "file": required,
                "line": None,
                "message": f"Required file missing: {required}",
            })

    # ── 4. Manifest is a valid dict literal ───────────────────────────────
    manifest_dict = None
    if "__manifest__.py" in files:
        manifest_src = files["__manifest__.py"]
        try:
            manifest_dict = ast.literal_eval(manifest_src)
            if not isinstance(manifest_dict, dict):
                errors.append({
                    "file": "__manifest__.py",
                    "line": None,
                    "message": "__manifest__.py must evaluate to a dict",
                })
                manifest_dict = None
            else:
                for key in ("name", "version", "depends", "license"):
                    if key not in manifest_dict:
                        errors.append({
                            "file": "__manifest__.py",
                            "line": None,
                            "message": f"Manifest missing required key: {key!r}",
                        })
                if "depends" in manifest_dict and not isinstance(
                    manifest_dict["depends"], list
                ):
                    errors.append({
                        "file": "__manifest__.py",
                        "line": None,
                        "message": "Manifest 'depends' must be a list",
                    })
        except (ValueError, SyntaxError) as exc:
            errors.append({
                "file": "__manifest__.py",
                "line": getattr(exc, "lineno", None),
                "message": f"Manifest parse error: {exc}",
            })

    # ── 5. Manifest data references exist in files ────────────────────────
    if manifest_dict:
        for data_path in manifest_dict.get("data", []):
            if data_path not in files:
                errors.append({
                    "file": "__manifest__.py",
                    "line": None,
                    "message": f"Manifest 'data' references missing file: {data_path!r}",
                })

    # ── 6. models/__init__.py coherence ───────────────────────────────────
    model_py_files = [
        p for p in files
        if re.match(r"^models/[^/]+\.py$", p) and p != "models/__init__.py"
    ]
    if model_py_files:
        if "models/__init__.py" not in files:
            errors.append({
                "file": "models/__init__.py",
                "line": None,
                "message": "models/__init__.py is missing but model files exist",
            })
        else:
            init_src = files["models/__init__.py"]
            for mf in model_py_files:
                stem = mf.split("/")[-1][:-3]  # strip .py
                if stem not in init_src:
                    errors.append({
                        "file": "models/__init__.py",
                        "line": None,
                        "message": (
                            f"models/__init__.py does not appear to import {stem!r}. "
                            f"Add: from . import {stem}"
                        ),
                    })

    # ── 7. security/ir.model.access.csv exists when models are defined ────
    if model_py_files and "security/ir.model.access.csv" not in files:
        errors.append({
            "file": "security/ir.model.access.csv",
            "line": None,
            "message": (
                "security/ir.model.access.csv is missing but models are defined. "
                "Every model needs at least one access rule."
            ),
        })

    # ── 8. Python syntax check ────────────────────────────────────────────
    for path, content in files.items():
        if not path.endswith(".py"):
            continue
        try:
            ast.parse(content)
        except SyntaxError as exc:
            errors.append({
                "file": path,
                "line": exc.lineno,
                "message": f"Python syntax error: {exc.msg}",
            })

    # ── 9. XML well-formedness ────────────────────────────────────────────
    xml_paths = [p for p in files if p.endswith(".xml")]
    if xml_paths:
        try:
            from lxml import etree  # lxml is a core Odoo dependency
            for path in xml_paths:
                try:
                    etree.fromstring(files[path].encode("utf-8"))
                except etree.XMLSyntaxError as exc:
                    line = exc.position[0] if exc.position else None
                    errors.append({
                        "file": path,
                        "line": line,
                        "message": f"XML syntax error: {exc}",
                    })
        except ImportError:
            pass  # skip XML check if lxml not available

    return errors
