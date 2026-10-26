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


class TaskChecklist(models.Model):
    """Model representing a task checklist template."""
    _name = 'task.checklist'
    _description = 'Task Checklist'

    name = fields.Char(
        required=True,
        help="Name of the checklist"
    )
    description = fields.Char(
        help="Description of the checklist"
    )
    checklist_ids = fields.One2many(
        'checklist.item',
        'checklist_id',
        string="Checklist Items",
        help="Items belonging to this checklist template"
    )
