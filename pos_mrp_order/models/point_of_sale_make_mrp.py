# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nikhil krishnan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api
from odoo.exceptions import Warning


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def create_mrp_from_pos(self, products):
        product_ids = []
        if products:
            for product in products:
                flag = 1
                if product_ids:
                    for product_id in product_ids:
                        if product_id['id'] == product['id']:
                            product_id['qty'] += product['qty']
                            flag = 0
                if flag:
                    product_ids.append(product)
            for prod in product_ids:
                if prod['qty'] > 0:
                    product = self.env['product.product'].search([('id', '=', prod['id'])])
                    bom_count = self.env['mrp.bom'].search([('product_tmpl_id', '=', prod['product_tmpl_id'])])
                    if bom_count:
                        bom_temp = self.env['mrp.bom'].search([('product_tmpl_id', '=', prod['product_tmpl_id']),
                                                               ('product_id', '=', False)])
                        bom_prod = self.env['mrp.bom'].search([('product_id', '=', prod['id'])])
                        if bom_prod:
                            bom = bom_prod[0]
                        elif bom_temp:
                            bom = bom_temp[0]
                        else:
                            bom = []
                        if bom:
                            vals = {
                                'origin': 'POS-' + prod['pos_reference'],
                                'state': 'confirmed',
                                'product_id': prod['id'],
                                'product_tmpl_id': prod['product_tmpl_id'],
                                'product_uom_id': prod['uom_id'],
                                'product_qty': prod['qty'],
                                'bom_id': bom.id,
                            }
                            self.sudo().create(vals)
        return True


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    to_make_mrp = fields.Boolean(string='To Create MRP Order',
                                 help="Check if the product should be make mrp order")

    @api.onchange('to_make_mrp')
    def onchange_to_make_mrp(self):
        if self.to_make_mrp:
            if not self.bom_count:
                raise Warning('Please set Bill of Material for this product.')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('to_make_mrp')
    def onchange_to_make_mrp(self):
        if self.to_make_mrp:
            if not self.bom_count:
                raise Warning('Please set Bill of Material for this product.')
