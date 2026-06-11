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
import math
from odoo import http
from odoo.http import request


class Stock3DView(http.Controller):
    """
    Controller for handling 3D stock view data requests.
    Provides routes for fetching warehouse, location, and product data.
    """

    @http.route('/3Dstock/warehouse', type='json', auth='user')
    def get_warehouse_data(self, company_id):
        """
        Fetch all warehouses for a specific company.

        :param int company_id: The ID of the current company.
        :return: A list of tuples containing (warehouse_id, warehouse_name).
        :rtype: list[tuple(int, str)]
        """
        warehouse = request.env['stock.warehouse'].search([])
        warehouse_list = []
        for rec in warehouse:
            if rec.company_id.id == company_id:
                warehouse_list.append((rec.id, rec.name))
        return warehouse_list

    @http.route('/3Dstock/data', type='json', auth='user')
    def get_stock_data(self, company_id, wh_id):
        """
        Fetch 3D positional and dimension data for internal locations of a warehouse.

        :param int company_id: The ID of the current company.
        :param int wh_id: The ID of the selected warehouse.
        :return: A dictionary mapping location unique codes to their 3D coordinates and dimensions.
        :rtype: dict
        """
        warehouse = request.env['stock.warehouse'].search(
            [('id', '=', int(wh_id)), ('company_id', '=', int(company_id))])
        locations = request.env['stock.location'].search(
            [('company_id', '=', int(company_id)),
             ('active', '=', True),
             ('usage', '=', 'internal')])
        location_dict = {}
        for loc in locations:
            for wh in warehouse:
                if loc.warehouse_id.id == wh.id:
                    if loc.id not in (
                            wh.lot_stock_id.id, wh.wh_input_stock_loc_id.id,
                            wh.wh_qc_stock_loc_id.id,
                            wh.wh_pack_stock_loc_id.id, wh.wh_output_stock_loc_id.id):
                        # Convert dimensions (assume 1 unit = 3.779 pixels * 2 for scaling)
                        length = int(loc.length * 3.779 * 2)
                        width = int(loc.width * 3.779 * 2)
                        height = int(loc.height * 3.779 * 2)
                        location_dict.update(
                            {loc.unique_code: [loc.pos_x, loc.pos_y, loc.pos_z,
                                               length, width, height]})
        return location_dict

    @http.route('/3Dstock/data/quantity', type='json', auth='user')
    def get_stock_count_data(self, loc_code):
        """
        Fetch the current stock load percentage for a specific location.

        :param str loc_code: The unique code of the location.
        :return: Tuple containing (max_capacity, current_load_percentage).
        :rtype: tuple(int, int)
        """
        quantity = request.env['stock.quant'].search(
            [('location_id.unique_code', '=', loc_code)]).mapped('quantity')
        capacity = request.env['stock.location'].search(
            [('unique_code', '=', loc_code)]).max_capacity
        count = math.fsum(quantity)
        quant_data = (0, 0)
        if capacity:
            if capacity > 0:
                load = int((count * 100) / capacity)
                quant_data = (capacity, load)
            else:
                if count > 0:
                    quant_data = (0, -1)
        return quant_data

    @http.route('/3Dstock/data/product', type='json', auth='user')
    def get_stock_product_data(self, loc_code):
        """
        Fetch a list of products and available space for a specific location.

        :param str loc_code: The unique code of the location.
        :return: Dictionary with capacity, available space, and details of stored products.
        :rtype: dict
        """
        products = request.env['stock.quant'].search(
            [('location_id.unique_code', '=', loc_code)])
        quantity_obj = products.mapped('quantity')
        capacity = request.env['stock.location'].search(
            [('unique_code', '=', loc_code)]).max_capacity
        product_list = [(rec.product_id.display_name, rec.quantity) for rec in products]
        load = math.fsum(quantity_obj)
        space = capacity - load if capacity > 0 else 0
        return {
            'capacity': capacity,
            'space': space,
            'product_list': product_list
        }

    @http.route('/3Dstock/data/standalone', type='json', auth='user')
    def get_standalone_stock_data(self, company_id, loc_id):
        """
        Fetch individual location data for the 3D form view.

        :param int company_id: The ID of the current company.
        :param int loc_id: The ID of the specific location.
        :return: A dictionary mapping location unique codes to 3D properties and database ID.
        :rtype: dict
        """
        warehouse = request.env['stock.location'].search(
            [('company_id.id', '=', int(company_id)),
             ('id', '=', int(loc_id))]).mapped('warehouse_id')
        locations = request.env['stock.location'].search(
            [('company_id.id', '=', int(company_id)),
             ('active', '=', True),
             ('usage', '=', 'internal')])
        location_dict = {}
        for loc in locations:
            if loc.warehouse_id.id == warehouse.id:
                length = int(loc.length * 3.779 * 2)
                width = int(loc.width * 3.779 * 2)
                height = int(loc.height * 3.779 * 2)
                location_dict.update(
                    {loc.unique_code: [loc.pos_x, loc.pos_y, loc.pos_z,
                                       length, width, height, loc.id]})
        return location_dict
