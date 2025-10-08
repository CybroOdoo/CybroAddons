"""This module handles the requests made by js files and returns the corresponding data."""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    """Class for handling the requests and responses"""

    @http.route('/3Dstock/warehouse', type='json', auth='public')
    def get_warehouse_data(self, company_id):
        """
        This method is used to handle the request for warehouse data.
        ------------------------------------------------
        @param self: object pointer.
        @param company_id: current company id.
        @return: a list of warehouses created under the active company.
        """
        warehouse = request.env['stock.warehouse'].sudo().search([])
        warehouse_list = []
        warehouse_list.clear()
        for rec in warehouse:
            if rec.company_id.id == company_id:
                warehouse_list.append((rec.id, rec.name))
        return warehouse_list

    @http.route('/3Dstock/data', type='json', auth='public')
    def get_stock_data(self, company_id, wh_id):
        """
        This method is used to handle the request for location data.
        ------------------------------------------------
        @param self: object pointer
        @param company_id: current company id.
        @param wh_id: the selected warehouse id.
        @return:a list of locations with their dimensions and positions of
                selected warehouse.
        """
        warehouse = request.env['stock.warehouse'].sudo().search(
            [('id', '=', int(wh_id)), ('company_id', '=', int(company_id))])
        locations = request.env['stock.location'].sudo().search(
            [('company_id', '=', int(company_id)),
             ('active', '=', 'true'),
             ('usage', '=', 'internal')])
        location_dict = {}
        for loc in locations:
            for wh in warehouse:
                if loc.warehouse_id.id == warehouse.id:
                    if loc.id not in (
                            wh.lot_stock_id.id, wh.wh_input_stock_loc_id.id,
                            wh.wh_qc_stock_loc_id.id,
                            wh.wh_pack_stock_loc_id.id, wh.wh_output_stock_loc_id.id):
                        length = int(loc.length * 3.779 * 2)
                        width = int(loc.width * 3.779 * 2)
                        height = int(loc.height * 3.779 * 2)
                        location_dict.update(
                            {loc.unique_code: [loc.pos_x, loc.pos_y, loc.pos_z,
                                               length, width, height]})

        return location_dict

    @http.route('/3Dstock/data/quantity', type='json', auth='public')
    def get_stock_count_data(self, loc_code):
        """
        This method is used to handle the request for location's current stock
        quantity.
        ------------------------------------------------
        @param self: object pointer.
        @param loc_code: the selected location code.
        @return: current quantity of selected location.
        """
        quantity = request.env['stock.quant'].sudo().search(
            [('location_id.unique_code', '=', loc_code)]).mapped(
            'quantity')
        capacity = request.env['stock.location'].sudo().search(
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

    @http.route('/3Dstock/data/product', type='json', auth='public')
    def get_stock_product_data(self, loc_code):
        """
        This method is used to handle the request for data of products of
        selected location.
        ------------------------------------------------
        @param self: object pointer.
        @param loc_code: the selected location code.
        @return: a dictionary including total capacity, current capacity and
        products stored in selected location.
        """
        products = request.env['stock.quant'].sudo().search(
            [('location_id.unique_code', '=', loc_code)])
        quantity_obj = request.env['stock.quant'].sudo().search(
            [('location_id.unique_code', '=', loc_code)]).mapped(
            'quantity')
        capacity = request.env['stock.location'].sudo().search(
            [('unique_code', '=', loc_code)]).max_capacity
        product_list = []
        product_list.clear()
        if products:
            for rec in products:
                product_list.append((rec.product_id.display_name, rec.quantity))
        load = math.fsum(quantity_obj)
        if capacity > 0:
            space = capacity - load
        else:
            space = 0
        data = {
            'capacity': capacity,
            'space': space,
            'product_list': product_list
        }
        return data

    @http.route('/3Dstock/data/standalone', type='json', auth='public')
    def get_standalone_stock_data(self, company_id, loc_id):
        """
        This method is used to handle the request for individual location data.
        ------------------------------------------------
        @param self: object pointer.
        @param company_id: the current company id.
        @param loc_id: the selected location code.
        @return: a dictionary including of selected location's dimensions and
        positions.
        """
        warehouse = request.env['stock.location'].sudo().search(
            [('company_id.id', '=', int(company_id)),
             ('id', '=', int(loc_id))]).mapped('warehouse_id')
        locations = request.env['stock.location'].sudo().search(
            [('company_id.id', '=', int(company_id)),
             ('active', '=', 'true'),
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
