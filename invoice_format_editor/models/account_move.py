# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ajith V(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields


class AccountMove(models.Model):
    """Inheriting the account move model and added the base layout model and
    a relational field to doc layout model"""
    _inherit = 'account.move'

    base_layout = fields.Selection(
        selection=[('default', 'Default'),
                   ('modern', 'Modern'),
                   ('normal', 'Normal'),
                   ('old', 'Old Standard')],
        required=True,
        string="Invoice Document Layout",
        default="default", help="The invoice document layout selection field")
    theme_id = fields.Many2one(
        'doc.layout',
        related='company_id.document_layout_id', string="Theme",
        help="The relational field for document layout")
