# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class ProductEstimatedDeliveryTime(models.Model):
    """This is for adding the estimated delivery time for each product"""
    _name = 'product.estimated.delivery.time'
    _description = "Product Estimated Delivery Time"

    name = fields.Char(string="Name", required=True,
                       help="Estimated delivery time name")
    pin = fields.Char(string="PIN", required=True, help="PIN number")
    days = fields.Integer(string="Available Within (Days)", required=True,
                          help="Estimated delivery time in days")
    product_id = fields.Many2one('product.template',
                                 string="Product", help="Relational field")
