# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class ChecklistItem(models.Model):
    """Model representing checklist items within a checklist template."""
    _name = 'checklist.item'
    _description = "Checklist Item"
    _order = 'sequence, id'

    name = fields.Char(
        required=True,
        help="Name of the checklist item"
    )
    sequence = fields.Integer(
        default=1,
        help="Sequence order for display"
    )
    description = fields.Char(
        help="Description of the checklist item"
    )
    checklist_id = fields.Many2one(
        'task.checklist',
        ondelete='cascade',
        help="Associated task checklist template"
    )
