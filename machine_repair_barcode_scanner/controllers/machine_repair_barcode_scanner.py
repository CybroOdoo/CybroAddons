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


class BarcodeScanner(http.Controller):
    @http.route('/barcode_search/machine', auth='user', type='jsonrpc')
    def barcode_search(self, **kwargs):
        """Search for barcodes"""
        product = request.env['product.product'].search(
            [('barcode', '=', kwargs.get('last_code'))], limit=1)
        if not product:
            return False
        repair_order = request.env['machine.repair'].browse(kwargs.get('order_id'))
        if kwargs.get('product') == 'machine':
            if not product.is_machine:
                return 'not_machine'
            repair_order.write({
                'machine_id': product.id,
                'machine_categ_id': product.categ_id.id
            })
        else:
            if not product.is_machine_parts:
                return 'not_part'
            consume_part = repair_order.consume_part_ids.filtered(
                lambda rec: rec.machine_id.id == product.id)
            if consume_part:
                consume_part.write({'qty': consume_part.qty + 1})
            else:
                consume_part.create({
                    'machine_id': product.id,
                    'consume_id': repair_order.id,
                    'qty': 1})
        return True
