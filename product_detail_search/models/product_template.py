# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul P I (odoo@cybrosys.com)
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
from odoo import models


class ProductTemplate(models.Model):
    """Inheriting The product template for adding the product_detail_search
    method"""
    _inherit = 'product.template'

    def product_detail_search(self, barcode):
        """Find the details for the product When the barcode Scan is
        Detected"""
        product = self.env['product.product'].search(
            [('barcode', '=', barcode)])
        if product:
            product_details = product.read()
            specification = [color.strip() for color in
                             product_details[0]['display_name'].split("(")[
                                 -1].split(")")[0].split(",")]
            symbol = self.env['res.currency'].browse(
                int(product_details[0]['currency_id'][0]))
            extra_details = {'symbol': str(symbol.symbol)}
            if product_details[0]['taxes_id']:
                extra_details.update({'tax_amount': str(
                    self.env['account.tax'].browse(
                        int(product_details[0]['taxes_id'][0])).name)})
            else:
                extra_details.update({'tax_amount': 'No tax',
                                      'specification': specification})
            product_details[0].update(extra_details)
            return product_details
        else:
            product_details = False
            return product_details
