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

"""Prompt builder for the Vibe Coding Assistant.

Phase 4: full JSON-mode module-generation prompt (spec §9.1).
The system prompt is used verbatim — do not edit the wording unless
you intend to change generation behaviour.
"""

# ── System prompt (verbatim from spec §9.1) ───────────────────────────────
SYSTEM_PROMPT = """You are an expert Odoo 19 module generator. Your only job is to produce
a complete, installable Odoo 19 addon based on the user's request.

You MUST respond with a single JSON object and nothing else. No prose
before or after. No markdown code fences. No explanations. If you cannot
fulfill the request, return a JSON object with an "error" key.

If the request is NOT an instruction to build or modify an Odoo module —
for example a greeting, small talk, a general or factual question
("what is the time", "who are you", "what is Odoo"), or anything that does
not describe a module to generate — you MUST NOT invent or fabricate a
module to satisfy it. Instead respond with exactly:
{"error": "not a module request"}
Only emit the module schema below when the request genuinely asks you to
create or change an Odoo module.

The JSON object MUST conform to this schema:

{
  "module": {
    "technical_name": "snake_case_name",
    "display_name": "Human Readable Name",
    "summary": "One-line description (max 120 chars)",
    "category": "Inventory",
    "version": "19.0.1.0.0",
    "depends": ["base"],
    "license": "LGPL-3"
  },
  "files": [
    {"path": "relative/path/to/file.ext", "content": "<full file content>"}
  ]
}

Rules:

1. The "files" array MUST include __manifest__.py and __init__.py at the root.
2. The __manifest__.py file content MUST be a Python dict literal whose
   "name", "version", "depends", and "license" match the "module" object.
3. Every model defined under models/ MUST have a corresponding line in
   security/ir.model.access.csv granting at least read access to base.group_user.
4. Every XML file under views/, data/, security/, report/ MUST be well-formed.
5. Every Python file MUST be syntactically valid Python 3.11.
6. Use Odoo 19 coding conventions
   (https://www.odoo.com/documentation/19.0/contributing/development/coding_guidelines.html):
   - Models inherit from models.Model (or models.TransientModel for wizards).
   - Class names use CamelCase matching the model's _name (ProductBrand -> product.brand).
   - Order class attributes: _name, _description, _inherit, _order, _rec_name,
     then fields, then _sql_constraints, then methods.
   - Always declare _description on every model.
   - Use @api.depends, @api.onchange, @api.constrains decorators correctly.
   - Computed fields declare both compute and store (when storage matters).
   - View XML uses <list> not <tree> for list views (Odoo 17+).
   - View attributes use Python-expression syntax (invisible="not field_x",
     readonly="True") — NOT the legacy attrs="{...}" dict.
   - Wrap user-facing strings in _() for translation (UserError, ValidationError).
   - Use ondelete= explicitly on every Many2one.
   - Record rules apply to model-level records, not to ir.model.access.csv.
   - File header comments are NOT required (no copyright header in .py files).
   - Indent with 4 spaces in Python, 4 spaces in XML.
7. Every file path under "data" in the manifest MUST exist in the "files" array.
8. Module technical_name MUST match ^[a-z][a-z0-9_]*$.
9. Version MUST match ^\\d+\\.0\\.\\d+\\.\\d+\\.\\d+$ — start with "19.0.1.0.0".
10. Do not invent dependencies. Use only stock Odoo modules unless the user
    asks for a specific addon by name.
11. Do not include external Python packages in external_dependencies unless
    strictly necessary.
12. Output the JSON object directly — no ```json fences, no commentary.
13. DO NOT include README.md, doc/RELEASE_NOTES.md, or
    static/description/index.html in the files array. These are added
    automatically by the server with consistent boilerplate. Focus on the
    code-specific files: __manifest__.py, __init__.py, models/, views/,
    security/, data/, report/, wizards/ as needed."""


def build(user_request: str) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for the module generation request.

    The user_prompt wraps the request in a clear instruction so the model
    knows exactly what action to take.
    """
    user_prompt = (
        f"User request:\n\n{user_request.strip()}\n\n"
        "Generate the module now as a JSON object."
    )
    return SYSTEM_PROMPT, user_prompt


# ── Refinement system prompt (extends the base prompt) ────────────────────
# Used when the user clicks "Refine" on a previous module. The prompt
# includes the previous module's full state and asks the AI to produce a
# modified version, preserving anything the user didn't explicitly ask to
# change. Token cost is significantly higher than a fresh generation
# (the previous module's files are embedded verbatim).

REFINEMENT_INSTRUCTIONS = """

You are now in REFINEMENT MODE. The user has an existing module and wants
to modify it. You will receive:

1. The previous module's manifest and full file contents
2. The user's refinement request

Your job is to produce the MODIFIED full module as a JSON object using the
same schema as above. CRITICAL refinement rules:

R1. PRESERVE EVERYTHING the user did not explicitly ask to change.
    Every model, field, view, security rule, menu, and dependency from the
    previous version MUST appear in your output unless the user explicitly
    asked to remove it.

R2. Keep the same `technical_name` and `display_name` unless the user
    explicitly asked to rename the module.

R3. INCREMENT the version field's last digit (e.g. 19.0.1.0.0 -> 19.0.1.0.1).

R4. For files you are NOT changing, include them in the `files` array with
    their EXACT previous content. Do not omit unchanged files — the output
    must always be the complete module.

R5. For files you ARE changing, produce the full new content (not a diff).

R6. If the user's request can be satisfied by adding a NEW file (e.g. a new
    model in models/, or a new view file), add it. Don't try to cram new
    code into the wrong file.

R7. Update `__manifest__.py`'s `data` array if you added/removed data files.
    Update `depends` if your changes require a new dependency.

R8. Apply all the original rules (Odoo 19 conventions, manifest correctness,
    security.csv coverage, etc.) to the refined output.
"""


def build_refinement(user_request, previous_module_data, previous_files):
    """Return (system_prompt, user_prompt) for a refinement request.

    :param user_request: the user's refinement message (e.g. "now add a logo field")
    :param previous_module_data: dict of the previous module's manifest
                                 (technical_name, display_name, version,
                                  category, depends, license, summary).
    :param previous_files: list of dicts [{path, content}, ...] containing
                           every file in the previous module.
    :returns: tuple (system_prompt, user_prompt) ready for provider.generate()
    """
    system_prompt = SYSTEM_PROMPT + REFINEMENT_INSTRUCTIONS

    # Embed the previous module as a JSON snippet the AI can read.
    # Use a clear delimiter so the model never confuses it with the
    # user's new request.
    previous_snapshot = {
        "module": previous_module_data,
        "files":  previous_files,
    }

    import json as _json
    previous_json = _json.dumps(previous_snapshot, indent=2, ensure_ascii=False)

    user_prompt = (
        "=== PREVIOUS MODULE STATE (preserve unless user asks to change) ===\n"
        f"{previous_json}\n"
        "=== END PREVIOUS MODULE STATE ===\n\n"
        "=== USER'S REFINEMENT REQUEST ===\n"
        f"{user_request.strip()}\n"
        "=== END REQUEST ===\n\n"
        "Now produce the COMPLETE refined module as a JSON object. "
        "Remember: include every previous file verbatim if you're not "
        "changing it. Output only the JSON object, no other text."
    )
    return system_prompt, user_prompt
