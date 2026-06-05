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

import json
import logging
import os

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Module-level constant — not a class attribute so it doesn't interfere
# with Odoo's field introspection.
_EXT_LANGUAGE_MAP = {
    ".py":   "python",
    ".xml":  "xml",
    ".csv":  "csv",
    ".md":   "markdown",
    ".txt":  "plaintext",
    ".rst":  "plaintext",
    ".json": "json",
    ".scss": "scss",
    ".css":  "css",
    ".js":   "javascript",
}


class VibeGeneratedFile(models.Model):
    _name = "vibe.generated.file"
    _description = "Vibe Generated File"
    _rec_name = "path"
    _order = "path"

    module_id = fields.Many2one(
        "vibe.generated.module",
        string="Module",
        required=True,
        ondelete="cascade",
        index=True,
    )
    path = fields.Char(
        string="Path",
        required=True,
        help="Relative path inside the module, e.g. 'models/product_brand.py'.",
    )
    content = fields.Text(string="Content", required=True)
    language = fields.Char(
        string="Language",
        compute="_compute_language",
        store=True,
        help="Syntax-highlighting hint derived from file extension.",
    )
    # Tracks whether this file has been hand-edited since it was generated.
    # The UI uses this to show a "Modified" badge and the ZIP packager
    # treats user edits as authoritative.
    user_modified = fields.Boolean(
        string="User Modified",
        default=False,
        help="True if the user has hand-edited this file after generation.",
    )

    _sql_constraints = [
        (
            "module_path_unique",
            "unique(module_id, path)",
            "Duplicate file path within the same generated module.",
        ),
    ]

    @api.depends("path")
    def _compute_language(self):
        for rec in self:
            _, ext = os.path.splitext(rec.path or "")
            rec.language = _EXT_LANGUAGE_MAP.get(ext.lower(), "plaintext")

    # ── Public API: called from OWL frontend ──────────────────────────────

    def save_content(self, new_content):
        """Persist a user-edited version of this file's content.

        Marks the file as user_modified, writes the new content, then
        re-validates the parent module so the validation badge reflects
        the edit.

        JS call:
            orm.call("vibe.generated.file", "save_content", [[file_id], new_content])

        Returns a dict the frontend can use to refresh its state:
            {
                "path":               str,
                "content":            str,    # the saved content, echoed back
                "user_modified":      True,
                "validation_state":   "valid" | "invalid" | "pending",
                "validation_errors":  [...],  # parsed list, possibly empty
            }
        """
        self.ensure_one()
        if new_content is None:
            raise UserError(_("File content cannot be null."))

        # Save the new content
        self.write({
            "content":       new_content,
            "user_modified": True,
        })

        # Re-validate the parent module with the edited content in place.
        # The validator works on a dict-shaped envelope, so reconstruct it
        # from the module's current state.
        mod = self.module_id
        try:
            manifest = json.loads(mod.manifest_data) if mod.manifest_data else {}
        except (json.JSONDecodeError, TypeError):
            manifest = {}

        parsed = {
            "module": manifest,
            "files": [
                {"path": f.path, "content": f.content}
                for f in mod.file_ids
            ],
        }

        from ..services.module_validator import validate as validate_module
        try:
            errors = validate_module(parsed)
        except Exception as e:
            _logger.warning("Re-validation after edit failed: %s", e)
            errors = []

        mod.write({
            "validation_state":  "valid" if not errors else "invalid",
            "validation_errors": json.dumps(errors) if errors else False,
        })

        return {
            "path":              self.path,
            "content":           self.content,
            "user_modified":     self.user_modified,
            "validation_state":  mod.validation_state,
            "validation_errors": errors,
        }
