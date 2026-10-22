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

from odoo import models, fields


class VibePromptTemplate(models.Model):
    """Curated example prompts shown above the composer when starting a chat.

    Helps users discover what the assistant can do and produces better
    generations by giving them concrete starting points instead of
    free-form requests like "what is odoo19".

    Admin-editable via Vibe Coding → Prompt Templates.
    """
    _name = "vibe.prompt.template"
    _description = "Vibe Prompt Template"
    _order = "sequence, category, name"
    _rec_name = "name"

    name = fields.Char(
        string="Label",
        required=True,
        help="Short label shown on the chip (e.g. 'Brand model').",
    )
    category = fields.Selection(
        [
            ("crud",        "CRUD Module"),
            ("inherit",     "Extend Existing"),
            ("report",      "Report"),
            ("wizard",      "Wizard"),
            ("integration", "Integration"),
            ("other",       "Other"),
        ],
        string="Category",
        required=True,
        default="crud",
    )
    prompt = fields.Text(
        string="Prompt",
        required=True,
        help="The actual prompt text that gets inserted when the user "
             "clicks the chip. Be specific — include field types, "
             "menu placement, security if relevant.",
    )
    description = fields.Char(
        string="Tooltip",
        help="Optional one-line hint shown on hover.",
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Lower values appear first within their category.",
    )
    active = fields.Boolean(default=True)
