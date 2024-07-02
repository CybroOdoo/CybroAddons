# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models,_


class ProductTemplate(models.Model):
    """Inheriting The product template for adding the product_detail_search
    method"""
    _inherit = 'product.template'

    def get_selection_label(self, object, field_name, field_value):
        return _(dict(
            self.env[object].fields_get(allfields=[field_name])[field_name][
                'selection'])[field_value])

    def product_detail_search(self, barcode):
        """Find the details for the product When the barcode Scan is
        Detected"""
        product = self.env['product.product'].search(
            [('barcode', '=', barcode)])
        if product:
            product_type = self.get_selection_label('product.product','detailed_type',product.detailed_type)
            product_details = [
                {'id': product.id,
                 'display_name': product.display_name, 'name': product.name,
                 'detailed_type': product.detailed_type,
                 'tax_amount': product.taxes_id,
                 'barcode': product.barcode,
                 'default_code': product.default_code,
                 'qty_available': product.qty_available,
                 'list_price': product.list_price,
                 'company_id': product.company_id if product.company_id else False,
                 'category': product.categ_id.name
                 }]
            specification = [color.strip() for color in
                             product.display_name.split("(")[
                                 -1].split(")")[0].split(",")]
            symbol = self.env['res.currency'].browse(product.currency_id.id)
            extra_details = {'symbol': str(symbol.symbol)}
            if product.taxes_id:
                extra_details.update({'tax_amount': str(
                    self.env['account.tax'].browse(product.taxes_id.id).name),
                    'specification': specification})
            else:
                extra_details.update({'tax_amount': 'No tax',
                                      'specification': specification})
            if product_type:
                extra_details.update({'detailed_type': product_type})
            else:
                extra_details.update({'detailed_type': False})
            product_details[0].update(extra_details)
        else:
            product_details = False
        return product_details
