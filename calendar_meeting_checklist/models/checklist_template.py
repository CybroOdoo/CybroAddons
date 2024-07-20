# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.

###############################################################################
from odoo import fields, models


class ChecklistTemplate(models.Model):
    """Checklist template model."""
    _name = 'checklist.template'
    _description = 'Checklist Template'
    _inherit = 'mail.thread'

    name = fields.Char(string="Template name",
                       help='Name for checklist template.')
    checklist_ids = fields.Many2many("meeting.checklist",
                                     string="Checklist",
                                     help="Allows you to associate multiple "
                                          "checklist records with single "
                                          "checklist template.")
