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
from odoo import http
from odoo.http import request


class PosSalesPersonController(http.Controller):
    """Controller to fetch POS salesperson for a product."""

    @http.route('/get_pos_sales_person', type='jsonrpc', auth='user', methods=['POST'])
    def get_pos_sales_person(self, product_id, pos_order_line_id=None):
        """Return salesperson information for a product."""
        product = request.env['product.product'].browse(product_id).exists()
        return {
            'sales_person': product.pos_sales_person_id.name if product and product.pos_sales_person_id else ''
        }
