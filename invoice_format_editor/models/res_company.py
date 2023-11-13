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


class ResCompany(models.Model):
    """Inheriting the res company model"""
    _inherit = 'res.company'

    base_layout = fields.Selection(
        selection=[('default', 'Default'),
                   ('modern', 'Modern'),
                   ('normal', 'Normal'),
                   ('old', 'Old Standard')],
        required=True, string="Invoice Document Layout", default="default",
        help="base layout selection")
    document_layout_id = fields.Many2one("doc.layout",
                                         string="Invoice Layout Configuration",
                                         help="Invoice layout configuration")
