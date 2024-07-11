# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev K P(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class PosCrossSellingLine(models.Model):
    """Pos Cross-Selling Products Line"""
    _name = 'pos.cross.selling.line'
    _description = 'POS Cross-Selling Product Line'

    product_id = fields.Many2one('product.product',
                                 domain=[('available_in_pos', '=', 'True')],
                                 required=True, string='Product Name',
                                 help="Product details")
    active = fields.Boolean(string='Active',
                            help="To check the cross selling is active or not",
                            default=True)
    pos_cross_product_id = fields.Many2one('pos.cross.selling',
                                           string='Pos Cross products',
                                           help="Pos Cross products")
