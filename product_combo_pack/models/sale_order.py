# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Afras Habis (odoo@cybrosys.com)
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

from odoo import api, fields, models


class SalePack(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        super(SalePack, self).action_confirm()
        for line in self.order_line:
            if line.product_id.is_pack:
                for record in line.product_id.pack_products_ids:
                    dest_loc = self.env.ref('stock.stock_location_customers').id
                    self.env['stock.move'].create({
                        'name': record.product_id.name,
                        'product_id': record.product_id.id,
                        'product_uom_qty': record.quantity * line.product_uom_qty,
                        'product_uom': record.product_id.uom_id.id,
                        'picking_id': self.picking_ids[0].id,
                        'location_id': self.picking_ids.picking_type_id.default_location_src_id.id,
                        'location_dest_id': dest_loc,
                    })
