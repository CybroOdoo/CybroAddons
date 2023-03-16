# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Marshad (odoo@cybrosys.com)
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

from odoo import models, fields, api


class MrpBom(models.Model):
    """Inherit mrp.bom model to add total cost of BOM"""
    _inherit = 'mrp.bom'
    currency_id = fields.Many2one(related='company_id.currency_id')
    bom_cost = fields.Monetary('Cost Per Unit', compute='_compute_bom_cost',
                               currency_field='currency_id',
                               help="Total cost of the BOM based on the raw \n"
                                    " materials cost price per unit")
    total_bom_cost = fields.Monetary('Total Cost', compute='_compute_bom_cost',
                                     currency_field='currency_id',
                                     readonly=True,
                                     help="Total cost of the BOM based on the\n"
                                          " raw materials cost price")

    @api.depends('bom_line_ids.product_id', 'product_qty')
    def _compute_bom_cost(self):
        """Compute total cost per unit"""
        for rec in self:
            cost_mapp = rec.bom_line_ids.mapped('cost')
            rec.bom_cost = sum(cost_mapp)
            rec.total_bom_cost = rec.bom_cost * rec.product_qty


class MrpBomLine(models.Model):
    """Inherit mrp.bom.line model to add total cost of order line"""
    _inherit = 'mrp.bom.line'
    cost = fields.Float(string='Unit Cost')

    @api.onchange('product_qty', 'product_id')
    def _onchange_product_id(self):
        """ Computing total cost of each component"""
        self.cost = self.product_id.standard_price * self.product_qty
