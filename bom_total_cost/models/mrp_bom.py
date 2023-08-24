# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class MrpBom(models.Model):
    """Inherit mrp.bom model to add total cost of BOM"""
    _inherit = 'mrp.bom'
    currency_id = fields.Many2one(related='company_id.currency_id',
                                  string='Currency', help='Currency of company')
    bom_cost = fields.Monetary(string='Cost Per Unit',
                               compute='_compute_bom_cost',
                               currency_field='currency_id',
                               help="Total cost of the BOM based on the raw "
                                    "materials cost price per unit")
    total_bom_cost = fields.Monetary(string='Total Cost',
                                     compute='_compute_bom_cost',
                                     currency_field='currency_id',
                                     help="Total cost of the BOM based on the "
                                          "raw materials cost price")

    @api.depends('bom_line_ids.product_id', 'product_qty')
    def _compute_bom_cost(self):
        """Compute total cost per unit"""
        for rec in self:
            rec.bom_cost = sum(rec.bom_line_ids.mapped('cost'))
            rec.total_bom_cost = rec.bom_cost * rec.product_qty


class MrpBomLine(models.Model):
    """Inherit mrp.bom.line model to add total cost of order line"""
    _inherit = 'mrp.bom.line'
    cost = fields.Float(string='Unit Cost',
                        help='The total price of the product is calculated '
                             'based on the quantity.')

    @api.onchange('product_qty', 'product_id')
    def _onchange_product_id(self):
        """ Computing total cost of each component"""
        self.cost = self.product_id.standard_price * self.product_qty
