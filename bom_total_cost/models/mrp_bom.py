# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(Contact : odoo@cybrosys.com)
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
                                  string='Currency',
                                  help='The currency used by the company')
    bom_cost = fields.Monetary(string='Cost Per Unit',
                               compute='_compute_bom_cost',
                               currency_field='currency_id',
                               help="Total cost of the BOM based on the raw\n"
                                    " materials cost price per unit")
    total_bom_cost = fields.Monetary(string='Total Cost',
                                     compute='_compute_bom_cost',
                                     currency_field='currency_id',
                                     help="Total cost of the BOM based on the\n"
                                          " raw materials cost")

    @api.depends('bom_line_ids.product_id', 'product_qty')
    def _compute_bom_cost(self):
        """Compute total cost per unit"""
        total_cost = 0
        for rec in self.bom_line_ids:
            cost_unit = rec.product_id.standard_price * rec.product_qty
            total_cost += cost_unit
            self.bom_cost = total_cost
            self.total_bom_cost = self.bom_cost * self.product_qty
