# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
################################################################################
from odoo import fields, models


class ProductAddVendor(models.TransientModel):
    """
        Model for adding seller_ids (product vendors)
    """
    _name = 'product.add.vendor'
    _description = 'Product Add Vendors'

    product_ids = fields.Many2many('product.template',
                                   string='Selected Products',
                                   help='Products which are selected')
    vendor_ids = fields.One2many('product.vendor', 'wizard_id',
                                 string="Product Attributes",
                                 help='Product Vendors')

    def action_add_product_vendors(self):
        """
        Function for adding seller_ids (product vendors) for Selected Products
        """
        if self.product_ids and self.vendor_ids:
            for products in self.product_ids:
                for vendor in self.vendor_ids:
                    products.seller_ids = [fields.Command.create({
                        'partner_id': vendor.partner_id.id,
                        'price': vendor.price,
                        'currency_id': vendor.currency_id.id,
                        'delay': vendor.delay,
                    })]


class ProductAttribute(models.TransientModel):
    _name = 'product.vendor'
    _description = 'Product Vendors'

    partner_id = fields.Many2one('res.partner',
                                 string='Vendor',
                                 help='Partner ID')
    price = fields.Float(string='Price', help='Price',
                         required=True)
    delay = fields.Integer(string='Delivery Lead Time',
                           help='Delivery Lead Time', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  help='Currency', required=True)
    wizard_id = fields.Many2one('product.add.vendor', string='ID',
                                help='Wizard ID')
