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

"""Module template merger.

Takes the AI's `{module, files}` envelope and merges in standard boilerplate
files from `vibe_coding_assistant/module_templates/` — README, LICENSE,
docs, etc. Template variables like `{{technical_name}}` are substituted
with values from the parsed manifest.

Design notes:
- Templates are static files on disk, not editable per-conversation. To
  customise: edit files under module_templates/ and reinstall the module.
- The AI is NOT informed about template files — they're added after the
  AI has finished. This keeps the prompt small and the AI focused on
  code generation. If the AI happened to produce a README.md anyway,
  we DO NOT overwrite it (AI wins on conflicts).
- Variable substitution is intentionally simple: `{{name}}` → string.
  No conditionals, no loops. Anything more complex belongs in code.
"""

import datetime
import logging
import os
import re

_logger = logging.getLogger(__name__)

# Filename of every template the merger should consider. Add files here
# when adding new templates under module_templates/.
TEMPLATE_FILES = (
    "README.md",
    "doc/RELEASE_NOTES.md",
    "static/description/index.html",
)

# Resolve the templates directory relative to this file's location.
# services/ is at vibe_coding_assistant/services/, so templates/ is one up.
TEMPLATES_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "module_templates",
)


def merge_templates(parsed):
    """Add boilerplate files to the parsed generation envelope.

    :param parsed: dict {"module": {...}, "files": [{"path", "content"}, ...]}
                   as returned by response_parser.parse(). Mutated in place.
    :returns: the same dict for chaining.
    """
    module = parsed.get("module") or {}
    existing_paths = {f["path"] for f in parsed.get("files", [])}

    context = _build_context(module)

    added = 0
    for relpath in TEMPLATE_FILES:
        if relpath in existing_paths:
            # AI already produced this file — respect it. No silent overwrite.
            _logger.debug("Template %s already exists in AI output; skipping.", relpath)
            continue

        abspath = os.path.join(TEMPLATES_ROOT, relpath)
        if not os.path.isfile(abspath):
            _logger.warning("Template file not found on disk: %s", abspath)
            continue

        try:
            with open(abspath, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except OSError as exc:
            _logger.warning("Could not read template %s: %s", abspath, exc)
            continue

        rendered = _substitute(raw, context)
        parsed["files"].append({"path": relpath, "content": rendered})
        added += 1

    # Make sure the manifest's `data` references aren't accidentally
    # claiming static/description files etc. (they shouldn't, but be safe).
    _logger.info("Template merger added %d boilerplate file(s).", added)
    return parsed


# ── Helpers ───────────────────────────────────────────────────────────────


def _build_context(module):
    """Pull substitution values out of the module's parsed manifest data."""
    depends = module.get("depends") or []
    if isinstance(depends, list):
        depends_list = ", ".join("`%s`" % d for d in depends) or "—"
    else:
        depends_list = str(depends)

    return {
        "technical_name": module.get("technical_name", "module"),
        "display_name":   module.get("display_name", "Module"),
        "summary":        module.get("summary", ""),
        "description":    module.get("description") or module.get("summary", ""),
        "version":        module.get("version", "19.0.1.0.0"),
        "category":       module.get("category", "Uncategorized"),
        "license":        module.get("license", "LGPL-3"),
        "author":         module.get("author", "Your Company"),
        "depends_list":   depends_list,
        "year":           str(datetime.date.today().year),
        "date":           datetime.date.today().isoformat(),
        "odoo_version":   "19.0",
    }


# Compiled once. Matches {{ name }} with optional whitespace inside.
_VAR_PATTERN = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def _substitute(text, context):
    """Replace every `{{name}}` token with context[name], or leave it alone
    if the variable isn't in context (helps debug missing vars)."""
    def repl(match):
        key = match.group(1)
        return str(context.get(key, match.group(0)))
    return _VAR_PATTERN.sub(repl, text)
