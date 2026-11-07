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
import json
from odoo import http, _
from odoo.exceptions import AccessError
from odoo.http.stream import content_disposition, request
from odoo.http.dispatcher import serialize_exception as _serialize_exception
from odoo.tools import html_escape

ALLOWED_XLSX_MODELS = {
    'dynamic.inventory.report',
    'wizard.stock.history',
}


class XLSXReportController(http.Controller):
    """Controller for handling XLSX report generation and dashboard data in Odoo."""

    def _check_inventory_access(self):
        """Ensure current user has inventory rights."""
        if not request.env.user.has_group('stock.group_stock_user'):
            raise AccessError(_("Access Denied: Inventory user rights required."))

    @http.route('/xlsx_reports', type='http', auth='user', methods=['POST'])
    def get_report_xlsx(self, model, options, output_format, report_name,
                        report_data=None):
        """Endpoint to generate and download an XLSX report."""
        self._check_inventory_access()
        if model not in ALLOWED_XLSX_MODELS:
            return request.not_found()
        uid = request.session.uid
        report_obj = request.env[model].with_user(uid)
        if not hasattr(report_obj, 'get_xlsx_report'):
            return request.not_found()
        token = 'dummy-because-api-expects-one'
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition',
                         content_disposition(report_name + '.xlsx'))
                    ]
                )
                options = json.loads(options) if isinstance(options, str) else options
                report_obj.get_xlsx_report(options, response, report_data)
                response.set_cookie('fileToken', token)
                return response
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))

    @http.route('/get_operation_types', auth='user', type='jsonrpc')
    def get_operation_types(self):
        """For operation type"""
        self._check_inventory_access()
        return request.env['stock.picking'].get_operation_types()

    @http.route('/get_the_top_products', auth='user', type='jsonrpc')
    def get_the_top_products(self):
        """To get top products"""
        self._check_inventory_access()
        return request.env['stock.move'].get_the_top_products()

    @http.route('/get_stock_moves', auth='user', type='jsonrpc')
    def get_stock_moves(self):
        """rpc method of stock moves graph"""
        self._check_inventory_access()
        return request.env['stock.move'].get_stock_moves()

    @http.route('/get_product_moves', auth='user', type='jsonrpc')
    def get_product_moves(self):
        """rpc method of product moves graph"""
        self._check_inventory_access()
        return request.env['stock.move.line'].get_product_moves()

    @http.route('/get_product_category', auth='user', type='jsonrpc')
    def get_product_category(self):
        """rpc method of product category graph"""
        self._check_inventory_access()
        return request.env['stock.picking'].get_product_category()

    @http.route('/get_locations', auth='user', type='jsonrpc')
    def get_locations(self):
        """Gets values of locations"""
        self._check_inventory_access()
        return request.env['stock.picking'].get_locations()

    @http.route('/get_the_top_products_today', auth='user', type='jsonrpc')
    def get_the_top_products_today(self, post=None):
        """rpc method to get top product today"""
        self._check_inventory_access()
        return request.env['stock.move'].get_the_top_products_today(post)

    @http.route('/get_the_top_products_thirty_days', auth='user', type='jsonrpc')
    def get_the_top_products_thirty_days(self, post=None):
        """rpc method to get top products thirty days"""
        self._check_inventory_access()
        return request.env['stock.move'].get_the_top_products_thirty_days(post)

    @http.route('/get_the_top_products_three_month', auth='user', type='jsonrpc')
    def get_the_top_products_three_month(self, post=None):
        """rpc method to get top products three months"""
        self._check_inventory_access()
        return request.env['stock.move'].get_the_top_products_three_month(post)

    @http.route('/get_the_top_products_last_year', auth='user', type='jsonrpc')
    def get_the_top_products_last_year(self, post=None):
        """rpc method to get top products last year"""
        self._check_inventory_access()
        return request.env['stock.move'].get_the_top_products_last_year(post)

    @http.route('/this_month', auth='user', type='jsonrpc')
    def this_month(self, post=None):
        """RPC method of stock moves graph select this month"""
        self._check_inventory_access()
        return request.env['stock.move'].this_month(post)

    @http.route('/last_three_month', auth='user', type='jsonrpc')
    def last_three_month(self, post=None):
        """rpc method of stock moves graph select 3 month"""
        self._check_inventory_access()
        return request.env['stock.move'].last_three_month(post)

    @http.route('/last_year', auth='user', type='jsonrpc')
    def last_year(self, post=None):
        """RPC method of stock moves graph select last year"""
        self._check_inventory_access()
        return request.env['stock.move'].last_year(post)
