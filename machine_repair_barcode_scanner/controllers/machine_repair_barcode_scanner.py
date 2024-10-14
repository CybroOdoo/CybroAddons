# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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
from odoo import http
from odoo.http import request


class BarcodeScanner(http.Controller):
    @http.route('/barcode_search/machine', auth='user', type='json')
    def barcode_search(self, **kwargs):
        product = request.env['product.product'].search(
            [('barcode', '=', kwargs.get('last_code'))])
        if not product:
            return False
        else:
            repair_order = request.env['machine.repair'].browse(kwargs.get('order_id'))
            if kwargs.get('product') == 'machine':
                repair_order.write({'machine_id': product.id})
            else:
                consume_part = repair_order.consume_part_id.filtered(
                    lambda rec: rec.machine_id.id == product.id)
                if consume_part:
                    consume_part.write({'qty': consume_part.qty + 1})
                else:
                    consume_part.create({
                        'machine_id': product.id,
                        'consume_id': repair_order.id,
                        'qty': 1})
            return True
