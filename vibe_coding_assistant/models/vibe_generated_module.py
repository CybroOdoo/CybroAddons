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
import re

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VibeGeneratedModule(models.Model):
    _name = "vibe.generated.module"
    _description = "Vibe Generated Module"
    _order = "create_date desc, id desc"

    conversation_id = fields.Many2one(
        "vibe.conversation",
        string="Conversation",
        required=True,
        ondelete="cascade",
        index=True,
    )
    message_id = fields.Many2one(
        "vibe.message",
        string="Source Message",
        ondelete="set null",
    )
    technical_name = fields.Char(string="Technical Name", required=True)
    # NOTE: the spec calls this field "display_name", but that name is reserved
    # by Odoo's ORM (computed from name_get). We store it as "name" which is
    # the standard Odoo field for a record's human-readable identifier.
    name = fields.Char(
        string="Module Name",
        required=True,
        help="Human-readable name, e.g. 'Product Brand Management'.",
    )
    manifest_data = fields.Text(
        string="Manifest Data",
        help="JSON-serialised module-level metadata for quick UI reads.",
    )
    validation_state = fields.Selection(
        [("pending", "Pending"), ("valid", "Valid"), ("invalid", "Invalid")],
        string="Validation",
        default="pending",
    )
    validation_errors = fields.Text(
        string="Validation Errors",
        help="JSON list of {file, line, message} dicts.",
    )
    file_ids = fields.One2many(
        "vibe.generated.file", "module_id", string="Files"
    )
    download_count = fields.Integer(string="Downloads", default=0)

    # ── Iterative refinement — revision tracking ────────────────────────
    # When the user clicks "Refine" on a previous module, the new generation
    # is stored as a separate module record linked here. This preserves the
    # full history (every version can still be downloaded), and the UI can
    # display revision badges and a "based on" backlink.
    parent_module_id = fields.Many2one(
        "vibe.generated.module",
        string="Refined From",
        ondelete="set null",
        index=True,
        help="The previous module this revision was refined from. "
             "NULL means this is a root (original) generation.",
    )
    child_module_ids = fields.One2many(
        "vibe.generated.module", "parent_module_id",
        string="Refinements",
    )
    revision_number = fields.Integer(
        string="Revision",
        default=1,
        help="1 for the original generation; 2, 3, ... for each refinement.",
    )
    is_refinement = fields.Boolean(
        string="Is Refinement",
        compute="_compute_is_refinement",
        store=True,
    )

    @api.depends("parent_module_id")
    def _compute_is_refinement(self):
        for rec in self:
            rec.is_refinement = bool(rec.parent_module_id)

    @api.constrains("technical_name")
    def _check_technical_name(self):
        for rec in self:
            if not re.match(r"^[a-z][a-z0-9_]*$", rec.technical_name or ""):
                raise ValidationError(_(
                    "Invalid technical name '%s'. "
                    "Must be lowercase letters, digits, and underscores, "
                    "starting with a letter."
                ) % rec.technical_name)

    def action_download(self):
        """Return the HTTP download URL for this module."""
        self.ensure_one()
        return "/vibe/module/%d/download" % self.id

    def get_validation_errors_list(self):
        """Return parsed validation errors or an empty list."""
        self.ensure_one()
        if not self.validation_errors:
            return []
        try:
            return json.loads(self.validation_errors)
        except (json.JSONDecodeError, TypeError):
            return []
