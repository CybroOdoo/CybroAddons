# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swathy K S (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
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
##############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    """Inheriting the sale order model and added the base layout and
        a relational field to doc layout model"""
    _inherit = 'sale.order'

    base_layout = fields.Selection(
        [('normal', 'Normal'), ('modern', 'Modern'),
         ('old', 'Old Standard'),
         ('default', 'Default')],
        default="default",
        string="Sale Document Layout", help="Type of sale document layout")
    theme_id = fields.Many2one('doc.layout',
                               string="Sale Layout Configuration",
                               help="Configuration of sale document layout",
                               related='company_id.document_layout_id')
