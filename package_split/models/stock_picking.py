# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhsina V (<https://www.cybrosys.com>)
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
#############################################################################
from odoo import models
from odoo.tools import float_compare, float_is_zero, float_round
from odoo.addons.stock.models.stock_picking import Picking


class Picking(models.Model):
    """Inheriting the stock picking model to change the package creation method
    based on package category provided inside the product form."""
    _inherit = 'stock.picking'

    def _put_in_pack(self, move_line_ids, create_package_level=True):
        """For each product in the orderline with the same package category,
        it creates packages and adds the corresponding products into the
        package when validating the delivery"""
        packages = {}
        precision_digits = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        if float_is_zero(move_line_ids[0].qty_done,
                         precision_digits=precision_digits):
            for line in move_line_ids:
                line.qty_done = line.reserved_uom_qty
        for move_line in move_line_ids:
            if float_compare(move_line.qty_done, move_line.reserved_uom_qty,
                             precision_rounding=move_line.product_uom_id.rounding
                             ) >= 0:
                if not move_line.product_id.package_category_id:
                    package_category_value = 'Others'
                    category_name = ""
                else:
                    package_category_value = move_line.product_id.package_category_id.name
                    category_name = '-' + move_line.product_id.package_category_id.name
                if package_category_value not in packages:
                    packages[package_category_value] = self.env[
                        'stock.quant.package'].create({})
                    packages[
                        package_category_value].name += category_name
                move_line.write(
                    {'result_package_id': packages[package_category_value].id})
            else:
                quantity_left_todo = float_round(
                    move_line.reserved_uom_qty - move_line.qty_done,
                    precision_rounding=move_line.product_uom_id.rounding,
                    rounding_method='HALF-UP')
                done_to_keep = move_line.qty_done
                new_move_line = move_line.copy(
                    default={'reserved_uom_qty': 0,
                             'qty_done': move_line.qty_done})
                vals = {'reserved_uom_qty': quantity_left_todo, 'qty_done': 0.0
                        }
                if move_line.picking_id.picking_type_id.code == 'incoming':
                    if move_line.lot_id:
                        vals['lot_id'] = False
                    if move_line.lot_name:
                        vals['lot_name'] = False
                move_line.write(vals)
                new_move_line.write({'reserved_uom_qty': done_to_keep})
                if not move_line.product_id.package_category_id:
                    package_category_value = 'Others'
                    category_name = ""
                else:
                    package_category_value = move_line.product_id.package_category_id.name
                    category_name = '-' + move_line.product_id.package_category_id.name
                if package_category_value not in packages:
                    packages[package_category_value] = self.env[
                        'stock.quant.package'].create({})
                    packages[
                        package_category_value].name += category_name
                new_move_line.write(
                    {'result_package_id': packages[package_category_value].id})
        if create_package_level:
            for package_category_value, package in packages.items():
                grouped_move_lines = move_line_ids.filtered(
                    lambda l: l.product_id.package_category_id.name ==
                              package_category_value)
                if not grouped_move_lines:
                    continue
                self.env['stock.package_level'].create({
                    'package_id': package.id,
                    'picking_id': grouped_move_lines[
                        0].picking_id.id if grouped_move_lines else False,
                    'location_id': False,
                    'location_dest_id': grouped_move_lines.mapped(
                        'location_dest_id').id,
                    'move_line_ids': [(6, 0, grouped_move_lines.ids)],
                    'company_id': grouped_move_lines[0].company_id.id,
                })
        return list(packages.values())

    Picking._put_in_pack = _put_in_pack
