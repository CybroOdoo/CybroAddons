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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models

from .dashboard_utils import check_dashboard_access

ACTIVE_STATES = ('assigned', 'waiting', 'confirmed')


class StockPicking(models.Model):
    """ Extends 'stock.picking' for retrieving stock picking data for
    dashboard."""
    _inherit = "stock.picking"

    @api.model
    def get_operation_types(self):
        """ Method for retrieving operation type tiles, operation type graph and
        returns operation type details.
        no_transfer - count of transfers for each operation type,
        late - count of late transfers for each operation type,
        waiting - count of waiting transfers for each operation type,
        operation_type_name - name of each operation type,
        backorder - count of backorders for each operation type.
        """
        check_dashboard_access(self.env)
        picking_types = self.env['stock.picking.type'].search(
            [('company_id', 'in', self.env.companies.ids)])
        now = fields.Datetime.now()
        # The same conditions are used by the "Late" link of the tiles.
        late_domain = [
            ('state', 'in', ACTIVE_STATES),
            '|', '|',
            ('has_deadline_issue', '=', True),
            ('date_deadline', '<=', now),
            ('scheduled_date', '<=', now),
        ]
        total_count = self._count_by_picking_type([])
        late_count = self._count_by_picking_type(late_domain)
        waiting_count = self._count_by_picking_type(
            [('state', '=', 'confirmed')])
        backorder_count = self._count_by_picking_type(
            [('backorder_id', '!=', False)])
        no_transfer = {}
        late = {}
        waiting = {}
        backorder = {}
        operation_type_name = {}
        for picking_type in picking_types:
            type_id = picking_type.id
            no_transfer[type_id] = total_count.get(type_id, 0)
            operation_type_name[type_id] = picking_type.display_name
            if late_count.get(type_id):
                late[type_id] = late_count[type_id]
            if waiting_count.get(type_id):
                waiting[type_id] = waiting_count[type_id]
            if backorder_count.get(type_id):
                backorder[type_id] = backorder_count[type_id]
        return no_transfer, late, waiting, operation_type_name, backorder

    @api.model
    def _count_by_picking_type(self, domain):
        """ Returns the number of transfers of each operation type.

        :param list domain: domain of the counted transfers.
        :return: dict of operation type id and transfer count.
        """
        return {
            picking_type.id: count
            for picking_type, count in self._read_group(
                domain, ['picking_type_id'], ['__count'])
        }

    @api.model
    def get_product_category(self):
        """ Returns the product categories and their on-hand quantity."""
        check_dashboard_access(self.env)
        quants = self.env['stock.quant']._read_group(
            [('location_id.usage', '=', 'internal')],
            ['product_id'], ['quantity:sum'])
        products = self.env['product.product'].browse(
            [product.id for product, _quantity in quants])
        category_by_product = {
            product.id: product.categ_id for product in products}
        category_quantity = {}
        for product, quantity in quants:
            category = category_by_product[product.id]
            category_quantity[category] = (
                category_quantity.get(category, 0.0) + quantity)
        category_name = []
        quantity_list = []
        for category, quantity in sorted(
                category_quantity.items(), key=lambda item: -item[1]):
            if quantity > 0:
                category_name.append(category.display_name)
                quantity_list.append(quantity)
        return {'name': category_name, 'count': quantity_list}

    @api.model
    def get_locations(self):
        """ Returns the internal locations and their on-hand quantity."""
        check_dashboard_access(self.env)
        value = {}
        for location, quantity in self.env['stock.quant']._read_group(
                [('location_id.usage', '=', 'internal')],
                ['location_id'], ['quantity:sum']):
            value[location.complete_name] = quantity
        return value
