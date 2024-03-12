# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul Raj(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models


class MRPOrderLine(models.Model):
    """Creates the model mrp.order.line """
    _name = 'mrp.order.line'
    _description = "Bills of Materials Components"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    product_id = fields.Many2one('product.product', string="Product",
                                 help="Component Product",
                                 required=True)
    product_qty = fields.Float(string="Quantity", default=1.0, tracking=True,
                               help="Quantity of products to be consumed")
    uom_id = fields.Many2one('uom.uom', string='Product Unit of Measure',
                             required=True,
                             help="Unit of Measure of the product to be "
                                  "consumed")
    mrp_id = fields.Many2one('mrp.order', string='MRP Order',
                             help="MRP Order of the product")
