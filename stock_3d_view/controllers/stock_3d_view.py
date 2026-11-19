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
#############################################################################
import math
from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request


class Stock3DView(http.Controller):
    """Class for handling the requests and responses"""

    def _check_access(self):
        """Verify the user is authenticated and belongs to stock.group_stock_user."""
        if not request.env.user.has_group('stock.group_stock_user'):
            raise AccessError("Access Denied: You must have Inventory User permissions to access 3D stock data.")

    @http.route('/3Dstock/warehouse', type='jsonrpc', auth='user')
    def get_warehouse_data(self, company_id):
        """
        This method is used to handle the request for warehouse data.
        ------------------------------------------------
        @param self: object pointer.
        @param company_id: current company id.
        @return: a list of warehouses created under the active company.
        """
        self._check_access()
        company_id = int(company_id) if company_id else request.env.company.id
        warehouses = request.env['stock.warehouse'].search([('company_id', '=', company_id)])
        return [(rec.id, rec.name) for rec in warehouses]

    @http.route('/3Dstock/data', type='jsonrpc', auth='user')
    def get_stock_data(self, company_id, wh_id):
        """
        This method is used to handle the request for location data.
        ------------------------------------------------
        @param self: object pointer
        @param company_id: current company id.
        @param wh_id: the selected warehouse id.
        @return: a list of locations with their dimensions and positions of
                selected warehouse.
        """
        self._check_access()
        warehouse = request.env['stock.warehouse'].search(
            [('id', '=', int(wh_id)), ('company_id', '=', int(company_id))], limit=1)
        if not warehouse:
            return {}
        locations = request.env['stock.location'].search(
            [('company_id', '=', int(company_id)),
             ('usage', '=', 'internal')])
        location_dict = {}
        excluded_ids = {
            warehouse.lot_stock_id.id,
            warehouse.wh_input_stock_loc_id.id,
            warehouse.wh_qc_stock_loc_id.id,
            warehouse.wh_pack_stock_loc_id.id,
            warehouse.wh_output_stock_loc_id.id,
        }
        for loc in locations:
            if loc.warehouse_id.id == warehouse.id and loc.id not in excluded_ids:
                length = int(loc.length * 3.779 * 2)
                width = int(loc.width * 3.779 * 2)
                height = int(loc.height * 3.779 * 2)
                code = loc.unique_code or loc.name or str(loc.id)
                location_dict[code] = [
                    loc.pos_x, loc.pos_y, loc.pos_z,
                    length, width, height, loc.id
                ]
        return location_dict

    @http.route('/3Dstock/data/quantity', type='jsonrpc', auth='user')
    def get_stock_count_data(self, loc_code=None, loc_id=None, **kw):
        """
        This method is used to handle the request for location's current stock
        quantity.
        ------------------------------------------------
        @param self: object pointer.
        @param loc_code: the selected location code.
        @param loc_id: the selected location id.
        @return: current quantity of selected location.
        """
        self._check_access()
        if loc_id:
            location = request.env['stock.location'].search([('id', '=', int(loc_id))], limit=1)
            quants = request.env['stock.quant'].search(
                [('location_id', 'child_of', location.id)]) if location else request.env['stock.quant']
        else:
            location = request.env['stock.location'].search(
                ['|', '|', ('unique_code', '=', loc_code), ('name', '=', loc_code),
                 ('complete_name', 'ilike', loc_code)], limit=1)
            if location:
                quants = request.env['stock.quant'].search([('location_id', 'child_of', location.id)])
            else:
                quants = request.env['stock.quant'].search(
                    ['|', '|', ('location_id.unique_code', '=', loc_code),
                     ('location_id.name', '=', loc_code),
                     ('location_id.complete_name', 'ilike', loc_code)])

        quantity = quants.mapped('quantity')
        capacity = location.max_capacity if location and location.exists() else 0
        count = math.fsum(quantity)
        quant_data = (0, 0)
        if capacity and capacity > 0:
            load = int((count * 100) / capacity)
            quant_data = (capacity, load)
        elif count > 0:
            quant_data = (0, -1)
        return quant_data

    @http.route('/3Dstock/data/product', type='jsonrpc', auth='user')
    def get_stock_product_data(self, loc_code=None, loc_id=None, **kw):
        """
        This method is used to handle the request for data of products of
        selected location.
        ------------------------------------------------
        @param self: object pointer.
        @param loc_code: the selected location code.
        @param loc_id: the selected location id.
        @return: a dictionary including total capacity, current capacity and
        products stored in selected location.
        """
        self._check_access()
        if loc_id:
            location = request.env['stock.location'].search([('id', '=', int(loc_id))], limit=1)
            products = request.env['stock.quant'].search(
                [('location_id', 'child_of', location.id), ('quantity', '!=', 0)]) if location else request.env['stock.quant']
        else:
            location = request.env['stock.location'].search(
                ['|', '|', ('unique_code', '=', loc_code), ('name', '=', loc_code),
                 ('complete_name', 'ilike', loc_code)], limit=1)
            if location:
                products = request.env['stock.quant'].search(
                    [('location_id', 'child_of', location.id), ('quantity', '!=', 0)])
            else:
                products = request.env['stock.quant'].search(
                    ['|', '|', ('location_id.unique_code', '=', loc_code),
                     ('location_id.name', '=', loc_code),
                     ('location_id.complete_name', 'ilike', loc_code),
                     ('quantity', '!=', 0)])

        quantity_obj = products.mapped('quantity')
        capacity = location.max_capacity if location and location.exists() else 0
        product_list = []
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

    @http.route('/3Dstock/data/standalone', type='jsonrpc', auth='user')
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
        self._check_access()
        location = request.env['stock.location'].search(
            [('company_id', '=', int(company_id)),
             ('id', '=', int(loc_id))], limit=1)
        if not location:
            return {}
        warehouse = location.warehouse_id
        if not warehouse:
            return {}
        locations = request.env['stock.location'].search(
            [('company_id', '=', int(company_id)),
             ('usage', '=', 'internal')])
        location_dict = {}
        for loc in locations:
            if loc.warehouse_id.id == warehouse.id:
                length = int(loc.length * 3.779 * 2)
                width = int(loc.width * 3.779 * 2)
                height = int(loc.height * 3.779 * 2)
                code = loc.unique_code or loc.name or str(loc.id)
                location_dict[code] = [
                    loc.pos_x, loc.pos_y, loc.pos_z,
                    length, width, height, loc.id
                ]
        return location_dict
