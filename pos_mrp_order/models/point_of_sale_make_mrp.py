# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nikhil krishnan(odoo@cybrosys.com)
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def create_mrp_from_pos(self, products):
        product_ids = []
        if products:
            for product in products:
                if self.env['product.product'].browse(int(product['id'])).to_make_mrp:
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
                            mrp_order = self.sudo().create(vals)
                            list_value = []
                            for bom_line in mrp_order.bom_id.bom_line_ids:
                                list_value.append((0, 0, {
                                    'raw_material_production_id': mrp_order.id,
                                    'name': mrp_order.name,
                                    'product_id': bom_line.product_id.id,
                                    'product_uom': bom_line.product_uom_id.id,
                                    'product_uom_qty': (bom_line.product_qty * mrp_order.product_qty)/self.env['mrp.bom'].search([("product_tmpl_id", "=", prod['product_tmpl_id'])]).product_qty,
                                    'picking_type_id': mrp_order.picking_type_id.id,
                                    'location_id': mrp_order.location_src_id.id,
                                    'location_dest_id': bom_line.product_id.with_company(self.company_id.id).property_stock_production.id,
                                    'company_id': mrp_order.company_id.id,
                                }))

                            finished_vals = {
                                'product_id': prod['id'],
                                'product_uom_qty': prod['qty'],
                                'product_uom': prod['uom_id'],
                                'name': mrp_order.name,
                                'date_deadline': mrp_order.date_deadline,
                                'picking_type_id': mrp_order.picking_type_id.id,
                                'location_id': mrp_order.location_src_id.id,
                                'location_dest_id': mrp_order.location_dest_id.id,
                                'company_id': mrp_order.company_id.id,
                                'production_id': mrp_order.id,
                                'warehouse_id': mrp_order.location_dest_id.warehouse_id.id,
                                'origin': mrp_order.name,
                                'group_id': mrp_order.procurement_group_id.id,
                                'propagate_cancel': mrp_order.propagate_cancel,
                            }
                            mrp_order.update({'move_raw_ids': list_value,
                                              'move_finished_ids': [
                                                  (0, 0, finished_vals)]
                                              })
        return True


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    to_make_mrp = fields.Boolean(string='To Create MRP Order',
                                 help="Check if the product should be make mrp order")

    @api.onchange('to_make_mrp')
    def onchange_to_make_mrp(self):
        if self.to_make_mrp:
            if not self.bom_count:
                raise ValidationError('Please set Bill of Material for this product.')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('to_make_mrp')
    def onchange_to_make_mrp(self):
        if self.to_make_mrp:
            if not self.bom_count:
                raise Warning('Please set Bill of Material for this product.')
