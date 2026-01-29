# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu P (odoo@cybrosys.com)
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
from collections import OrderedDict
from odoo import api, fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    location_warehouse_id = fields.Many2one('stock.warehouse',
                                            compute='_compute_location_warehouse_id',
                                            store=True)

    @api.depends('warehouse_view_ids')
    def _compute_location_warehouse_id(self):
        """Computes the warehouse location"""
        warehouses = self.env['stock.warehouse'].search(
            [('view_location_id', 'parent_of', self.ids)])
        view_by_wh = OrderedDict(
            (wh.view_location_id.id, wh.id) for wh in warehouses)
        self.warehouse_id = False
        for loc in self:
            path = set(
                int(loc_id) for loc_id in loc.parent_path.split('/')[:-1])
            for view_location_id in view_by_wh:
                if view_location_id in path:
                    loc.location_warehouse_id = view_by_wh[view_location_id]
                    break
