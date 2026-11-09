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
    """Inherit mrp.bom model to add total cost of BOM."""
    _inherit = 'mrp.bom'

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        compute='_compute_currency_id',
        help='The currency used by the company for BOM costing.',
    )
    bom_cost = fields.Monetary(
        string='Cost Per Unit',
        compute='_compute_bom_cost',
        currency_field='currency_id',
        store=True,
        help='Total cost of the BOM raw materials per finished unit.',
    )
    total_bom_cost = fields.Monetary(
        string='Total Cost',
        compute='_compute_bom_cost',
        currency_field='currency_id',
        store=True,
        help='Total cost of the BOM based on all raw material components.',
    )

    @api.depends('company_id')
    def _compute_currency_id(self):
        """Compute company or environment currency for multi-company support."""
        for bom in self:
            bom.currency_id = (
                bom.company_id.currency_id or self.env.company.currency_id
            )

    @api.depends('bom_line_ids.cost', 'product_qty')
    def _compute_bom_cost(self):
        """Compute total BOM raw material cost and cost per finished unit."""
        for bom in self:
            total_cost = sum(bom.bom_line_ids.mapped('cost'))
            bom.total_bom_cost = total_cost
            bom.bom_cost = total_cost / bom.product_qty if bom.product_qty else 0.0
