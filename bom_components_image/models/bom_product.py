# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Treesa Maria Jude(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api


class UsedInBom(models.Model):
    _inherit = 'product.template'

    used_bom_count = fields.Integer(compute='_bom_count', string='Count')

    def _bom_count(self):
        bom = self.env['mrp.bom'].search([])
        for i in bom:
            for j in i.bom_line_ids:
                if j.product_id.name == self.name:
                    self.used_bom_count = self.used_bom_count +1


class MoLineImage(models.Model):
    _inherit = 'stock.move'

    image = fields.Binary()


class BomLineImage(models.Model):
    _inherit = 'mrp.bom.line'

    image = fields.Binary(string="Image")

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        self.image = self.product_id.image_medium


class GetMoLineImage(models.Model):
    _inherit = 'mrp.production'

    def _generate_raw_move(self, bom_line, line_data):
        quantity = line_data['qty']
        alt_op = line_data['parent_line'] and line_data['parent_line'].operation_id.id or False
        if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom':
            return self.env['stock.move']
        if bom_line.product_id.type not in ['product', 'consu']:
            return self.env['stock.move']
        if self.bom_id.routing_id and self.bom_id.routing_id.location_id:
            source_location = self.bom_id.routing_id.location_id
        else:
            source_location = self.location_src_id
        original_quantity = self.product_qty - self.qty_produced
        data = {
            'name': self.name,
            'date': self.date_planned_start,
            'date_expected': self.date_planned_start,
            'bom_line_id': bom_line.id,
            'product_id': bom_line.product_id.id,
            'image': bom_line.image,
            'product_uom_qty': quantity,
            'product_uom': bom_line.product_uom_id.id,
            'location_id': source_location.id,
            'location_dest_id': self.product_id.property_stock_production.id,
            'raw_material_production_id': self.id,
            'company_id': self.company_id.id,
            'operation_id': bom_line.operation_id.id or alt_op,
            'price_unit': bom_line.product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': self.name,
            'warehouse_id': source_location.get_warehouse().id,
            'group_id': self.procurement_group_id.id,
            'propagate': self.propagate,
            'unit_factor': quantity / original_quantity,
        }
        return self.env['stock.move'].create(data)
