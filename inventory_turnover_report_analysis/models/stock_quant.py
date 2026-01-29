# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class StockQuant(models.Model):
    """Inherit StockQuant to add new fields"""
    _inherit = "stock.quant"

    last_count_date = fields.Date(compute='_compute_last_count_date',
                                  help='Last time the Quantity was Updated')

    def _compute_last_count_date(self):
        """ Compute the last count date by examining the stock move lines associated with each quant.
        """
        self.last_count_date = False
        groups = self.env['stock.move.line'].read_group(
            [
                ('state', '=', 'done'),
                ('is_inventory', '=', True),
                ('product_id', 'in', self.product_id.ids),
                '|',
                ('lot_id', 'in', self.lot_id.ids),
                ('lot_id', '=', False),
                '|',
                ('owner_id', 'in', self.owner_id.ids),
                ('owner_id', '=', False),
                '|',
                ('location_id', 'in', self.location_id.ids),
                ('location_dest_id', 'in', self.location_id.ids),
                '|',
                ('package_id', '=', False),
                '|',
                ('package_id', 'in', self.package_id.ids),
                ('result_package_id', 'in', self.package_id.ids),
            ],
            ['date:max', 'product_id', 'lot_id', 'package_id', 'owner_id',
             'result_package_id', 'location_id', 'location_dest_id'],
            ['product_id', 'lot_id', 'package_id', 'owner_id',
             'result_package_id', 'location_id', 'location_dest_id'],
            lazy=False)

        def _update_dict(date_by_quant, key, value):
            current_date = date_by_quant.get(key)
            if not current_date or value > current_date:
                date_by_quant[key] = value

        date_by_quant = {}
        for group in groups:
            move_line_date = group['date']
            location_id = group['location_id'][0]
            location_dest_id = group['location_dest_id'][0]
            package_id = group['package_id'] and group['package_id'][0]
            result_package_id = group['result_package_id'] and \
                                group['result_package_id'][0]
            lot_id = group['lot_id'] and group['lot_id'][0]
            owner_id = group['owner_id'] and group['owner_id'][0]
            product_id = group['product_id'][0]
            _update_dict(date_by_quant, (
            location_id, package_id, product_id, lot_id, owner_id),
                         move_line_date)
            _update_dict(date_by_quant, (
            location_dest_id, package_id, product_id, lot_id, owner_id),
                         move_line_date)
            _update_dict(date_by_quant, (
            location_id, result_package_id, product_id, lot_id, owner_id),
                         move_line_date)
            _update_dict(date_by_quant, (
            location_dest_id, result_package_id, product_id, lot_id, owner_id),
                         move_line_date)
        for quant in self:
            quant.last_count_date = date_by_quant.get((quant.location_id.id,
                                                       quant.package_id.id,
                                                       quant.product_id.id,
                                                       quant.lot_id.id,
                                                       quant.owner_id.id))
