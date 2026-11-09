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


class MrpBomLine(models.Model):
    """Inherit mrp.bom.line model to add total cost of BOM component line."""
    _inherit = 'mrp.bom.line'

    currency_id = fields.Many2one(
        related='bom_id.currency_id',
        string='Currency',
        help='The currency used for the BOM component cost.',
    )
    cost = fields.Monetary(
        string='Cost',
        compute='_compute_cost',
        currency_field='currency_id',
        store=True,
        help='The total cost of the BOM component based on product cost and UoM.',
    )

    @api.depends('product_qty', 'product_id', 'product_id.standard_price', 'uom_id')
    def _compute_cost(self):
        """Compute the total cost of each component line with UoM conversion."""
        for line in self:
            price = line.product_id.standard_price or 0.0
            if line.uom_id and line.product_id.uom_id and line.uom_id != line.product_id.uom_id:
                qty = line.uom_id._compute_quantity(line.product_qty, line.product_id.uom_id)
            else:
                qty = line.product_qty
            line.cost = price * qty
