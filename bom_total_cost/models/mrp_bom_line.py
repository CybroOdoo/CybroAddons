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
    """Inherit mrp.bom.line model to add total cost of order line"""
    _inherit = 'mrp.bom.line'

    cost = fields.Float(string='Cost',  compute='_compute_cost',
                        help='The total cost of the bom components',store=True)

    @api.depends('product_qty', 'product_id')
    def _compute_cost(self):
        """ Computing total cost of each component"""
        for rec in self:
            rec.cost = rec.product_id.standard_price * rec.product_qty
