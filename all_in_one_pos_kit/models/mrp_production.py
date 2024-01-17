# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
from odoo import models


class MrpProduction(models.Model):
    """Inherit the class mrp_production to add new function"""
    _inherit = 'mrp.production'

    def create_mrp_from_pos(self, products):
        """Fetch value from js and create manufacturing order for the product
        and return true"""
        product_ids = []
        if products:
            for product in products:
                if self.env['product.product'].browse(
                        int(product['id'])).to_make_mrp:
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
                    if self.env['mrp.bom'].search([('product_tmpl_id', '=',
                                                    prod['product_tmpl_id'])]):
                        if self.env['mrp.bom'].search(
                                [('product_id', '=', prod['id'])]):
                            bom = self.env['mrp.bom'].search(
                                [('product_id', '=', prod['id'])])[0]
                        elif self.env['mrp.bom'].search([(
                                                         'product_tmpl_id', '=',
                                                         prod[
                                                             'product_tmpl_id']),
                                                         ('product_id', '=',
                                                          False)]):
                            bom = self.env['mrp.bom'].search([(
                                                              'product_tmpl_id',
                                                              '=', prod[
                                                                  'product_tmpl_id']),
                                                              (
                                                              'product_id', '=',
                                                              False)])[0]
                        else:
                            bom = []
                        if bom:
                            mrp_order = self.sudo().create({
                                'origin': 'POS-' + prod['pos_reference'],
                                'state': 'confirmed',
                                'product_id': prod['id'],
                                'product_tmpl_id': prod['product_tmpl_id'],
                                'product_uom_id': prod['uom_id'],
                                'product_qty': prod['qty'],
                                'bom_id': bom.id})
                            list_value = []
                            for bom_line in mrp_order.bom_id.bom_line_ids:
                                list_value.append((0, 0, {
                                    'raw_material_production_id': mrp_order.id,
                                    'name': mrp_order.name,
                                    'product_id': bom_line.product_id.id,
                                    'product_uom': bom_line.product_uom_id.id,
                                    'product_uom_qty': bom_line.product_qty * mrp_order.product_qty,
                                    'picking_type_id': mrp_order.picking_type_id.id,
                                    'location_id': mrp_order.location_src_id.id,
                                    'location_dest_id': bom_line.product_id.with_company(
                                        self.company_id.id).property_stock_production.id,
                                    'company_id': mrp_order.company_id.id,
                                }))
                            mrp_order.update({'move_raw_ids': list_value})
        return True
