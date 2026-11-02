# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import models, _


class ProductTemplate(models.Model):
    """Inheriting The product template for adding the product_detail_search
    method"""
    _inherit = 'product.template'

    def get_selection_label(self, res_model, field_name, field_value):
        """Return the translated label for a selection field value."""
        selection = dict(
            self.env[res_model].fields_get(allfields=[field_name])[field_name][
                'selection'])
        return _(selection[field_value]) if field_value in selection else False

    def product_detail_search(self, barcode):
        """Find the details for the product When the barcode Scan is
        Detected"""
        if not barcode or not str(barcode).strip():
            return False
        product = self.env['product.product'].search(
            [('barcode', '=', str(barcode).strip())], limit=1)
        if product:
            product_type = self.get_selection_label(
                'product.product', 'type', product.type) if product.type else False
            specification = [
                color.strip() for color in
                product.display_name.split('(')[-1].split(')')[0].split(',')
                if color.strip()
            ] if '(' in product.display_name and ')' in product.display_name else []
            tax_names = ', '.join(product.taxes_id.mapped('name')) if product.taxes_id else 'No tax'
            currency_symbol = str(product.currency_id.symbol) if product.currency_id.symbol else ''
            product_details = [{
                'id': product.id,
                'display_name': product.display_name,
                'name': product.name,
                'type': product_type,
                'taxes_id': product.taxes_id.ids if product.taxes_id else False,
                'tax_amount': tax_names,
                'barcode': product.barcode,
                'default_code': product.default_code,
                'qty_available': product.qty_available,
                'list_price': product.list_price,
                'company_id': [product.company_id.id, product.company_id.name] if product.company_id else False,
                'category': product.categ_id.name,
                'symbol': currency_symbol,
                'specification': specification,
            }]
        else:
            product_details = False
        return product_details
