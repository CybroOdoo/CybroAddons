# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Risha C.T (<https://www.cybrosys.com>)
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
###################################################################################

from odoo import models, fields, api
from odoo.osv import expression


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_multi_barcodes = fields.One2many('multi.barcode.products',
                                             'product_multi', string='Barcodes')

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        res.product_multi_barcodes.update({
            'template_multi': res.product_tmpl_id.id
        })
        return res

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        self.product_multi_barcodes.update({
            'template_multi': self.product_tmpl_id.id
        })
        return res


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    template_multi_barcodes = fields.One2many('multi.barcode.products',
                                              'template_multi',
                                              string='Barcodes')

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        res.template_multi_barcodes.update({
            'product_multi': res.product_variant_id.id
        })
        return res

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if self.template_multi_barcodes:
            self.template_multi_barcodes.update({
                'product_multi': self.product_variant_id.id
            })
        return res


class ProductMultiBarcode(models.Model):
    _name = 'multi.barcode.products'
    _description = 'For creating multiple Barcodes for products'

    multi_barcode = fields.Char(string="Barcode",
                                help="Provide alternate barcodes for this product")
    product_multi = fields.Many2one('product.product')
    template_multi = fields.Many2one('product.template')

    _sql_constraints = [('field_unique', 'unique(multi_barcode)',
                         'Existing barcode is not allowed !'), ]

    def get_barcode_val(self, product):
        """returns barcode of record in self and product id"""
        print(self.multi_barcode, product)
        return self.multi_barcode, product


class PosSessions(models.Model):
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        new_model = 'multi.barcode.products'
        if new_model not in result:
            result.append(new_model)
        return result

    def _loader_params_multi_barcode_products(self):
        record = {
            'search_params': {
                'fields': ['product_multi', 'multi_barcode']
            }
        }
        return record

    def _loader_params_product_product(self):
        result = super()._loader_params_product_product()
        result['search_params']['fields'].append('product_multi_barcodes')
        return result

    def _get_pos_ui_multi_barcode_products(self, params):
        record = self.env['multi.barcode.products'].search_read(
            **params['search_params'])
        return record

    def _pos_data_process(self, loaded_data):
        super()._pos_data_process(loaded_data)
        context = {}
        for rec in loaded_data['multi.barcode.products']:
            if rec['product_multi']:
                context[rec['multi_barcode']] = rec['product_multi'][0]
        loaded_data['multi_barcode'] = context