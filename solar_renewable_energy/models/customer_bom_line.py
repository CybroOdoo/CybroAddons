# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amrithesh K (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class CustomerBomLine(models.Model):
    """Class for Project BOM lines"""
    _name = 'customer.bom.line'
    _description = 'Customer BoM Line'

    ren_order_id = fields.Many2one(
        comodel_name='ren.order',
        string='Ren Order Reference',
        ondelete='cascade',
        help='Reference to the Renewable Order this BoM line belongs to')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        help='Select the product required for the order')
    product_qty = fields.Float(
        string='Quantity',
        help='Specify the quantity of the product required')
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        related='product_id.uom_id',
        help='Unit of measure for the selected product')
