# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul PI (<https://www.cybrosys.com>)
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


class ProductTemplateInherited(models.Model):
    """Inheriting the product template for adding the field for icecat
    product brand"""
    _inherit = 'product.template'

    brand = fields.Char(string="Brand",
                        help="The brand name of product in the icecat")

    def get_icecat_product_details(self, product_id):
        """Returns the details of a product"""
        if product_id:
            products = self.env['product.product'].sudo().browse(int(product_id))
            username = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_icecat_connector.user_id_icecat')
            icecat_product_details = {'brand': products.brand,
                                      'product_code': products.default_code,
                                      'username': str(username)}
            return icecat_product_details


